"""Read/write active model provider configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from model_paths import model_config_path
from model_registry import get_provider, resolve_model


DEFAULT_CONFIG = """# Loop Engineer model config - ~/.loop-engineer/data/model.yml
version: 1
active:
  provider: ""
  model: ""
  custom_name: ""
fallback: []
custom:
  base_url: ""
  env_key: CUSTOM_API_KEY
custom_providers: []
context_length: ""
"""


def _parse_yaml(text: str) -> dict[str, Any]:
    from model_registry import _parse_simple_yaml

    return _parse_simple_yaml(text)


def load_config() -> dict[str, Any]:
    path = model_config_path()
    empty = {
        "version": 1,
        "active": {"provider": "", "model": "", "custom_name": ""},
        "fallback": [],
        "custom": {},
        "custom_providers": [],
        "context_length": "",
    }
    if not path.exists():
        return empty
    data = _parse_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return empty
    active = data.get("active") or {}
    if not isinstance(active, dict):
        active = {}
    fallback = data.get("fallback") or []
    if not isinstance(fallback, list):
        fallback = []
    custom_providers = data.get("custom_providers") or []
    if not isinstance(custom_providers, list):
        custom_providers = []
    return {
        "version": data.get("version", 1),
        "active": {
            "provider": active.get("provider", ""),
            "model": active.get("model", ""),
            "custom_name": active.get("custom_name", ""),
        },
        "fallback": [f for f in fallback if isinstance(f, dict)],
        "custom": data.get("custom") or {},
        "custom_providers": [c for c in custom_providers if isinstance(c, dict)],
        "context_length": data.get("context_length", ""),
    }


def _write_list_of_dicts(lines: list[str], key: str, items: list[dict[str, Any]]) -> None:
    if not items:
        lines.append(f"{key}: []")
        return
    lines.append(f"{key}:")
    for item in items:
        entries = list(item.items())
        if not entries:
            continue
        first_key, first_val = entries[0]
        lines.append(f"  - {first_key}: {first_val}")
        for k, v in entries[1:]:
            lines.append(f"    {k}: {v}")


def save_config(cfg: dict[str, Any]) -> Path:
    path = model_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    active = cfg.get("active") or {}
    provider = active.get("provider", "")
    model = active.get("model", "")
    custom_name = active.get("custom_name", "")
    lines = [
        "# Loop Engineer model config",
        "version: 1",
        "active:",
        f"  provider: {provider}",
        f"  model: {model}",
        f"  custom_name: {custom_name}",
    ]
    _write_list_of_dicts(lines, "fallback", cfg.get("fallback") or [])
    custom = cfg.get("custom") or {}
    if custom:
        lines.append("custom:")
        for k, v in custom.items():
            lines.append(f"  {k}: {v}")
    _write_list_of_dicts(lines, "custom_providers", cfg.get("custom_providers") or [])
    context_length = cfg.get("context_length", "")
    if context_length:
        lines.append(f"context_length: {context_length}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def get_custom_provider(name: str, cfg: dict[str, Any] | None = None) -> dict[str, Any] | None:
    cfg = cfg or load_config()
    for entry in cfg.get("custom_providers") or []:
        if entry.get("name") == name:
            return entry
    return None


def add_custom_provider(name: str, base_url: str, env_key: str = "") -> dict[str, Any]:
    cfg = load_config()
    providers = [c for c in cfg.get("custom_providers") or [] if c.get("name") != name]
    entry: dict[str, Any] = {"name": name, "base_url": base_url}
    if env_key:
        entry["env_key"] = env_key
    providers.append(entry)
    cfg["custom_providers"] = providers
    save_config(cfg)
    return entry


def parse_selection(text: str, root: Path | None = None) -> tuple[str, str, str]:
    """Parse a selection string into (provider_id, model, custom_name).

    Forms:
      provider                        -> (provider, default_model, "")
      provider:model                  -> (provider, model, "")
      custom:name:model               -> ("custom", model, name)
    """
    text = text.strip()
    if text.startswith("custom:"):
        rest = text[len("custom:") :]
        if ":" in rest:
            name, _, model_ref = rest.partition(":")
            return "custom", model_ref.strip(), name.strip()
        return "custom", "", rest.strip()
    if ":" in text:
        provider_id, model_ref = text.split(":", 1)
        provider_id = provider_id.strip().lower()
        meta = get_provider(provider_id, root)
        if not meta:
            return provider_id, model_ref.strip(), ""
        return meta["id"], resolve_model(meta["id"], model_ref.strip(), root), ""
    provider_id = text.strip().lower()
    meta = get_provider(provider_id, root)
    if not meta:
        return provider_id, "", ""
    return meta["id"], resolve_model(meta["id"], "", root), ""


def set_active(
    provider_id: str, model: str = "", root: Path | None = None, custom_name: str = ""
) -> dict[str, Any]:
    meta = get_provider(provider_id, root)
    if not meta:
        raise ValueError(f"Unknown provider: {provider_id}")
    cfg = load_config()
    if meta["id"] == "custom" and custom_name:
        entry = get_custom_provider(custom_name, cfg)
        if not entry:
            raise ValueError(
                f"Unknown custom provider `{custom_name}` - run: "
                f"loop model custom add {custom_name} <base_url>"
            )
        model = model or ""
    else:
        model = resolve_model(meta["id"], model, root)
    cfg["active"] = {"provider": meta["id"], "model": model, "custom_name": custom_name}
    if meta["id"] == "custom" and not custom_name and not cfg.get("custom", {}).get("base_url"):
        cfg.setdefault("custom", {})["base_url"] = meta.get("base_url", "")
    save_config(cfg)
    return cfg


def add_fallback(provider_id: str, model: str = "", root: Path | None = None) -> dict[str, Any]:
    meta = get_provider(provider_id, root)
    if not meta:
        raise ValueError(f"Unknown provider: {provider_id}")
    model = resolve_model(meta["id"], model, root)
    cfg = load_config()
    fallback = cfg.get("fallback") or []
    fallback = [f for f in fallback if not (f.get("provider") == meta["id"] and f.get("model") == model)]
    fallback.append({"provider": meta["id"], "model": model})
    cfg["fallback"] = fallback
    save_config(cfg)
    return cfg


def clear_fallback() -> dict[str, Any]:
    cfg = load_config()
    cfg["fallback"] = []
    save_config(cfg)
    return cfg


def set_context_length(value: str) -> dict[str, Any]:
    cfg = load_config()
    cfg["context_length"] = value
    save_config(cfg)
    return cfg


def active_summary(root: Path | None = None) -> str:
    cfg = load_config()
    active = cfg.get("active") or {}
    pid = active.get("provider") or "(none)"
    model = active.get("model") or "(default)"
    custom_name = active.get("custom_name")
    if pid != "(none)" and pid == "custom" and custom_name:
        return f"custom:{custom_name} - {model}"
    meta = get_provider(pid, root) if pid != "(none)" else None
    label = meta.get("label", pid) if meta else pid
    return f"{label} - {model}"


def resolve_api_target(root: Path | None = None) -> dict[str, str]:
    """Resolved endpoint + model for automation scripts."""
    from model_paths import load_secrets_env, merge_env_secrets

    merge_env_secrets()
    cfg = load_config()
    active = cfg.get("active") or {}
    pid = active.get("provider", "")
    model = active.get("model", "")
    custom_name = active.get("custom_name", "")
    meta = get_provider(pid, root) if pid else None
    if not meta:
        return {"provider": "", "model": "", "base_url": "", "api_mode": "", "env_key": ""}
    base_url = meta.get("base_url", "")
    env_key = meta.get("env_key", "")
    label = meta.get("label", pid)
    if pid == "custom":
        if custom_name:
            entry = get_custom_provider(custom_name, cfg) or {}
            base_url = entry.get("base_url") or base_url
            env_key = entry.get("env_key") or env_key
            label = f"custom:{custom_name}"
        else:
            custom = cfg.get("custom") or {}
            base_url = custom.get("base_url") or base_url
            env_key = custom.get("env_key") or env_key
    secrets = load_secrets_env()
    has_key = bool(secrets.get(env_key) or (meta.get("env_key_alt") and secrets.get(meta["env_key_alt"])))
    if meta.get("auth") in ("none", "optional_key", "ide"):
        has_key = True
    return {
        "provider": pid,
        "model": model or meta.get("default_model", ""),
        "label": label,
        "base_url": base_url,
        "api_mode": meta.get("api_mode", "openai_chat"),
        "env_key": env_key,
        "has_key": str(has_key),
        "context_length": str(cfg.get("context_length", "") or meta.get("context_min", "")),
        "fallback": cfg.get("fallback") or [],
    }
