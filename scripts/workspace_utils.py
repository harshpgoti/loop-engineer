"""Shared workspace helpers for Loop Engineering OS scripts."""

from __future__ import annotations

import json
from pathlib import Path

from loop_home import registry_path
from workspace_resolver import resolve_effective_workspace


ROOT = Path(__file__).resolve().parents[1]


def config_path() -> Path:
    """Registry location: global ~/.loop-engineer/data/registry/workspaces.json.

    A legacy `.loop-workspaces.json` at the tool repo root is honored read-only
    when the global registry doesn't exist yet. New writes always go global —
    the tool repo is never a write target (save_config creates the parent dir).
    """
    global_registry = registry_path()
    if global_registry.exists():
        return global_registry
    legacy = ROOT / ".loop-workspaces.json"
    if legacy.exists():
        return legacy
    return global_registry


CONFIG_PATH = config_path()


def _resolve_from_root(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    return (ROOT / path).resolve()


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {"current": None, "workspaces": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_config(config: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_workspace(workspace: str | None = None) -> Path:
    """Resolve workspace with auto-detection.

    Priority:
    1. Explicit --workspace argument
    2. Local loop data in cwd or a parent folder (excluding tool runtime)
    3. Registered current workspace (when set)
    4. Global data home (~/.loop-engineer)
    """
    if workspace:
        resolved, _ = resolve_effective_workspace(workspace)
        return resolved

    auto_path, mode = resolve_effective_workspace(None)
    if mode == "local":
        return auto_path

    config = load_config()
    current = config.get("current")
    workspaces = config.get("workspaces", {})
    if current and current in workspaces:
        entry = workspaces[current]
        raw_path = entry.get("path", "")
        if raw_path:
            resolved = _resolve_from_root(raw_path) if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
            if entry.get("memory_mode") == "local" and resolved.exists():
                return resolved

    return auto_path


def get_workspace_mode(workspace: Path | None = None) -> str:
    path = workspace or resolve_workspace()
    _, mode = resolve_effective_workspace(str(path))
    return mode
