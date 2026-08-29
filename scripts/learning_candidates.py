#!/usr/bin/env python3
"""Govern repeated observations without silently rewriting skills or rules."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|password|secret|bearer\s+[a-z0-9._-]+|token\s*[:=])")


def _path(workspace: Path) -> Path:
    return workspace / ".loop" / "learning" / "observations.jsonl"


def observe(workspace: Path, *, pattern: str, evidence: str, session_id: str,
            confidence: float, source: str) -> dict[str, Any]:
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if not all(value.strip() for value in (pattern, evidence, session_id, source)):
        raise ValueError("pattern, evidence, session_id, and source are required")
    if SECRET_PATTERN.search(f"{pattern}\n{evidence}"):
        raise ValueError("observation may contain sensitive data")
    normalized = re.sub(r"\s+", " ", pattern.strip().lower())
    fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]
    item = {"version": 1, "fingerprint": fingerprint, "pattern": pattern.strip(),
            "evidence": evidence.strip(), "session_id": session_id, "confidence": confidence,
            "source": source, "observed_at": datetime.now(timezone.utc).isoformat()}
    destination = _path(workspace)
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing = observations(workspace)
    if any(row["fingerprint"] == fingerprint and row["session_id"] == session_id for row in existing):
        return next(row for row in existing if row["fingerprint"] == fingerprint and row["session_id"] == session_id)
    with destination.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(item, sort_keys=True) + "\n")
    return item


def observations(workspace: Path) -> list[dict[str, Any]]:
    path = _path(workspace)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def candidates(workspace: Path, *, min_sessions: int = 3, min_confidence: float = 0.8) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in observations(workspace):
        grouped.setdefault(item["fingerprint"], []).append(item)
    result = []
    for fingerprint, rows in grouped.items():
        sessions = {row["session_id"] for row in rows}
        average = sum(float(row["confidence"]) for row in rows) / len(rows)
        result.append({"fingerprint": fingerprint, "pattern": rows[-1]["pattern"],
                       "observations": len(rows), "distinct_sessions": len(sessions),
                       "average_confidence": round(average, 4),
                       "eligible": len(sessions) >= min_sessions and average >= min_confidence,
                       "sources": sorted({row["source"] for row in rows})})
    return sorted(result, key=lambda item: (-item["distinct_sessions"], item["fingerprint"]))


def promote(workspace: Path, fingerprint: str, *, approved_by: str) -> Path:
    if not approved_by.strip():
        raise ValueError("explicit approver identity is required")
    match = next((item for item in candidates(workspace) if item["fingerprint"] == fingerprint), None)
    if not match or not match["eligible"]:
        raise ValueError("candidate is not eligible for promotion")
    destination = workspace / ".loop" / "pending" / f"learning-{fingerprint}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({"version": 1, "candidate": match, "approved_by": approved_by,
                                       "status": "pending-review"}, indent=2) + "\n", encoding="utf-8")
    return destination
