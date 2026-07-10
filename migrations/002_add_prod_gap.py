"""Migration 002: ensure plan/PROD-GAP.md scaffold exists."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 2
NAME = "add_prod_gap"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    target = workspace / "plan" / "PROD-GAP.md"
    if target.exists():
        return []
    template = Path(__file__).resolve().parents[1] / "templates" / "prod_gap.template.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return ["created plan/PROD-GAP.md scaffold"]
