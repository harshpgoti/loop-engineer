#!/usr/bin/env python3
"""One entry point for hierarchy awareness: refresh links, write reports, stage notes.

Called once per session by `loop session-start` / `session-end`, and directly by
`loop workspace refresh` and `/product-tree`.

Write policy, enforced here:

- **Metadata** (`.loop/workspace.json`) may be stamped into a sub-product directly.
- **Product state** (`DOUBTS.md`, `HANDOFF.md`, `plan/*`) is never written across a
  workspace boundary at all.

Findings are no longer copied into the sub-product either. They are derived, so the
sub-product recomputes its own from its side (`parent_inbox`) and its commands ask
the user about them in the session. Staging them made a frozen copy of derived state
that could not self-heal, in a queue nobody remembered to drain.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import hierarchy_drift as drift
from parent_context import PARENT_CONTEXT_FILE, write_context
from subproducts_report import SUBPRODUCTS_FILE, write_report
from workspace_tree import ROLE_MAIN, describe_tree, refresh
from workspace_utils import resolve_workspace


def _drop_stale(path: Path, result: dict) -> None:
    """Remove a hierarchy report that no longer describes this workspace."""
    if not path.exists():
        return
    try:
        path.unlink()
        result.setdefault("removed", []).append(path.name)
    except OSError:
        pass


def _advance_watermark(workspace: Path, tree: dict) -> str | None:
    """Record that this sub-product has seen the parent's current state.

    Held back while the sub-product still has open findings. The watermark is what
    makes an upstream change stop being news, so advancing it before the user has
    answered would silence a question that was never asked. Once the inbox is
    empty - every finding accepted, declined or deferred - the parent's current
    state genuinely has been seen.
    """
    from workspace_tree import read_meta

    parent_ws = (tree.get("parent") or {}).get("data_dir")
    if not parent_ws:
        return None

    import parent_inbox
    import parent_watermark as wm

    if parent_inbox.inbox(workspace)["total"]:
        return None
    map_id = tree.get("map_id") or read_meta(workspace).get("map_id")
    return str(wm.sync(workspace, Path(parent_ws), map_id=map_id))


def run(workspace: Path, *, stage: bool = True) -> dict:
    """Refresh the hierarchy and regenerate whichever report this workspace needs."""
    tree = refresh(workspace)
    result: dict = {
        "enabled": bool(tree.get("enabled")),
        "role": tree.get("role"),
        "children": len(tree.get("children") or []),
        "parent": (tree.get("parent") or {}).get("name"),
        "findings": [],
        "counts": {"error": 0, "warn": 0, "info": 0, "total": 0},
        "subproducts_file": None,
        "parent_context_file": None,
    }
    if not tree.get("enabled"):
        result["reason"] = tree.get("reason")
        return result

    if tree.get("parent"):
        path = write_context(workspace, tree)
        if path is not None:
            result["parent_context_file"] = str(path)
        if stage:
            try:
                result["parent_watermark"] = _advance_watermark(workspace, tree)
            except Exception as exc:  # noqa: BLE001 - never block a session on this
                result["parent_watermark_error"] = f"{exc.__class__.__name__}: {exc}"
    else:
        # No parent any more (unlinked, moved, or pinned standalone). A stale report
        # would keep feeding a session inherited constraints that no longer apply -
        # every command reads it from the manifest.
        _drop_stale(workspace / PARENT_CONTEXT_FILE, result)

    if not tree.get("children"):
        _drop_stale(workspace / SUBPRODUCTS_FILE, result)

    if tree.get("role") == ROLE_MAIN and tree.get("children"):
        findings = drift.check_children(workspace, tree["children"])
        # Reported here, answered there: each sub-product recomputes its own share
        # of these and raises them with the user during its next command.
        path, _ = write_report(workspace, tree, {}, findings)
        result["findings"] = findings
        result["counts"] = drift.summarize(findings)
        result["subproducts_file"] = str(path) if path else None

    return result


def readiness(workspace: Path) -> dict:
    """Hierarchy view for /status, /prod-gap, and /release-check. Writes nothing.

    A main product is only as ready as its sub-products: an uninitialized or
    conflicting sub-product is a launch blocker for the platform, not a detail
    hidden inside another folder.
    """
    empty = {"role": None, "children": 0, "parent": None, "lines": [], "blockers": []}
    try:
        tree = refresh(workspace)
    except Exception:
        return empty
    if not tree.get("enabled") or tree.get("role") == "standalone":
        return empty

    lines: list[str] = [f"- **Role:** `{tree['role']}`"]
    blockers: list[str] = []

    parent = tree.get("parent")
    if parent:
        lines.append(f"- **Parent product:** `{parent['name']}` (`{parent['path']}`) - see `plan/PARENT_CONTEXT.md`")

    children = tree.get("children") or []
    if children:
        from subproducts_report import collect_child

        findings = drift.check_children(workspace, children)
        counts = drift.summarize(findings)
        lines.append(
            f"- **Sub-products:** {len(children)} - see `plan/SUBPRODUCTS.md` "
            f"({counts['error']} error, {counts['warn']} warning finding(s))"
        )
        for child in children:
            row = collect_child(child)
            state = "missing" if child.get("missing") else ("planned" if row["initialized"] else "uninitialized")
            lines.append(f"  - `{row['name']}` (map {row['map_id'] or '-'}): {state}, {row['tasks']}, gate {row['gate']}")
            if child.get("missing"):
                blockers.append(f"Sub-product `{row['name']}` folder is missing - the link is broken.")
            elif not row["initialized"]:
                blockers.append(f"Sub-product `{row['name']}` has no initialized plan - run `/plan-loop` there.")
        for item in findings:
            if item["level"] == drift.LEVEL_ERROR:
                blockers.append(f"Sub-product `{item['sub']}` - {item['kind']}: {item['detail']}")

    return {
        "role": tree.get("role"),
        "children": len(children),
        "parent": (parent or {}).get("name"),
        "lines": lines,
        "blockers": blockers,
    }


def manifest_block(workspace: Path, result: dict) -> list[str]:
    """Lines appended to plan/SESSION_MANIFEST.md so every agent sees the hierarchy."""
    if not result.get("enabled") or result.get("role") == "standalone":
        return []

    lines = ["", "## Hierarchy", "", f"- **Role:** `{result['role']}`"]
    if result.get("parent"):
        lines.append(
            f"- **Parent product:** `{result['parent']}` - read `plan/PARENT_CONTEXT.md` for "
            "inherited decisions and contracts. Parent decisions are constraints."
        )
    if result.get("children"):
        counts = result["counts"]
        lines.append(
            f"- **Sub-products:** {result['children']} - read `plan/SUBPRODUCTS.md` "
            f"(drift: {counts['error']} error, {counts['warn']} warning)."
        )
        if counts["error"]:
            lines.append(
                "- **Action:** resolve the `error` findings before build. Each sub-product raises "
                "its own share with the user during its next command - fix the master plan here "
                "when this side is the one that is wrong."
            )
        lines.append("- Sub-product state is read-only from here - never edit a sub-product's files directly.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh product hierarchy links and reports.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument(
        "--no-stage",
        action="store_true",
        help="Report only: do not advance this sub-product's parent watermark.",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    result = run(workspace, stage=not args.no_stage)
    print(describe_tree(workspace))
    if not result["enabled"]:
        return 0
    if result["subproducts_file"]:
        print(f"\nWrote {result['subproducts_file']}")
    if result["parent_context_file"]:
        print(f"Wrote {result['parent_context_file']}")
    counts = result["counts"]
    if counts["total"]:
        print(f"\nDrift: {counts['error']} error, {counts['warn']} warning, {counts['info']} info")
        for item in result["findings"]:
            print(f"  [{item['level']}] {item['sub']} {item['kind']}: {item['detail']}")
    if result.get("parent") and result.get("parent_watermark") is None:
        print("\nParent watermark held - open findings remain here. Run `loop findings ask`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
