"""Load the declarative coding-harness capability registry."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_DIR = ROOT / "harnesses"
PATH_FIELDS = ("skill_paths", "command_paths", "permission_paths", "legacy_command_paths")
REQUIRED_FIELDS = ("name", "skill_paths", "invocation", "trust", "hooks")


def load_adapters(folder: Path = ADAPTERS_DIR) -> dict[str, dict]:
    adapters: dict[str, dict] = {}
    for path in sorted(folder.glob("*.json")):
        if path.name == "worker_versions.json":
            continue
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
VERIFIED_VERSIONS_PATH = ADAPTERS_DIR / "worker_versions.json"
VERIFIED_VERSIONS = json.loads(VERIFIED_VERSIONS_PATH.read_text(encoding="utf-8")) if VERIFIED_VERSIONS_PATH.exists() else {}

BINARY_NAMES = {"claude": "claude", "codex": "codex", "cursor": "cursor-agent", "opencode": "opencode", "grok": "grok", "pi": "pi", "kimi": "kimi"}
LAUNCH_TEMPLATES = {
    "claude": ["claude", "{pointer}"], "codex": ["codex", "{pointer}"],
    "cursor": ["cursor-agent", "--trust", "{pointer}"], "opencode": ["opencode", "{pointer}"],
    "grok": ["grok", "{pointer}"], "pi": ["pi", "{pointer}"], "kimi": ["kimi", "--auto"],
}


def executable_contract(name: str) -> dict:
    if name not in ADAPTERS:
        raise ValueError(f"unknown harness adapter: {name}")
    binary = BINARY_NAMES.get(name)
    path = shutil.which(binary) if binary else None
    version = ""
    version_ok = False
    if path:
        result = subprocess.run([path, "--version"], text=True, capture_output=True, check=False, timeout=10)
        version = (result.stdout or result.stderr).strip().splitlines()[0][:200] if (result.stdout or result.stderr).strip() else "unknown"
        version_ok = result.returncode == 0 and VERIFIED_VERSIONS.get(name) == version
    status = "verified-local" if version_ok else ("version-drift" if path and name in VERIFIED_VERSIONS else ("preflight-failed" if path else "unsupported-local"))
    return {"name": name, "advertised": version_ok, "available": bool(path), "binary": path or binary or "", "version": version, "pinned_version": VERIFIED_VERSIONS.get(name, ""), "launch_template": LAUNCH_TEMPLATES.get(name, []), "supports_pointer_launch": name in LAUNCH_TEMPLATES, "verified_at": datetime.now(timezone.utc).isoformat() if version_ok else "", "status": status}


def compatibility_matrix() -> list[dict]:
    return [executable_contract(name) for name in sorted(ADAPTERS)]


def write_compatibility_matrix(path: Path) -> Path:
    rows = compatibility_matrix()
    lines = ["# Worker Harness Compatibility", "", "Generated from executable local preflights; unavailable tools are not advertised as runnable.", "", "| Harness | Local status | Version | Pointer launch |", "|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['name']} | {row['status']} | {row['version'] or '-'} | {'yes' if row['supports_pointer_launch'] and row['advertised'] else 'no'} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def path_table(field: str) -> dict[str, dict[str, str]]:
    if field not in PATH_FIELDS:
        raise ValueError(f"unknown harness path field: {field}")
    return {name: adapter[field] for name, adapter in ADAPTERS.items() if field in adapter}
