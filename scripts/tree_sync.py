#!/usr/bin/env python3
"""One command that makes main product and sub-product agree, run from either end.

`loop workspace refresh` only ever refreshed the workspace it was run in. From a
sub-product that left the parent's roll-up stale until the parent happened to have
a session, so keeping a tree current meant remembering which command to run in
which folder. This runs the sync from wherever the user is standing.

Write policy is unchanged where it matters:

- **Derived reports** (`plan/SUBPRODUCTS.md`, `plan/PARENT_CONTEXT.md`) are regenerated
  from either end. They are generated views with no authored content to lose.
- **Authored state** (`DOUBTS.md`, `HANDOFF.md`, the rest of `plan/`) still never
  crosses a workspace boundary.
- **Drift staging** still only originates from the main product. Syncing from a
  sub-product refreshes reports but stages nothing, so a sub-product can never queue
  work into its siblings.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import hierarchy_sync
from workspace_tree import ROLE_MAIN, read_meta, refresh
from workspace_utils import resolve_workspace
from workspace_utils import console_utf8


def _ultraplan_status(workspace: Path) -> str | None:
    """Regenerate `plan/ULTRAPLAN_STATUS.md`. Read-only over the plan - creates no packs."""
    try:
        from plan_paths import product_map_file
        from ultraplan_harness import update_ultraplan_status

        if not product_map_file(workspace).exists():
            return None
        return str(update_ultraplan_status(workspace))
    except Exception:
        return None


def _dedupe(workspace: Path) -> int:
    try:
        from pending_writes import dedupe_pending

        return len(dedupe_pending(workspace))
    except Exception:
        return 0


def sync(workspace: Path, *, stage: bool = True) -> dict:
    """Sync this workspace and the other end of its link. Idempotent."""
    result: dict = {
        "workspace": str(workspace),
        "self": hierarchy_sync.run(workspace, stage=stage),
        "parent_refreshed": None,
        "ultraplan_status": _ultraplan_status(workspace),
        "deduped": _dedupe(workspace),
    }

    # Standing in a sub-product, refresh the parent's roll-up too - otherwise it keeps
    # reporting this sub-product as it was at the parent's last session. Never stage
    # from here: notes into sub-products are the main product's to propose.
    parent = (result["self"] or {}).get("parent")
    if parent and result["self"].get("role") != ROLE_MAIN:
        parent_ws = _parent_workspace(workspace)
        if parent_ws is not None:
            try:
                hierarchy_sync.run(parent_ws, stage=False)
                result["parent_refreshed"] = str(parent_ws)
            except Exception as exc:  # noqa: BLE001 - a stale roll-up must not fail the sync
                result["parent_error"] = f"{exc.__class__.__name__}: {exc}"

    return result


def _parent_workspace(workspace: Path) -> Path | None:
    from workspace_tree import data_dir_for, product_folder

    folder = product_folder(workspace)
    stored = read_meta(workspace).get("parent")
    if folder is None or not stored:
        return None
    parent_folder = (folder / str(stored)).resolve()
    return data_dir_for(parent_folder) if parent_folder.is_dir() else None


def describe(result: dict) -> str:
    self_result = result.get("self") or {}
    if not self_result.get("enabled"):
        return f"Nothing to sync - {self_result.get('reason', 'not a local product workspace')}."
    if not self_result.get("children") and not self_result.get("parent"):
        return (
            "Nothing to sync - this is a standalone workspace: no parent and no sub-products.\n"
            "  Sub-products are folders under this one with their own `.loop-engineer/`.\n"
            "  For one elsewhere on disk: `loop workspace link <path> --map-id NN`."
        )

    lines = [f"Synced `{result['workspace']}` [{self_result.get('role')}]"]
    if self_result.get("subproducts_file"):
        lines.append(f"  roll-up:        {self_result['subproducts_file']}")
    if self_result.get("parent_context_file"):
        lines.append(f"  parent context: {self_result['parent_context_file']}")
    if result.get("parent_refreshed"):
        lines.append(f"  parent roll-up: {result['parent_refreshed']} (refreshed)")
    if result.get("ultraplan_status"):
        lines.append(f"  ultraplan:      {result['ultraplan_status']}")
    if result.get("deduped"):
        lines.append(f"  pending:        dropped {result['deduped']} duplicate write(s)")

    counts = self_result.get("counts") or {}
    if counts.get("total"):
        lines.append(
            f"  drift:          {counts.get('error', 0)} error, "
            f"{counts.get('warn', 0)} warning, {counts.get('info', 0)} info"
        )
        for item in self_result.get("findings", []):
            lines.append(f"    [{item['level']}] {item['sub']} {item['kind']}: {item['detail']}")
    else:
        lines.append("  drift:          none")

    staged = self_result.get("staged") or {}
    if staged:
        lines.append(
            f"  staged:         {len(staged)} note(s) into sub-products - "
            "approve them there with `loop pending approve --all`"
        )
    return "\n".join(lines)


def main() -> int:
    console_utf8()
    parser = argparse.ArgumentParser(description="Sync main product and sub-products from either end.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument(
        "--no-stage", action="store_true", help="Report drift without staging notes into sub-products."
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    refresh(workspace)
    print(describe(sync(workspace, stage=not args.no_stage)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
