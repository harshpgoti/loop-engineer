#!/usr/bin/env python3
"""Append-only, idempotent Loop lifecycle event store with payload redaction."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _policy(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "manifests" / "events.json").read_text(encoding="utf-8"))


def _redact(value: Any, sensitive: set[str]) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key.lower() in sensitive else _redact(item, sensitive) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, sensitive) for item in value]
    return value


def append(workspace: Path, event_type: str, payload: dict[str, Any] | None = None, *,
           idempotency_key: str, root: Path = ROOT) -> dict[str, Any]:
    policy = _policy(root)
    if event_type not in policy["events"]:
        raise ValueError(f"unknown event type: {event_type}")
    if not idempotency_key.strip():
        raise ValueError("idempotency key is required")
    destination = workspace / ".loop" / "events.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] | None = None
    if destination.exists():
        for line in destination.read_text(encoding="utf-8").splitlines():
            item = json.loads(line)
            if item.get("idempotency_key") == idempotency_key:
                existing = item
                break
    if existing:
        if existing["type"] != event_type:
            raise ValueError("idempotency key already belongs to another event type")
        return existing
    clean = _redact(payload or {}, set(policy["sensitive_keys"]))
    event_id = hashlib.sha256(f"{event_type}|{idempotency_key}".encode("utf-8")).hexdigest()[:20]
    event = {"version": 1, "id": event_id, "type": event_type,
             "recorded_at": datetime.now(timezone.utc).isoformat(),
             "idempotency_key": idempotency_key, "payload": clean}
    with destination.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def read(workspace: Path, event_type: str | None = None) -> list[dict[str, Any]]:
    path = workspace / ".loop" / "events.jsonl"
    if not path.exists():
        return []
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [item for item in events if event_type is None or item["type"] == event_type]
