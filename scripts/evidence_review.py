#!/usr/bin/env python3
"""When a recorded claim stops being trustworthy, which is not when its file changes.

`EVIDENCE_LOG.md` is the one file with no settlement mechanism that works. Compaction
is liveness-gated - an entry cited by open work stays whole - and on a real workspace
126 of 143 entries were cited, so 196,051 chars were effectively incompressible. It
grew from 63 to 143 entries in a single planning session.

Compaction cannot settle it because it answers the wrong question. "Is this evidence
still referenced?" is not "is this evidence still true." A market fact from July is
cited by the live plan *and* possibly false; nothing in the harness could say so,
because every other staleness check keys on file content - and the file has not
changed, the world has.

So evidence gets a second axis: an **epistemic** validity window, deliberately kept
separate from the mechanical content-hash freshness in `freshness.py`. A claim past
its window is not deleted and not disproved - it becomes "uncertain, pending
re-check", which forces a look instead of silent reliance.

Windows come from the strength of the evidence, which these entries already record.
The tiering follows arXiv:2607.26191 (evaluation results as perishable knowledge
claims - crowd/LLM judgement valid for weeks, controlled study for months, formal
property indefinitely) and the 53-day average evidence validity window measured over
62 real architectural decisions in arXiv:2601.21116, where 23% had gone stale within
two months and 86% of that was found reactively, during an incident.

Deliberately not implemented: a numeric reliability score. The source paper builds one
from unjustified constants, and a made-up number gets treated as meaningful. A date
and a reason are honest; 0.73 is not.
"""

from __future__ import annotations

import argparse
import re
from datetime import date, datetime, timedelta
from pathlib import Path

EVIDENCE_FILE = "EVIDENCE_LOG.md"

# Days a claim of this kind stays trustworthy without a re-check. A regulation is not
# a market observation; treating them alike is what makes any single window wrong.
WINDOWS = {
    "regulatory": 365,
    "verified_fact": 180,
    "expert_evidence": 180,
    "customer_evidence": 90,
    "market_observation": 90,
    "assumption": 30,
}
DEFAULT_WINDOW = 120

# A low-confidence claim decays faster than a high-confidence one of the same kind.
CONFIDENCE_FACTOR = {"high": 1.0, "medium-high": 0.75, "medium": 0.5, "low": 0.25}

# Already dismissed - re-checking a rejected claim is not work.
TERMINAL_TYPES = {"rejected", "superseded", "withdrawn"}

HEADING = re.compile(r"^(?P<hashes>#{2,4})\s+(?P<id>E-[A-Z0-9-]*\d+)\s*[:.]?\s*(?P<title>.*)$")
FIELD = re.compile(r"^[-*]\s+\*\*(?P<key>[^:*]+):?\*\*:?\s*(?P<value>.*)$")
DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
CONFIDENCE_INLINE = re.compile(r"(?i)confidence:?\*{0,2}:?\s*([a-z-]+)")


def evidence_file(workspace: Path) -> Path:
    return workspace / EVIDENCE_FILE


def _clean(value: str) -> str:
    return re.sub(r"[*`]", "", str(value)).strip().lower()


def parse(workspace: Path) -> list[dict]:
    """Every evidence entry with the fields that determine its shelf life."""
    path = evidence_file(workspace)
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    entries: list[dict] = []
    current: dict | None = None
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()

        heading = HEADING.match(stripped)
        if heading:
            current = {
                "id": heading.group("id"),
                "title": heading.group("title").strip(),
                "line": number,
                "type": "",
                "confidence": "",
                "checked": "",
                "review_after": "",
            }
            entries.append(current)
            continue
        if current is None:
            continue

        field = FIELD.match(stripped)
        if field:
            key, value = _clean(field.group("key")), field.group("value")
            if key == "type" and not current["type"]:
                tokens = _clean(value).split()
                current["type"] = tokens[0] if tokens else ""
            elif key.startswith("date") and not current["checked"]:
                match = DATE.search(value)
                if match:
                    current["checked"] = match.group(1)
            elif key.startswith("review after") and not current["review_after"]:
                match = DATE.search(value)
                if match:
                    current["review_after"] = match.group(1)

        # Real entries put both on one line: `Date checked: ... - **Confidence:** high`.
        if not current["confidence"] and "confidence" in stripped.lower():
            inline = CONFIDENCE_INLINE.search(stripped)
            if inline:
                current["confidence"] = inline.group(1).lower()

    return entries


def window_days(entry: dict) -> int:
    base = WINDOWS.get(entry.get("type", ""), DEFAULT_WINDOW)
    factor = CONFIDENCE_FACTOR.get(entry.get("confidence", ""), 1.0)
    return max(int(base * factor), 14)


def due_date(entry: dict) -> str | None:
    """When this claim should be looked at again, or None if it cannot expire."""
    if entry.get("type") in TERMINAL_TYPES:
        return None
    if entry.get("review_after"):
        return entry["review_after"]
    checked = entry.get("checked")
    if not checked:
        return None  # undated: no honest way to decay it, so do not pretend to
    try:
        stamp = datetime.strptime(checked, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (stamp + timedelta(days=window_days(entry))).isoformat()


def review_due(workspace: Path, *, today: str | None = None) -> list[dict]:
    """Entries whose window has closed. Uncertain, not disproved."""
    now = today or date.today().isoformat()
    out = []
    for entry in parse(workspace):
        due = due_date(entry)
        if due and due <= now:
            out.append(dict(entry, due=due, window=window_days(entry)))
    return sorted(out, key=lambda item: item["due"])


def undated(workspace: Path) -> list[dict]:
    """Entries with no `Date checked`, for which no window can be computed."""
    return [e for e in parse(workspace) if not e.get("checked") and e.get("type") not in TERMINAL_TYPES]


def summarize(workspace: Path, *, today: str | None = None) -> dict:
    entries = parse(workspace)
    return {
        "total": len(entries),
        "due": len(review_due(workspace, today=today)),
        "undated": len(undated(workspace)),
        "terminal": sum(1 for e in entries if e.get("type") in TERMINAL_TYPES),
    }


def describe(workspace: Path, *, today: str | None = None, verbose: bool = False) -> str:
    counts = summarize(workspace, today=today)
    if not counts["total"]:
        return "No evidence entries recorded."

    lines = [
        f"{counts['total']} evidence entr(ies): {counts['due']} due for re-check, "
        f"{counts['undated']} undated, {counts['terminal']} terminal."
    ]

    due = review_due(workspace, today=today)
    if due:
        lines.extend(["", "Past their validity window - uncertain, not disproved:"])
        for entry in due:
            kind = entry.get("type") or "untyped"
            confidence = entry.get("confidence") or "no confidence"
            lines.append(f"  {entry['id']}  due {entry['due']}  ({kind}/{confidence}, {entry['window']}d window)")
            lines.append(f"      {entry['title'][:88]}")
        lines.extend(
            [
                "",
                "Re-check it, or record a fresh `- **Date checked:**`. Nothing is deleted -",
                "a claim past its window still supports whatever cited it, it just stops",
                "counting as current until someone looks.",
            ]
        )

    if counts["undated"] and verbose:
        lines.extend(["", "No `Date checked` - shelf life cannot be computed:"])
        for entry in undated(workspace):
            lines.append(f"  {entry['id']}  {entry['title'][:80]}")

    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="Evidence past its validity window.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--verbose", action="store_true", help="Include undated entries.")
    parser.add_argument("--today", default=None, help="Evaluate as of this date (YYYY-MM-DD).")
    args = parser.parse_args()

    print(describe(resolve_workspace(args.workspace), today=args.today, verbose=args.verbose))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
