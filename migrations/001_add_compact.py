"""Migration 001: ensure COMPACT.md exists in older workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 1
NAME = "add_compact"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    result = seed(workspace, "COMPACT.md", "templates/starter/COMPACT.md")
    return [result] if result else []
