"""What a sub-product has already seen of its parent's plan.

The hierarchy checks in `hierarchy_drift` compare *current* parent values against
*current* sub-product values, so they can only report a contradiction between two
keys that both sides already carry. They are structurally unable to answer the
question an in-development sub-product actually needs answered: **what changed in
the master plan since I last looked?** A new platform-level constraint the
sub-product never considered produces no contradiction, so nothing is reported and
the sub-product keeps building against a stale contract.

This module adds the missing memory. Each sub-product stores a watermark - the
parent surface as it stood when that sub-product last synced - and the diff
against it becomes a finding.

    <sub-product>/.loop/parent-sync.json
    { "<parent key>": { "taken_at": ..., "surfaces": {...} } }

Keyed by parent, so re-linking a sub-product to a different main product starts a
fresh baseline instead of diffing against the previous parent's decisions. One
machine can hold many main products, and a main product many sub-products; nothing
here is global, and a middle node in a deeper tree keeps its own watermark for its
own parent while acting as a parent to its children.

Who moves the watermark matters. The parent computes the diff (it is the side that
runs `check_children`) but never advances it - if it did, a change would be
reported once into a queue and then forgotten. The sub-product advances its own
watermark when it next runs `loop session-start`, which is the moment it has
actually read the refreshed `plan/PARENT_CONTEXT.md`. Until then the diff keeps
reporting.

A sub-product with no watermark yet is baselined silently. Otherwise every
existing sub-product would wake up to a finding for every decision its parent has
ever recorded.

Rules first, AI second (AGENTS.md non-negotiable #4): everything here is parsed
from structured plan files.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

WATERMARK_FILE = ".loop/parent-sync.json"

SURFACE_DEPLOYMENT = "deployment"
SURFACE_DECISIONS = "decisions"
SURFACE_MAP_ROW = "map-row"
SURFACE_CONTRACTS = "contracts"

# Human-facing names for the surfaces, used in findings.
SURFACE_LABELS = {
    SURFACE_DEPLOYMENT: "Deployment & Infrastructure",
    SURFACE_DECISIONS: "DECISIONS.md",
    SURFACE_MAP_ROW: "PRODUCT_MAP row",
    SURFACE_CONTRACTS: "integration contracts",
}

CHANGE_ADDED = "added"
CHANGE_CHANGED = "changed"
CHANGE_REMOVED = "removed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parent_key(parent_ws: Path) -> str:
    """Stable identity for a parent workspace, independent of how it was reached."""
    return sha256(str(Path(parent_ws).resolve()).lower().encode("utf-8")).hexdigest()[:16]


# A watermark only has to *detect* change, so it stores a digest per key rather than
# the value. Storing whole values made it grow with the parent's decision log - 9,069
# chars for 28 decisions on the workspace this was built against, per parent, rewritten
# every session. The excerpt is what a change message quotes, and is bounded.
EXCERPT_LIMIT = 160


def _entry(label: str, value: str) -> dict[str, str]:
    import hierarchy_drift as drift

    normalized = drift.normalize_value(value)
    return {
        "label": label,
        "digest": sha256(normalized.encode("utf-8")).hexdigest()[:12],
        "excerpt": value[:EXCERPT_LIMIT],
    }


def _digest_of(entry: dict) -> str:
    """Digest for comparison, recomputed for watermarks written before this format."""
    import hierarchy_drift as drift

    if entry.get("digest"):
        return str(entry["digest"])
    normalized = drift.normalize_value(str(entry.get("value", "")))
    return sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _text_of(entry: dict) -> str:
    return str(entry.get("excerpt") or entry.get("value") or "")


def snapshot(parent_ws: Path, *, map_id: str | None = None) -> dict:
    """The parent surface a sub-product is bound by, as key -> digest + excerpt."""
    import hierarchy_drift as drift

    surfaces: dict[str, dict[str, dict[str, str]]] = {
        SURFACE_DEPLOYMENT: {
            key: _entry(label, value) for key, (label, value) in drift.deployment_labels(parent_ws).items()
        },
        SURFACE_DECISIONS: {
            key: _entry(label, value) for key, (label, value) in drift.decisions_labels(parent_ws).items()
        },
        SURFACE_MAP_ROW: {},
        SURFACE_CONTRACTS: {},
    }

    row = _map_row(parent_ws, map_id)
    if row:
        for field in ("title", "type", "depends"):
            value = str(row.get(field, "")).strip()
            if value:
                surfaces[SURFACE_MAP_ROW][field] = _entry(field, value)
        for name in _counterparts(parent_ws, row):
            surfaces[SURFACE_CONTRACTS][drift.normalize_key(name)] = _entry(name, "required")

    return {"parent": str(Path(parent_ws).resolve()), "taken_at": _now(), "surfaces": surfaces}


def _map_row(parent_ws: Path, map_id: str | None) -> dict | None:
    if not map_id:
        return None
    try:
        from ultraplan_harness import parse_product_map
    except ImportError:
        return None
    for row in parse_product_map(parent_ws):
        if row.get("id") == map_id:
            return row
    return None


def _counterparts(parent_ws: Path, row: dict) -> list[str]:
    """Other map rows *declared* by this row's integration spec.

    Was a substring scan of the spec's prose, which made this watermark surface flap
    whenever unrelated wording changed - and every flap produced a staged
    `parent-added` / `parent-removed` finding that interrupted the user.
    """
    try:
        import dependency_ledger as ledger_mod

        from plan_paths import find_step_folder
        from ultraplan_harness import parse_product_map
    except ImportError:
        return []

    folder = find_step_folder(parent_ws, str(row.get("id")))
    if folder is None:
        return []
    by_id, by_title = ledger_mod.index_rows(parse_product_map(parent_ws))
    declared = ledger_mod.parse_internal_apis(folder / "integrations.md", by_id, by_title)
    return [e["label"] for e in declared if e["id"] != str(row.get("id", ""))]


# ---------------------------------------------------------------------------
# storage
# ---------------------------------------------------------------------------


def _load(child_ws: Path) -> dict:
    path = Path(child_ws) / WATERMARK_FILE
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_watermark(child_ws: Path, parent_ws: Path) -> dict | None:
    entry = _load(child_ws).get(parent_key(parent_ws))
    return entry if isinstance(entry, dict) else None


def write_watermark(child_ws: Path, parent_ws: Path, snap: dict) -> Path:
    """Record that this sub-product has seen the parent as of `snap`."""
    path = Path(child_ws) / WATERMARK_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _load(child_ws)
    data[parent_key(parent_ws)] = snap
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def sync(child_ws: Path, parent_ws: Path, *, map_id: str | None = None) -> Path:
    """Advance this sub-product's watermark to the parent's current state."""
    return write_watermark(child_ws, parent_ws, snapshot(parent_ws, map_id=map_id))


# ---------------------------------------------------------------------------
# diff
# ---------------------------------------------------------------------------


def diff(previous: dict | None, current: dict) -> list[dict]:
    """Per-key changes between two snapshots, newest state last.

    Returns [] when there is no baseline: without one, every parent decision would
    read as new.
    """
    if not previous:
        return []

    changes: list[dict] = []
    prev_surfaces = previous.get("surfaces") or {}
    curr_surfaces = current.get("surfaces") or {}

    for surface in (SURFACE_DEPLOYMENT, SURFACE_DECISIONS, SURFACE_MAP_ROW, SURFACE_CONTRACTS):
        before = prev_surfaces.get(surface) or {}
        after = curr_surfaces.get(surface) or {}
        for key in sorted(set(before) | set(after)):
            prev_entry, curr_entry = before.get(key) or {}, after.get(key) or {}
            old, new = _text_of(prev_entry), _text_of(curr_entry)
            label = (curr_entry or prev_entry).get("label", key)
            if key not in before:
                changes.append(_change(surface, key, label, CHANGE_ADDED, "", new))
            elif key not in after:
                changes.append(_change(surface, key, label, CHANGE_REMOVED, old, ""))
            elif _digest_of(prev_entry) != _digest_of(curr_entry):
                changes.append(_change(surface, key, label, CHANGE_CHANGED, old, new))
    return changes


def _change(surface: str, key: str, label: str, kind: str, before: str, after: str) -> dict:
    return {
        "surface": surface,
        "surface_label": SURFACE_LABELS.get(surface, surface),
        "key": key,
        "label": label,
        "change": kind,
        "before": before,
        "after": after,
    }


def describe(change: dict) -> str:
    """One line a human can act on, with both values when both exist."""
    where = change["surface_label"]
    label = change["label"]
    if change["change"] == CHANGE_ADDED:
        return f"{where}: **{label}** is new at platform level - now **{change['after']}**."
    if change["change"] == CHANGE_REMOVED:
        return f"{where}: **{label}** was removed at platform level (was **{change['before']}**)."
    return f"{where}: **{label}** changed at platform level - **{change['before']}** -> **{change['after']}**."


# ---------------------------------------------------------------------------
# how urgent is this for the sub-product
# ---------------------------------------------------------------------------


def has_work_in_flight(child_ws: Path) -> bool:
    """True when this sub-product has a task actually in progress.

    A platform change that lands mid-build can invalidate work already underway,
    so it is treated as an error rather than a warning. Parsed, not inferred.
    """
    path = Path(child_ws) / "TASKS.yml"
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    for raw in text.splitlines():
        line = raw.strip().lower().replace("-", "_")
        if line.startswith("status:") and line.split(":", 1)[1].strip().strip("\"'") in ("in_progress", "doing", "active"):
            return True
    return False
