"""Migration 003: ensure RELEASE_CHECK.md scaffold exists."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 3
NAME = "add_release_check"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    target = workspace / "RELEASE_CHECK.md"
    if target.exists():
        return []
    template = Path(__file__).resolve().parents[1] / "templates" / "release_check.template.md"
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return ["created RELEASE_CHECK.md scaffold"]
