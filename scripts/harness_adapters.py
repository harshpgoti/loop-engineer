"""Load the declarative coding-harness capability registry."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = ROOT / "harnesses"
PATH_FIELDS = ("skill_paths", "command_paths", "permission_paths", "legacy_command_paths")
REQUIRED_FIELDS = ("name", "skill_paths", "invocation", "trust", "hooks")


def load_adapters(folder: Path = ADAPTERS_DIR) -> dict[str, dict]:
    adapters: dict[str, dict] = {}
    for path in sorted(folder.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        missing = [field for field in REQUIRED_FIELDS if field not in data]
        if missing:
            raise ValueError(f"{path.name}: missing {', '.join(missing)}")
        name = data["name"]
        if name != path.stem:
            raise ValueError(f"{path.name}: name must match filename")
        if name in adapters:
            raise ValueError(f"duplicate harness adapter: {name}")
        for field in PATH_FIELDS:
            if field not in data:
                continue
            paths = data[field]
            if set(paths) != {"user", "project"} or not all(isinstance(v, str) and v for v in paths.values()):
                raise ValueError(f"{path.name}: {field} needs non-empty user and project paths")
        adapters[name] = data
    if not adapters:
        raise ValueError(f"no harness adapters found in {folder}")
    return adapters


ADAPTERS = load_adapters()


def path_table(field: str) -> dict[str, dict[str, str]]:
    if field not in PATH_FIELDS:
        raise ValueError(f"unknown harness path field: {field}")
    return {name: adapter[field] for name, adapter in ADAPTERS.items() if field in adapter}

