"""Migration 004: ensure STATUS.md, DOCTOR.md, and SYNC_REPORT.md scaffolds exist."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 4
NAME = "add_status_doctor_sync"


SCAFFOLDS = {
    "STATUS.md": "templates/status.template.md",
    "DOCTOR.md": "templates/doctor.template.md",
    "SYNC_REPORT.md": "templates/sync_loop_state.template.md",
}


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    root = Path(__file__).resolve().parents[1]
    results: list[str] = []
    for target_name, template_rel in SCAFFOLDS.items():
        target = workspace / target_name
        if target.exists():
            continue
        template = root / template_rel
        if not template.exists():
            results.append(f"missing template for {target_name}")
            continue
        target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        results.append(f"created {target_name} scaffold")
    version_result = seed(workspace, ".loop-workspace-version", "templates/starter/.loop-workspace-version")
    if version_result:
        results.append(version_result)
    return results
