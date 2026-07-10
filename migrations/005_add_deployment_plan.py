"""Migration 005: ensure DEPLOYMENT_PLAN.md scaffold exists."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 5
NAME = "add_deployment_plan"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    target = workspace / "DEPLOYMENT_PLAN.md"
    if target.exists():
        return []
    template = Path(__file__).resolve().parents[1] / "templates" / "deployment_plan.template.md"
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return ["created DEPLOYMENT_PLAN.md scaffold"]
