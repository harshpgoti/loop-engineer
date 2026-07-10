"""Resolve product workspace: local folder vs global ~/.loop-engineer data.

Local product data lives under <product-folder>/.loop-engineer/ — a single
hidden folder holding everything (memories/, state.db, main_plan.md, plan/,
...), kept out of the way of the product's own code, mirroring how
~/.loop-engineer/data/ separates data from app/ globally.
"""

from __future__ import annotations

import os
from pathlib import Path

from loop_home import app_path, global_data_home, loop_home

LOCAL_DATA_DIRNAME = ".loop-engineer"

LOCAL_MARKER_FILES = (
    ".loop-workspace-version",
    "memories/MEMORY.md",
    "memories/USER.md",
)
TOOL_MARKER_FILES = (
    "commands/plan.md",
    "scripts/setup_loop_engine.py",
    "scripts/loop_cli.py",
)


def is_tool_runtime(path: Path) -> bool:
    resolved = path.resolve()
    if resolved == app_path().resolve():
        return True
    return all((resolved / rel).exists() for rel in TOOL_MARKER_FILES[:2])


def is_global_data_home(path: Path) -> bool:
    return path.resolve() == global_data_home().resolve()


def local_data_dir(product_folder: Path) -> Path:
    """The nested data root for a local product folder."""
    return product_folder / LOCAL_DATA_DIRNAME


def _has_markers_at(root: Path) -> bool:
    for rel in LOCAL_MARKER_FILES:
        if (root / rel).exists():
            return True
    if (root / "memories").is_dir() and (
        (root / "plan" / "main_plan.md").exists() or (root / "main_plan.md").exists()
    ):
        return True
    return False


def has_local_loop_data(path: Path) -> bool:
    """True if `path` is a product folder with a `.loop-engineer/` data dir."""
    if not path.is_dir():
        return False
    if is_tool_runtime(path):
        return False
    if is_global_data_home(path):
        return has_global_loop_data(path)
    return _has_markers_at(local_data_dir(path))


def has_global_loop_data(path: Path | None = None) -> bool:
    root = (path or global_data_home()).resolve()
    return _has_markers_at(root)


def find_local_workspace(start: Path | None = None) -> Path | None:
    """Walk from start (default cwd) upward for a product folder with a
    `.loop-engineer/` data dir. Returns the nested data dir itself, since
    that's what every caller treats as "the workspace."""
    current = (start or Path.cwd()).resolve()
    checked: set[str] = set()
    for path in [current, *current.parents]:
        key = str(path)
        if key in checked:
            continue
        checked.add(key)
        if is_tool_runtime(path):
            continue
        if is_global_data_home(path):
            continue
        if _has_markers_at(local_data_dir(path)):
            return local_data_dir(path)
    return None


def resolve_effective_workspace(
    explicit: str | None = None,
    *,
    cwd: Path | None = None,
) -> tuple[Path, str]:
    """Return (workspace_path, mode) where mode is 'local' or 'global'.

    `workspace_path` is always the actual data root — `.loop-engineer/`
    already appended for local mode, `~/.loop-engineer/data/` for global.
    """
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if is_global_data_home(path):
            return path, "global"
        if path.resolve() == loop_home().resolve():
            # Someone passed the LOOP_ENGINEER_HOME root itself (which is
            # typically also named ".loop-engineer") — that's the parent of
            # app/ + data/, not a product folder. Redirect to the data root.
            return global_data_home(), "global"
        if is_tool_runtime(path):
            # The tool runtime holds no product state — route to global data.
            return global_data_home(), "global"
        if path.name == LOCAL_DATA_DIRNAME:
            return path, "local"
        if _has_markers_at(path) or (path / "plan" / "main_plan.md").exists():
            # The path itself already looks like a data root (e.g. an explicit
            # data dir, templates/starter, or a legacy flat workspace).
            return path, "local"
        # A raw product folder was passed explicitly — resolve to its data dir.
        return local_data_dir(path), "local"

    local = find_local_workspace(cwd)
    if local is not None:
        return local, "local"

    home = global_data_home()
    return home, "global"


def describe_resolution(workspace: Path, mode: str) -> str:
    if mode == "local":
        return f"Using local product data in `{workspace}` (detected from current folder)."
    return f"Using global product data in `{workspace}` (no local loop data in current folder)."
