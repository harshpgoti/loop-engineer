#!/usr/bin/env python3
"""One-time migration: move an existing flat Loop Engineer layout into the new
app/data split (global) or the .loop-engineer/ nested folder (local product).

Old global layout:  ~/.loop-engineer/{memories,state.db,main_plan.md,...}
New global layout:  ~/.loop-engineer/data/{memories,state.db,main_plan.md,...}

Old local layout:   <product-folder>/{memories,state.db,main_plan.md,...}
New local layout:   <product-folder>/.loop-engineer/{memories,state.db,main_plan.md,...}

Safe by construction: only moves an explicit allowlist of Loop-Engineer-owned
paths. Dry-run by default - pass --apply to actually move files. Never
overwrites an existing target.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from loop_home import data_home, loop_home
from workspace_resolver import local_data_dir

# Safe to bulk-move: names exclusively used by Loop Engineer, vanishingly
# unlikely to collide with a real product's own files/folders.
SAFE_ENTRIES = (
    "memories",
    "state.db",
    "main_plan.md",
    "MEMORY.md",
    "USER.md",
    "SOUL.md",
    "CONTEXT.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "DECISIONS.md",
    "EVIDENCE_LOG.md",
    "HANDOFF.md",
    "CURRENT_STATE.md",
    "COMPACT.md",
    "STARTUP_MEMORY.md",
    "STATUS.md",
    "DOCTOR.md",
    "SYNC_REPORT.md",
    "RELEASE_CHECK.md",
    "DEPLOYMENT_PLAN.md",
    "plan",
    ".ai",
    ".loop",
    ".loop-workspace-version",
    "secrets.env",
    "registry",
)

# Common product-folder names too - only bulk-moved for the global home
# (which is exclusively Loop Engineer's own directory, nothing else lives
# there). For a local product folder, these are flagged instead of moved,
# since a real product very plausibly has its own docs/ or skills/.
GLOBAL_ONLY_ENTRIES = ("docs", "skills")

# Specific files inside docs/ and skills/ that ARE safe to move for a local
# product even though the parent folder itself is not bulk-moved there.
LOCAL_NESTED_SAFE_FILES = (
    "docs/ACCEPTANCE_CRITERIA.md",
    "docs/TEST_PLAN.md",
    "docs/interview_script.md",
)


def _move(src: Path, dest: Path, apply: bool) -> str:
    if dest.exists():
        return f"skipped (target exists): {src.name}"
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    return f"{'moved' if apply else 'would move'}: {src.name} -> {dest}"


def is_legacy_global(root: Path) -> bool:
    """True if ~/.loop-engineer/ has old-style flat data directly in it."""
    if not root.is_dir():
        return False
    if (root / "data").exists():
        return False  # already migrated
    return any((root / name).exists() for name in SAFE_ENTRIES)


def is_legacy_local(product_folder: Path) -> bool:
    """True if a product folder has old-style flat loop data directly in it."""
    if not product_folder.is_dir():
        return False
    if (product_folder / ".loop-engineer").exists():
        return False  # already migrated
    return (product_folder / "memories").is_dir() and (product_folder / "main_plan.md").exists()


def migrate_global(apply: bool = False) -> list[str]:
    root = loop_home()
    target = data_home()
    results: list[str] = []
    if not is_legacy_global(root):
        results.append(f"No legacy flat layout found at {root} - nothing to do.")
        return results
    for name in SAFE_ENTRIES + GLOBAL_ONLY_ENTRIES:
        src = root / name
        if not src.exists():
            continue
        results.append(_move(src, target / name, apply))
    return results


def migrate_local(product_folder: Path, apply: bool = False) -> list[str]:
    target = local_data_dir(product_folder)
    results: list[str] = []
    if not is_legacy_local(product_folder):
        results.append(f"No legacy flat layout found at {product_folder} - nothing to do.")
        return results
    for name in SAFE_ENTRIES:
        src = product_folder / name
        if not src.exists():
            continue
        results.append(_move(src, target / name, apply))
    for rel in LOCAL_NESTED_SAFE_FILES:
        src = product_folder / rel
        if not src.exists():
            continue
        results.append(_move(src, target / rel, apply))
    for name in GLOBAL_ONLY_ENTRIES:
        src = product_folder / name
        if src.exists():
            results.append(
                f"NOT auto-moved (may be your own product {name}/): review and move "
                f"remaining files under {src} into {target / name} manually if they are Loop Engineer's."
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a flat Loop Engineer layout to the new nested one.")
    parser.add_argument("--workspace", default=None, help="Product folder for local mode. Omit for global (~/.loop-engineer).")
    parser.add_argument("--apply", action="store_true", help="Actually move files. Default is dry-run.")
    args = parser.parse_args()

    if args.workspace:
        results = migrate_local(Path(args.workspace).expanduser().resolve(), apply=args.apply)
    else:
        results = migrate_global(apply=args.apply)

    for line in results:
        print(f"- {line}")
    if not args.apply:
        print("\nDry run only. Re-run with --apply to move files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
