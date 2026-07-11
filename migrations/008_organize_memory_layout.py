"""Migration 008: relocate memory/plan-loop files to their canonical homes.

- main_plan.md          -> plan/main_plan.md
- root MEMORY.md        -> memories/MEMORY.md (or removed if an exact duplicate)
- STARTUP_MEMORY.md     -> memories/STARTUP_MEMORY.md (legacy, preserved not deleted)
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 8
NAME = "organize_memory_layout"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    results: list[str] = []

    main_src = workspace / "main_plan.md"
    main_dest = workspace / "plan" / "main_plan.md"
    if main_src.exists() and not main_dest.exists():
        main_dest.parent.mkdir(parents=True, exist_ok=True)
        main_src.rename(main_dest)
        results.append("moved main_plan.md -> plan/main_plan.md")
    elif main_src.exists() and main_dest.exists():
        results.append(
            "both main_plan.md and plan/main_plan.md exist - plan/main_plan.md is canonical; "
            "review and remove the root copy manually"
        )

    root_mem = workspace / "MEMORY.md"
    canonical_mem = workspace / "memories" / "MEMORY.md"
    if root_mem.exists():
        if not canonical_mem.exists():
            canonical_mem.parent.mkdir(parents=True, exist_ok=True)
            root_mem.rename(canonical_mem)
            results.append("moved root MEMORY.md -> memories/MEMORY.md")
        elif root_mem.read_text(encoding="utf-8", errors="ignore").strip() == canonical_mem.read_text(
            encoding="utf-8", errors="ignore"
        ).strip():
            root_mem.unlink()
            results.append("removed root MEMORY.md (exact duplicate of memories/MEMORY.md)")
        else:
            backup = workspace / "memories" / "MEMORY.root-legacy.md"
            if backup.exists():
                results.append("root MEMORY.md differs from canonical and backup already exists - review manually")
            else:
                root_mem.rename(backup)
                results.append(
                    "root MEMORY.md differed from memories/MEMORY.md - preserved as memories/MEMORY.root-legacy.md; "
                    "merge anything still relevant into memories/MEMORY.md"
                )

    startup = workspace / "STARTUP_MEMORY.md"
    if startup.exists():
        dest = workspace / "memories" / "STARTUP_MEMORY.md"
        if dest.exists():
            results.append("STARTUP_MEMORY.md exists in both places - review manually")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            startup.rename(dest)
            results.append("moved legacy STARTUP_MEMORY.md -> memories/STARTUP_MEMORY.md")

    if not results:
        results.append("memory layout already organized")
    return results
