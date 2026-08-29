"""Shared workspace helpers for Loop Engineering OS scripts."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from loop_home import registry_path
from workspace_resolver import resolve_effective_workspace


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path, max_chars: int | None = None, *, strip: bool = True) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = text.strip() if strip else text
    if max_chars is not None and len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n\n_...truncated_"
    return text


def extract_line(text: str, prefix: str, default: str = "TBD") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def load_template(name: str, fallback: str | None = None) -> str:
    path = ROOT / "templates" / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    if fallback is not None:
        return fallback
    raise FileNotFoundError(path)


def render_template(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def bullet(items: list[str], empty: str = "- None.") -> str:
    return "\n".join(f"- {item}" for item in items) if items else empty


def append_session_log(workspace: Path, title: str, lines: list[str]) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"- {line}" for line in lines)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {date.today().isoformat()} - {title}\n\n{body}\n")


def console_utf8() -> None:
    """Let this process print product text on a cp1252 console.

    `loop` sets PYTHONIOENCODING for the scripts it launches; this covers running a
    script directly, which is what the skills' documented `python scripts/x.py` lines
    do. Replacement is deliberate - a mangled character beats a crashed command.
    """
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def config_path() -> Path:
    """Registry location: global ~/.loop-engineer/data/registry/workspaces.json.

    A legacy `.loop-workspaces.json` at the tool repo root is honored read-only
    when the global registry doesn't exist yet. New writes always go global -
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
                # Registry entries name the product folder. Local product state is
                # nested beneath it; returning the product root silently creates a
                # second, flat workspace beside the canonical `.loop-engineer/` one.
                nested = resolved / ".loop-engineer"
                return nested if nested.is_dir() else resolved

    return auto_path


def get_workspace_mode(workspace: Path | None = None) -> str:
    path = workspace or resolve_workspace()
    _, mode = resolve_effective_workspace(str(path))
    return mode
