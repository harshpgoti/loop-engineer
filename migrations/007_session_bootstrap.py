"""Migration 007: SOUL/CONTEXT bootstrap, pending write dirs, recall/review scaffolds."""

from __future__ import annotations

from pathlib import Path
from typing import Callable


MIGRATION_ID = 7
NAME = "session_bootstrap"


def apply(workspace: Path, seed: Callable[[Path, str, str], str | None]) -> list[str]:
    from memory_paths import ensure_memory_layout

    results = [f"{key}: {value}" for key, value in ensure_memory_layout(workspace).items()]

    for rel, source in (
        ("plan/SESSION_RECALL.md", "templates/session_recall.template.md"),
        ("plan/MEMORY_REVIEW.md", "templates/memory_review.template.md"),
    ):
        created = seed(workspace, rel, source)
        if created:
            results.append(created)

    pending = workspace / ".loop" / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    (pending / "memory").mkdir(parents=True, exist_ok=True)
    (pending / "skills").mkdir(parents=True, exist_ok=True)
    results.append("pending write dirs: ensured")
    return results
