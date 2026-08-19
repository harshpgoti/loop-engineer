#!/usr/bin/env python3
"""What the user decided about a hierarchy finding - the only part worth storing.

A finding is *derived*: `hierarchy_drift` recomputes it from two plan files every
sync, so it has no independent existence. The old approval queue stored a frozen
copy of each one, which could not self-heal - this repo's own sub-product ended up
holding six queued notes for findings that no longer existed.

So findings are never persisted. Decisions about them are:

    .loop/finding-log.json
    {"resolutions": {"<finding id>": {"decision": ..., "value_key": ...}}}

A resolution is bound to the **values it was made about** (`value_key`). Declining
"the platform says AWS" must not silently suppress "the platform now says GCP" -
when the upstream value changes, the resolution stops applying and the finding
comes back.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

LOG_FILE = ".loop/finding-log.json"

ACCEPTED = "accepted"
DECLINED = "declined"
DEFERRED = "deferred"
DECISIONS = (ACCEPTED, DECLINED, DEFERRED)

# How long a deferred finding stays quiet before it is worth raising again.
DEFER_DAYS = 7


def log_path(workspace: Path) -> Path:
    return workspace / LOG_FILE


def value_key(finding: dict) -> str:
    """Identity of the *substance* of a finding, so a changed value reopens it."""
    material = str(finding.get("material") or finding.get("detail") or "")
    return sha256(material.strip().encode("utf-8")).hexdigest()[:16]


def read_log(workspace: Path) -> dict:
    path = log_path(workspace)
    if not path.exists():
        return {"version": 1, "resolutions": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "resolutions": {}}
    if not isinstance(data, dict) or not isinstance(data.get("resolutions"), dict):
        return {"version": 1, "resolutions": {}}
    return data


def write_log(workspace: Path, log: dict) -> Path:
    path = log_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def resolve(workspace: Path, finding: dict, decision: str, *, note: str = "") -> dict:
    """Record what the user decided about one finding."""
    if decision not in DECISIONS:
        raise ValueError(f"unknown decision: {decision} (expected one of {', '.join(DECISIONS)})")

    entry = {
        "decision": decision,
        "at": datetime.now(timezone.utc).isoformat(),
        "value_key": value_key(finding),
        "kind": finding.get("kind", ""),
        "detail": finding.get("detail", "")[:400],
        "note": note.strip(),
    }
    if decision == DEFERRED:
        entry["resurface_after"] = (date.today() + timedelta(days=DEFER_DAYS)).isoformat()

    log = read_log(workspace)
    log["resolutions"][str(finding.get("id"))] = entry
    write_log(workspace, log)
    return entry


def resolution_for(workspace: Path, finding: dict, log: dict | None = None) -> dict | None:
    """The live resolution for this finding, or None if it still needs an answer.

    Returns None when the resolution was made about different values, or when a
    deferral has run out - both mean the question is open again.
    """
    log = log if log is not None else read_log(workspace)
    entry = log.get("resolutions", {}).get(str(finding.get("id")))
    if not entry:
        return None
    if entry.get("value_key") != value_key(finding):
        return None  # the upstream value moved - this decision was about something else
    if entry.get("decision") == DEFERRED:
        after = str(entry.get("resurface_after") or "")
        if after and after <= date.today().isoformat():
            return None
    return entry


def unresolved(workspace: Path, findings: list[dict]) -> list[dict]:
    log = read_log(workspace)
    return [f for f in findings if resolution_for(workspace, f, log) is None]


def prune(workspace: Path, findings: list[dict]) -> int:
    """Drop resolutions for findings that no longer exist. Returns how many went.

    Without this the log would accumulate a row for every disagreement the two
    plans ever had - the same unbounded growth that killed the approval queue.
    """
    log = read_log(workspace)
    resolutions = log.get("resolutions", {})
    if not resolutions:
        return 0
    live = {str(f.get("id")) for f in findings}
    stale = [key for key in resolutions if key not in live]
    for key in stale:
        del resolutions[key]
    if stale:
        write_log(workspace, log)
    return len(stale)


def summarize(workspace: Path) -> dict[str, int]:
    counts = {ACCEPTED: 0, DECLINED: 0, DEFERRED: 0}
    for entry in read_log(workspace).get("resolutions", {}).values():
        decision = str(entry.get("decision", ""))
        if decision in counts:
            counts[decision] += 1
    return counts
