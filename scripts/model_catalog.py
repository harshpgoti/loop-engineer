"""Fetch available models from provider APIs (live catalog, not registry)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from model_config import load_config
from model_paths import load_secrets_env, merge_env_secrets
from model_registry import get_provider


def _resolve_custom(cfg: dict) -> tuple[str, str]:
    """Return (base_url, env_key) for the active custom provider (named or default)."""
    active = cfg.get("active") or {}
    custom_name = active.get("custom_name", "")
    if custom_name:
        from model_config import get_custom_provider

        entry = get_custom_provider(custom_name, cfg) or {}
        return entry.get("base_url", ""), entry.get("env_key", "")
    custom = cfg.get("custom") or {}
    return custom.get("base_url", ""), custom.get("env_key", "")


def _api_token(meta: dict, env_key_override: str = "") -> str:
    merge_env_secrets()
    env_key = env_key_override or meta.get("env_key", "")
    alt = meta.get("env_key_alt")
    token = os.environ.get(env_key, "")
    if not token and alt:
        token = os.environ.get(alt, "")
    if not token:
        secrets = load_secrets_env()
        token = secrets.get(env_key, "") or (secrets.get(alt or "", "") if alt else "")
    return token


def _resolve_base_url(provider_id: str, meta: dict) -> str:
    base_url = meta.get("base_url", "")
    if provider_id == "custom":
        base_url, _ = _resolve_custom(load_config())
        base_url = base_url or meta.get("base_url", "")
    return base_url.rstrip("/")


def _http_get_json(url: str, headers: dict[str, str], timeout: int = 15) -> tuple[bool, dict | list, str]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512_000).decode("utf-8", errors="ignore")
            return True, json.loads(body), ""
    except urllib.error.HTTPError as e:
        chunk = e.read(512).decode("utf-8", errors="ignore") if e.fp else ""
        return False, {}, f"HTTP {e.code}: {chunk[:200]}"
    except urllib.error.URLError as e:
        return False, {}, f"connection failed: {e.reason}"
    except json.JSONDecodeError as e:
        return False, {}, f"invalid JSON: {e}"
    except Exception as e:
        return False, {}, str(e)


def _parse_openai_models(payload: dict | list) -> list[str]:
    if isinstance(payload, list):
        data = payload
    elif isinstance(payload, dict):
        data = payload.get("data") or payload.get("models") or []
    else:
        return []
    ids: list[str] = []
    for item in data:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict):
            mid = item.get("id") or item.get("name")
            if mid:
                ids.append(str(mid))
    return sorted(set(ids))


def _parse_anthropic_models(payload: dict | list) -> list[str]:
    if isinstance(payload, dict):
        data = payload.get("data") or []
    elif isinstance(payload, list):
        data = payload
    else:
        return []
    ids: list[str] = []
    for item in data:
        if isinstance(item, dict):
            mid = item.get("id") or item.get("name")
            if mid:
                ids.append(str(mid))
    return sorted(set(ids))


def fetch_provider_models(provider_id: str, root: Path | None = None) -> tuple[bool, list[str], str]:
    """Return (ok, model_ids, message) from the provider's live API."""
    meta = get_provider(provider_id, root)
    if not meta:
        return False, [], f"unknown provider `{provider_id}`"
    if meta.get("auth") == "ide":
        return False, [], "IDE provider has no external model catalog"

    base_url = _resolve_base_url(provider_id, meta)
    api_mode = meta.get("api_mode", "openai_chat")
    env_key_override = ""
    if provider_id == "custom":
        _, env_key_override = _resolve_custom(load_config())
    token = _api_token(meta, env_key_override)
    auth = meta.get("auth", "api_key")

    if api_mode == "anthropic_messages":
        if auth == "api_key" and not token:
            return False, [], f"missing {meta.get('env_key')} - run: loop model set-key {meta.get('env_key')}"
        headers = {
            "anthropic-version": "2023-06-01",
            "x-api-key": token,
        }
        url = (base_url or "https://api.anthropic.com/v1").rstrip("/") + "/models"
        ok, payload, err = _http_get_json(url, headers)
        if not ok:
            return False, [], err
        return True, _parse_anthropic_models(payload), f"{len(_parse_anthropic_models(payload))} models"

    if not base_url:
        return False, [], "no base_url - configure provider endpoint first"

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    elif auth == "api_key":
        return False, [], f"missing {meta.get('env_key')} - run: loop model set-key {meta.get('env_key')}"

    url = base_url.rstrip("/") + "/models"
    ok, payload, err = _http_get_json(url, headers)
    if not ok:
        return False, [], err
    models = _parse_openai_models(payload)
    return True, models, f"{len(models)} models"


def filter_models(models: list[str], query: str = "") -> list[str]:
    q = query.strip().lower()
    if not q:
        return models
    return [m for m in models if q in m.lower()]
