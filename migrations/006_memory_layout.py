"""Migration 006: memory layout (memories/, USER.md, state.db, user skills/)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 6
NAME = "memory_layout"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    from memory_paths import ensure_memory_layout, state_db
    from session_store import init_db

    results = [f"{key}: {value}" for key, value in ensure_memory_layout(workspace).items()]
    db = state_db(workspace)
    if not db.exists():
        init_db(db)
        results.append("initialized state.db")
    else:
        results.append("state.db: exists")
    return results
