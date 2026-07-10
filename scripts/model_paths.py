"""Paths for Loop Engineer model provider config."""

from __future__ import annotations

import os
from pathlib import Path

from loop_home import data_home


def model_config_path() -> Path:
    return data_home() / "model.yml"


def secrets_env_path() -> Path:
    return data_home() / "secrets.env"


def registry_path(root: Path) -> Path:
    return root / "providers" / "registry.yml"


def workspace_model_status(workspace: Path) -> Path:
    return workspace / "plan" / "MODEL_STATUS.md"


def load_secrets_env() -> dict[str, str]:
    path = secrets_env_path()
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def merge_env_secrets() -> None:
    """Overlay secrets.env into os.environ without overwriting existing."""
    for key, val in load_secrets_env().items():
        if key not in os.environ and val:
            os.environ[key] = val
