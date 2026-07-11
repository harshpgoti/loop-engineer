"""Connectivity checks for configured model providers."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from model_config import load_config, resolve_api_target
from model_paths import load_secrets_env, merge_env_secrets
from model_registry import get_provider, list_provider_ids


def _auth_header(env_key: str, env_key_alt: str | None = None) -> dict[str, str]:
    merge_env_secrets()
    token = os.environ.get(env_key, "") or (os.environ.get(env_key_alt or "", "") if env_key_alt else "")
    if not token:
        secrets = load_secrets_env()
        token = secrets.get(env_key, "") or secrets.get(env_key_alt or "", "")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def check_provider_key(
    provider_id: str, root: Path | None = None, custom_name: str = ""
) -> tuple[bool, str]:
    meta = get_provider(provider_id, root)
    if not meta:
        return False, f"unknown provider `{provider_id}`"
    auth = meta.get("auth", "api_key")
    if auth == "ide":
        return True, "IDE-hosted - no API key required"
    if auth == "none":
        return True, "local endpoint - no API key required"
    env_key = meta.get("env_key", "")
    if provider_id == "custom" and custom_name:
        from model_config import get_custom_provider, load_config

        entry = get_custom_provider(custom_name, load_config()) or {}
        env_key = entry.get("env_key") or env_key
        if not env_key:
            return True, f"custom:{custom_name} - no key configured"
    alt = meta.get("env_key_alt")
    merge_env_secrets()
    if os.environ.get(env_key) or (alt and os.environ.get(alt)):
        return True, f"{env_key} set"
    secrets = load_secrets_env()
    if secrets.get(env_key) or (alt and secrets.get(alt)):
        return True, f"{env_key} in secrets.env"
    if auth == "optional_key":
        return True, f"{env_key} optional (not set)"
    return False, f"missing {env_key} - run: loop model set-key {env_key}"


def probe_openai_compatible(base_url: str, headers: dict[str, str], timeout: int = 8) -> tuple[bool, str]:
    url = base_url.rstrip("/") + "/models"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096).decode("utf-8", errors="ignore")
            if resp.status == 200:
                return True, "reachable (/models OK)"
            return False, f"HTTP {resp.status}: {body[:120]}"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, f"HTTP {e.code} - check API key"
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"connection failed: {e.reason}"
    except Exception as e:
        return False, str(e)


def doctor_active(root: Path | None = None) -> list[tuple[str, bool, str]]:
    cfg = load_config()
    active = cfg.get("active") or {}
    pid = active.get("provider", "")
    results: list[tuple[str, bool, str]] = []
    if not pid:
        results.append(("active", False, "no provider selected - run: loop model setup"))
        return results
    custom_name = active.get("custom_name", "")
    ok, msg = check_provider_key(pid, root, custom_name)
    key_label = f"custom:{custom_name}" if pid == "custom" and custom_name else pid
    results.append((f"key:{key_label}", ok, msg))
    target = resolve_api_target(root)
    meta = get_provider(pid, root)
    if not meta:
        results.append(("registry", False, "provider missing from registry"))
        return results
    if meta.get("auth") == "ide":
        results.append(("probe", True, "IDE provider - skip HTTP probe"))
        return results
    base_url = target.get("base_url", "")
    if not base_url:
        results.append(("probe", False, "no base_url configured"))
        return results
    headers = {"Content-Type": "application/json"}
    headers.update(_auth_header(target.get("env_key", ""), meta.get("env_key_alt")))
    ok, msg = probe_openai_compatible(base_url, headers)
    results.append(("probe", ok, msg))
    return results


def doctor_all_keys(root: Path | None = None) -> list[tuple[str, bool, str]]:
    rows = []
    for pid in list_provider_ids(root):
        ok, msg = check_provider_key(pid, root)
        rows.append((pid, ok, msg))
    return rows
