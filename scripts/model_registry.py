"""Load Loop Engineer model provider registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from model_paths import registry_path
from workspace_utils import ROOT


def _scalar(rest: str) -> Any:
    rest = rest.strip().strip('"').strip("'")
    if rest.isdigit():
        return int(rest)
    if rest.lower() in ("true", "false"):
        return rest.lower() == "true"
    return rest


def _parse_yaml_block(entries: list[tuple[int, str]], i: int, indent: int) -> tuple[Any, int]:
    """Parse a dict or list block starting at entries[i], which is at `indent`."""
    if i >= len(entries) or entries[i][0] != indent:
        return {}, i
    if entries[i][1].startswith("- "):
        items: list[Any] = []
        while i < len(entries) and entries[i][0] == indent and entries[i][1].startswith("- "):
            content = entries[i][1][2:]
            if ":" in content:
                key, _, raw_rest = content.partition(":")
                key = key.strip()
                item: dict[str, Any] = {}
                i += 1
                if raw_rest.strip():
                    item[key] = _scalar(raw_rest)
                else:
                    sub, i = _parse_yaml_block(entries, i, indent + 2)
                    item[key] = sub
                while i < len(entries) and entries[i][0] > indent:
                    sub_indent = entries[i][0]
                    sub_content = entries[i][1]
                    if ":" not in sub_content:
                        i += 1
                        continue
                    k2, _, r2 = sub_content.partition(":")
                    k2 = k2.strip()
                    i += 1
                    if r2.strip():
                        item[k2] = _scalar(r2)
                    else:
                        subval, i = _parse_yaml_block(entries, i, sub_indent + 2)
                        item[k2] = subval
                items.append(item)
            else:
                items.append(_scalar(content))
                i += 1
        return items, i
    node: dict[str, Any] = {}
    while i < len(entries) and entries[i][0] == indent:
        line = entries[i][1]
        if ":" not in line:
            i += 1
            continue
        key, _, raw_rest = line.partition(":")
        key = key.strip()
        i += 1
        if raw_rest.strip():
            node[key] = _scalar(raw_rest)
        else:
            sub, i = _parse_yaml_block(entries, i, indent + 2)
            node[key] = sub
    return node, i


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Indent-based YAML subset for registry/config files (stdlib only).

    Supports nested maps and lists of maps (one list per level), enough for
    `providers/registry.yml` and `~/.loop-engineer/data/model.yml`.
    """
    entries: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        entries.append((indent, raw.strip()))
    if not entries:
        return {}
    root, _ = _parse_yaml_block(entries, 0, entries[0][0])
    return root if isinstance(root, dict) else {}


def load_registry(root: Path | None = None) -> dict[str, dict]:
    path = registry_path(root or ROOT)
    if not path.exists():
        return {}
    data = _parse_simple_yaml(path.read_text(encoding="utf-8"))
    merged: dict[str, dict] = {}
    for section in ("providers", "ide_providers"):
        block = data.get(section, {})
        if isinstance(block, dict):
            for pid, meta in block.items():
                if isinstance(meta, dict):
                    merged[pid] = meta
    return merged


def get_provider(provider_id: str, root: Path | None = None) -> dict | None:
    reg = load_registry(root)
    if provider_id in reg:
        meta = dict(reg[provider_id])
        meta["id"] = provider_id
        return meta
    aliases = {
        "claude": "anthropic",
        "openai-api": "openai",
        "google": "gemini",
        "local": "ollama",
    }
    aid = aliases.get(provider_id)
    if aid and aid in reg:
        meta = dict(reg[aid])
        meta["id"] = aid
        return meta
    return None


def list_provider_ids(root: Path | None = None) -> list[str]:
    reg = load_registry(root)
    return sorted(k for k, v in reg.items() if v.get("auth") != "ide")


def resolve_model(provider_id: str, model_ref: str, root: Path | None = None) -> str:
    """Use model id as-is; empty ref falls back to provider default_model."""
    ref = model_ref.strip()
    if ref:
        return ref
    meta = get_provider(provider_id, root)
    return meta.get("default_model", "") if meta else ""
