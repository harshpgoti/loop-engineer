#!/usr/bin/env python3
"""Write plan/PARENT_CONTEXT.md inside a sub-product workspace.

The other half of the hierarchy link: a sub-product session starts already knowing
the constraints it inherits from the master plan, so it cannot silently re-decide
something the platform already settled.

Read-only against the parent workspace.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import hierarchy_drift as drift
from workspace_tree import product_folder, refresh
from workspace_utils import resolve_workspace


PARENT_CONTEXT_FILE = "plan/PARENT_CONTEXT.md"


def _row_for(parent_ws: Path, map_id: str | None, fallback_name: str) -> dict | None:
    from ultraplan_harness import parse_product_map
    from workspace_tree import map_id_for

    rows = parse_product_map(parent_ws)
    if not rows:
        return None
    wanted = map_id or map_id_for(parent_ws, fallback_name)
    for row in rows:
        if row.get("id") == wanted:
            return row
    return None


def _table(pairs: dict[str, tuple[str, str]], header: tuple[str, str]) -> str:
    """Render with the labels as the master plan wrote them, not the match keys."""
    if not pairs:
        return "_None recorded in the master plan._"
    lines = [f"| {header[0]} | {header[1]} |", "|---|---|"]
    for _key, (label, value) in sorted(pairs.items()):
        lines.append(f"| {label} | {value} |")
    return "\n".join(lines)


def _siblings(parent_ws: Path, row: dict | None) -> str:
    from ultraplan_harness import parse_product_map

    if not row:
        return "_No product map row bound to this sub-product._"
    rows = parse_product_map(parent_ws)
    by_id = {r.get("id"): r for r in rows}

    depends = [d.strip() for d in row.get("depends", "").replace(";", ",").split(",") if d.strip()]
    dependents = [
        r for r in rows if r.get("id") != row.get("id") and row.get("id", "") in str(r.get("depends", ""))
    ]

    lines: list[str] = []
    if depends:
        for dep in depends:
            key = dep.zfill(2) if dep.isdigit() else dep
            title = by_id.get(key, {}).get("title", dep)
            lines.append(f"- **Depends on** {key} - {title}")
    if dependents:
        for dep in dependents:
            lines.append(f"- **Depended on by** {dep.get('id')} - {dep.get('title')}")
    return "\n".join(lines) if lines else "_No dependencies recorded in the product map._"


def _integrations(parent_ws: Path, row: dict | None) -> str:
    from plan_paths import find_step_folder

    if not row:
        return "_No integration spec bound to this sub-product._"
    folder = find_step_folder(parent_ws, str(row.get("id")))
    if folder is None:
        return "_The master plan has no ultraplan folder for this step yet._"
    spec = drift.read_text(folder / "integrations.md", 4000).strip()
    if not spec:
        return f"_`plan/steps/{folder.name}/integrations.md` is empty in the master plan._"
    body = "\n".join(f"> {line}" for line in spec.splitlines()[:40])
    return (
        f"**This section is an obligation, not evidence.** Quoting it here does not mean this\n"
        f"sub-product has accounted for anything - record the response in `plan/INTEGRATIONS.yml`\n"
        f"or under `## Internal platform APIs` in this workspace's own step pack.\n\n"
        f"From main `plan/steps/{folder.name}/integrations.md`:\n\n{body}"
    )


def build_context(workspace: Path, tree: dict | None = None) -> str | None:
    tree = tree or refresh(workspace)
    parent = tree.get("parent")
    if not parent:
        return None

    parent_ws = parent["data_dir"]
    folder = product_folder(workspace)
    name = tree.get("name") or (folder.name if folder else workspace.name)
    from workspace_tree import read_meta

    row = _row_for(parent_ws, read_meta(workspace).get("map_id"), name)

    row_block = (
        f"| {row.get('id')} | {row.get('type')} | {row.get('title')} | {row.get('depends') or '-'} | "
        f"{row.get('status') or '-'} |"
        if row
        else None
    )

    lines = [
        f"# Parent Context - {name}",
        "",
        f"**Updated:** {date.today().isoformat()}",
        f"**Parent product:** `{parent['name']}` (`{parent['path']}`)",
        f"**Parent workspace:** `{parent_ws}`",
        "",
        "This sub-product belongs to a larger product. Everything below is **inherited "
        "constraint**, read from the master plan - it is not restated here to be re-decided.",
        "",
        "## Product map row",
        "",
    ]
    if row_block:
        lines.extend(
            [
                "| ID | Type | Title | Depends on | Ultraplan |",
                "|----|------|-------|------------|-----------|",
                row_block,
            ]
        )
    else:
        lines.append(
            "_This sub-product has no row in the parent's `plan/PRODUCT_MAP.md`. "
            "The master plan does not yet account for it - raise this before building._"
        )

    lines.extend(
        [
            "",
            "## Dependencies across the platform",
            "",
            _siblings(parent_ws, row),
            "",
            "## Inherited deployment & infrastructure",
            "",
            _table(drift.deployment_labels(parent_ws), ("Item", "Platform choice")),
            "",
            "## Inherited decisions",
            "",
            _table(drift.decisions_labels(parent_ws), ("Topic", "Platform decision")),
            "",
            "## Integration contracts owed",
            "",
            _integrations(parent_ws, row),
            "",
            "## Rules",
            "",
            "- Parent decisions are **constraints**. Do not silently re-decide them here.",
            "- A genuine conflict goes to this workspace's `DOUBTS.md` and to the parent's "
            "`plan/SUBPRODUCTS.md` - the parent's next `/plan-loop` reconciles it.",
            "- Staged notes from the parent arrive in `.loop/pending/`; review with "
            "`loop pending list` and apply with `loop pending approve --all`.",
            "- Anything not listed above is this sub-product's own call.",
            "",
        ]
    )
    return "\n".join(lines)


def write_context(workspace: Path, tree: dict | None = None) -> Path | None:
    content = build_context(workspace, tree)
    if content is None:
        return None
    path = workspace / PARENT_CONTEXT_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    # Sources live in the *parent* workspace, so this view goes stale when the master
    # plan moves - which is exactly the case a sub-product needs to notice.
    try:
        import freshness

        parent_ws = (tree or {}).get("parent", {}).get("data_dir")
        if parent_ws:
            parent_ws = Path(parent_ws)
            freshness.stamp(
                path,
                [parent_ws / "DECISIONS.md", parent_ws / "plan" / "main_plan.md", parent_ws / "plan" / "PRODUCT_MAP.md"],
                generator="parent-context",
                version=1,
                workspace=workspace,
                command="loop session-start",
            )
    except Exception:
        pass
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write plan/PARENT_CONTEXT.md for a sub-product workspace.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    tree = refresh(workspace)
    content = build_context(workspace, tree)
    if content is None:
        print("No parent product workspace resolved - nothing to write.")
        return 0
    if args.print:
        print(content)
        return 0
    path = write_context(workspace, tree)
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
