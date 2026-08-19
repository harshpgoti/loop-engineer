#!/usr/bin/env python3
"""One parser for DOUBTS.md, so every command agrees what is open.

Before this, four call sites each scraped the file with their own regex and their
own truncation budget. On this repo's own sub-product they disagreed badly:

    plan_phase       "open doubts exist"   (bool, substring `status: open`)
    /status          3                     (regex over the first 3,000 chars)
    /product-tree    17                    (same regex, 20,000 chars)
    prod_gap         P1 blocker            (the bare word "open" anywhere)
    truth            13 entries, ~9 live

`prod_gap`'s test was the worst: the `## Open Doubts` *heading* contains the word,
so a fully resolved file still raised a launch blocker, which appended a note, which
made the file longer - three identical blocks are sitting in the real file now.

So: one parser, no truncation, an explicit status vocabulary, and a blocking flag
that is *recorded* rather than re-guessed by a model every session.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

OPEN = "open"
RESOLVED = "resolved"
DEFERRED = "deferred"
STATUSES = (OPEN, RESOLVED, DEFERRED)

HEADING = re.compile(r"^#{2,4}\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\s*[:.]\s*(?P<title>.+?)\s*$")
FIELD = re.compile(r"^[-*]\s+\*\*(?P<key>[^:*]+):?\*\*:?\s*(?P<value>.*)$")
SECTION = re.compile(r"^##\s+(?P<name>.+?)\s*$")

# Phrases that settle whether an open doubt blocks development. Checked against the
# whole entry, because real entries put this in the status parenthetical
# ("open (commercial - does not block the build)") rather than in a field.
NON_BLOCKING = (
    "does not block",
    "doesn't block",
    "non-blocking",
    "not blocking",
    "nice to have",
    "commercial only",
)
BLOCKING = ("blocks ", "blocker", "p0", "before build", "blocking")


@dataclass
class Doubt:
    id: str
    title: str
    status: str
    blocking: bool
    section: str
    question: str = ""
    why: str = ""
    default: str = ""
    note: str = ""
    line: int = 0
    superseded_by: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def is_open(self) -> bool:
        return self.status == OPEN

    def suggestion(self) -> tuple[str, str]:
        """The recommended answer and where it came from.

        `Default if unavailable` is already the house format for "what to do when
        nobody answers" (`templates/starter/DOUBTS.md`), so it is the suggestion -
        deterministic, authored by whoever raised the doubt, never model-invented.
        """
        if self.default:
            return (self.default, "the doubt's own **Default if unavailable**")
        if not self.blocking:
            return ("Defer it", "nothing marks this as blocking development")
        return ("", "no default was recorded - this one needs a real answer")


def doubts_file(workspace: Path) -> Path:
    return workspace / "DOUBTS.md"


# ---------------------------------------------------------------------------
# supersession - a decision can retire a question instead of answering it
# ---------------------------------------------------------------------------

SUPERSEDES = re.compile(r"^[-*]\s+\*\*Supersedes:?\*\*:?\s*(?P<ids>.+)$", re.I)
DECISION_HEADING = re.compile(r"^#{2,4}\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\s*[:.]\s*(?P<title>.+?)\s*$")
ID_IN_TEXT = re.compile(r"\b([A-Z]{1,4}(?:-[A-Z]+)*-\d+)\b")


def _supersessions_in(path: Path) -> dict[str, str]:
    """`doubt id -> decision id` from one DECISIONS.md.

    Read from `- **Supersedes:** DQ-007, DQ-020` under a decision heading. Some
    decisions do not answer a question - they remove the reason it was ever asked,
    and there was no way to say so where code could see it.
    """
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {}

    found: dict[str, str] = {}
    decision = ""
    for line in text.splitlines():
        stripped = line.strip()
        heading = DECISION_HEADING.match(stripped)
        if heading:
            decision = heading.group("id")
            continue
        match = SUPERSEDES.match(stripped)
        if not match or not decision:
            continue
        for doubt_id in ID_IN_TEXT.findall(match.group("ids")):
            found.setdefault(doubt_id.upper(), decision)
    return found


def _parent_decisions(workspace: Path) -> Path | None:
    """The parent product's DECISIONS.md, when this workspace is a sub-product."""
    try:
        from workspace_tree import data_dir_for, product_folder, read_meta

        folder = product_folder(workspace)
        stored = read_meta(workspace).get("parent")
        if folder is None or not stored:
            return None
        parent_folder = (folder / str(stored)).resolve()
        if not parent_folder.is_dir():
            return None
        return data_dir_for(parent_folder) / "DECISIONS.md"
    except Exception:
        return None


def supersessions(workspace: Path) -> dict[str, str]:
    """Every decision that retires a doubt in *this* workspace.

    Sources: this workspace's own decisions, and its parent product's. The
    direction is one-way by construction - a workspace only ever applies these to
    its own DOUBTS.md, so a sub-product can never close a question in its parent.

    Derived, never written: delete the `Supersedes:` line and the doubt reopens.
    """
    found = _supersessions_in(doubts_file(workspace).parent / "DECISIONS.md")
    parent = _parent_decisions(workspace)
    if parent is not None:
        for doubt_id, decision in _supersessions_in(parent).items():
            found.setdefault(doubt_id, f"{decision} (parent product)")
    return found


def _status_of(raw: str) -> tuple[str, str]:
    """First word of a status value wins; the rest is kept as a qualifier.

    Real values look like `open (P0 for pilot - PR-040)` or
    `deferred / not required by current architecture (2026-07-12)`.
    """
    cleaned = raw.strip().strip("*_` ").lower()
    for status in STATUSES:
        if cleaned.startswith(status):
            return status, raw.strip()
    return (OPEN if cleaned else ""), raw.strip()


def _blocking_from(text: str, status: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in NON_BLOCKING):
        return False
    if any(token in lowered for token in BLOCKING):
        return True
    # An open doubt with nothing said either way is treated as blocking: the
    # cautious default, and the one the user can always downgrade explicitly.
    return status == OPEN


def parse(workspace: Path) -> list[Doubt]:
    """Every entry in DOUBTS.md. Reads the whole file - never truncates."""
    path = doubts_file(workspace)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    entries: list[Doubt] = []
    section = ""
    current: Doubt | None = None
    body: list[str] = []

    def close() -> None:
        if current is None:
            return
        blob = "\n".join(body)
        declared = current.blocking_raw  # type: ignore[attr-defined]
        if declared:
            # An explicit `- **Blocking:** yes|no` is the author's call and outranks
            # any phrase found in the prose.
            current.blocking = declared.strip().lower().startswith(("y", "true"))
        else:
            current.blocking = _blocking_from(blob + " " + current.status_raw, current.status)  # type: ignore[attr-defined]
        _finalize(current, blob)
        entries.append(current)

    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        section_match = SECTION.match(stripped)
        if section_match and not HEADING.match(stripped):
            close()
            current, body = None, []
            section = section_match.group("name")
            continue

        heading = HEADING.match(stripped)
        if heading:
            close()
            body = []
            current = Doubt(
                id=heading.group("id"),
                title=heading.group("title"),
                status="",
                blocking=False,
                section=section,
                line=number,
            )
            current.status_raw = ""  # type: ignore[attr-defined]
            current.blocking_raw = ""  # type: ignore[attr-defined]
            continue

        if current is None:
            continue
        body.append(stripped)

        field_match = FIELD.match(stripped)
        if not field_match:
            continue
        key = field_match.group("key").strip().lower()
        value = field_match.group("value").strip()
        if key == "status":
            current.status, current.status_raw = _status_of(value)  # type: ignore[attr-defined]
        elif key == "blocking":
            current.blocking_raw = value  # type: ignore[attr-defined]
        elif key == "question":
            current.question = value
        elif key.startswith("why"):
            current.why = value
        elif key.startswith("default"):
            current.default = value
        elif key.startswith("resolution") or key.startswith("resolved"):
            current.note = value

    close()
    _apply_supersessions(workspace, entries)
    return entries


def _apply_supersessions(workspace: Path, entries: list[Doubt]) -> None:
    """Close questions a decision has retired. Applied at read time, not written.

    Keeping it derived is what makes it reversible: if the decision is withdrawn,
    the `Supersedes:` line goes with it and the doubt is open again on the next read.
    """
    try:
        retired = supersessions(workspace)
    except Exception:
        return
    if not retired:
        return
    for entry in entries:
        decision = retired.get(entry.id.upper())
        if not decision or entry.status == RESOLVED:
            continue
        entry.superseded_by = decision
        entry.status = RESOLVED
        entry.blocking = False
        entry.note = entry.note or f"Superseded by {decision} - the question no longer applies."


def _finalize(doubt: Doubt, blob: str) -> None:
    """Settle status from every signal, and record contradictions instead of hiding them."""
    heading_resolved = "resolved" in doubt.title.lower()
    section_resolved = "resolved" in doubt.section.lower() or "superseded" in doubt.section.lower()
    has_resolution = bool(doubt.note) or bool(re.search(r"\*\*resolv", blob, re.I))

    if not doubt.status:
        # No Status field at all - fall back to the heading, then the section.
        doubt.status = RESOLVED if (heading_resolved or section_resolved) else OPEN
        doubt.issues.append("no **Status:** field - inferred from heading/section")
        return

    if doubt.status == OPEN and (heading_resolved or has_resolution):
        doubt.issues.append("marked open but carries a resolution - status is the one to trust, fix it")
    if doubt.status == OPEN and section_resolved:
        doubt.issues.append(f"marked open but filed under '{doubt.section}'")
    if doubt.status == RESOLVED and not has_resolution:
        doubt.issues.append("marked resolved with no recorded answer")


def open_doubts(workspace: Path) -> list[Doubt]:
    return [d for d in parse(workspace) if d.is_open]


def blocking_doubts(workspace: Path) -> list[Doubt]:
    return [d for d in open_doubts(workspace) if d.blocking]


def counts(workspace: Path) -> dict[str, int]:
    entries = parse(workspace)
    result = {status: 0 for status in STATUSES}
    for item in entries:
        result[item.status] = result.get(item.status, 0) + 1
    result["total"] = len(entries)
    result["blocking"] = sum(1 for d in entries if d.is_open and d.blocking)
    result["issues"] = sum(1 for d in entries if d.issues)
    result["superseded"] = sum(1 for d in entries if d.superseded_by)
    return result


def has_blocking(workspace: Path) -> bool:
    """The routing signal: only a *blocking* open doubt should hold up task compile.

    The old test fired on any open item, so one non-blocking commercial question
    pinned a workspace before `task-compiler` indefinitely.
    """
    return bool(blocking_doubts(workspace))


# ---------------------------------------------------------------------------
# writing - deterministic, so a resolution is a state change and not a narration
# ---------------------------------------------------------------------------


def set_status(
    workspace: Path,
    doubt_id: str,
    status: str,
    *,
    answer: str = "",
    decision_ref: str = "",
) -> bool:
    """Rewrite one entry's status in place, recording the answer with it.

    Nothing in the harness used to write this - the model was told to "mark it
    resolved" with no format, and the real file grew four incompatible encodings.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status} (expected one of {', '.join(STATUSES)})")

    path = doubts_file(workspace)
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()

    start = None
    for index, line in enumerate(lines):
        heading = HEADING.match(line.strip())
        if heading and heading.group("id").lower() == doubt_id.lower():
            start = index
            break
    if start is None:
        return False

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].strip().startswith("#"):
            end = index
            break

    stamp = date.today().isoformat()
    replaced = False
    for index in range(start + 1, end):
        field_match = FIELD.match(lines[index].strip())
        if field_match and field_match.group("key").strip().lower() == "status":
            lines[index] = f"- **Status:** {status}"
            replaced = True
            break
    if not replaced:
        lines.insert(start + 1, f"- **Status:** {status}")
        end += 1

    if answer or decision_ref:
        label = "Resolution" if status == RESOLVED else "Deferral"
        body = answer.strip()
        if decision_ref:
            body = f"{body} → `{decision_ref}`" if body else f"See `{decision_ref}`"
        lines.insert(end, f"- **{label} ({stamp}):** {body}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def resolve(workspace: Path, doubt_id: str, answer: str, *, decision_ref: str = "") -> bool:
    return set_status(workspace, doubt_id, RESOLVED, answer=answer, decision_ref=decision_ref)


def defer(workspace: Path, doubt_id: str, reason: str) -> bool:
    return set_status(workspace, doubt_id, DEFERRED, answer=reason)


def next_id(workspace: Path, prefix: str = "DQ") -> str:
    numbers = [
        int(match.group(1))
        for d in parse(workspace)
        if (match := re.search(r"(\d+)$", d.id)) and d.id.upper().startswith(prefix.upper())
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def add(
    workspace: Path,
    *,
    title: str,
    question: str,
    why: str = "",
    default: str = "",
    blocking: bool = True,
    doubt_id: str | None = None,
    prefix: str = "DQ",
) -> str | None:
    """Append a schema-shaped doubt. Returns None when an identical one exists."""
    existing = parse(workspace)
    for item in existing:
        if item.question and item.question.strip().lower() == question.strip().lower():
            return None
        if doubt_id and item.id.lower() == doubt_id.lower():
            return None

    identifier = doubt_id or next_id(workspace, prefix)
    entry = [
        "",
        f"### {identifier}: {title}",
        f"- **Status:** {OPEN}",
        f"- **Blocking:** {'yes' if blocking else 'no'}",
        f"- **Question:** {question}",
    ]
    if why:
        entry.append(f"- **Why it matters:** {why}")
    if default:
        entry.append(f"- **Default if unavailable:** {default}")

    path = doubts_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else "# Doubts\n"
    path.write_text(existing_text.rstrip() + "\n" + "\n".join(entry) + "\n", encoding="utf-8")
    return identifier


def question(doubt: Doubt) -> dict:
    """One doubt rendered as a question with a recommended answer."""
    recommended, source = doubt.suggestion()
    return {
        "id": doubt.id,
        "question": doubt.question or doubt.title,
        "why": doubt.why,
        "blocking": doubt.blocking,
        "recommended": recommended,
        "recommended_source": source,
        "options": ["answer it", "accept the default", "defer it"],
    }


def describe(workspace: Path, *, verbose: bool = False) -> str:
    entries = parse(workspace)
    if not entries:
        return "No doubts recorded."
    tally = counts(workspace)
    lines = [
        f"{tally['total']} doubt(s): {tally[OPEN]} open ({tally['blocking']} blocking), "
        f"{tally[RESOLVED]} resolved, {tally[DEFERRED]} deferred",
        "",
    ]
    for item in entries:
        if item.status != OPEN and not (verbose or item.superseded_by):
            continue
        flag = "BLOCKING" if item.blocking else "non-blocking"
        lines.append(f"  [{item.status}/{flag}] {item.id}: {item.title}")
        if item.superseded_by:
            lines.append(f"      superseded by {item.superseded_by} - not asked")
        if verbose and item.question:
            lines.append(f"      Q: {item.question}")
        for issue in item.issues:
            lines.append(f"      ! {issue}")
    if tally["issues"]:
        lines.append("")
        lines.append(f"{tally['issues']} entry(ies) have inconsistent status - run `loop doubts lint`.")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import resolve_workspace

    parser = argparse.ArgumentParser(description="Read and update DOUBTS.md deterministically.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")

    listing = sub.add_parser("list", help="Open doubts and their status.")
    listing.add_argument("--verbose", action="store_true")

    sub.add_parser("ask", help="Open blocking doubts as questions with recommended answers.")
    sub.add_parser("lint", help="Entries whose status contradicts their content.")
    sub.add_parser("counts", help="One authoritative count for every command to use.")

    resolve_p = sub.add_parser("resolve", help="Mark a doubt resolved, recording the answer.")
    resolve_p.add_argument("doubt_id")
    resolve_p.add_argument("answer")
    resolve_p.add_argument("--decision", default="", help="DECISIONS.md id to cross-link, e.g. D-014")

    defer_p = sub.add_parser("defer", help="Mark a doubt deferred, recording why.")
    defer_p.add_argument("doubt_id")
    defer_p.add_argument("reason")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    cmd = args.cmd or "list"

    if cmd == "resolve":
        ok = resolve(workspace, args.doubt_id, args.answer, decision_ref=args.decision)
        print(f"{args.doubt_id}: resolved" if ok else f"No doubt with id {args.doubt_id!r}")
        return 0 if ok else 1

    if cmd == "defer":
        ok = defer(workspace, args.doubt_id, args.reason)
        print(f"{args.doubt_id}: deferred" if ok else f"No doubt with id {args.doubt_id!r}")
        return 0 if ok else 1

    if cmd == "counts":
        for key, value in counts(workspace).items():
            print(f"{key}\t{value}")
        return 0

    if cmd == "lint":
        bad = [d for d in parse(workspace) if d.issues]
        if not bad:
            print("Every entry's status matches its content.")
            return 0
        for item in bad:
            print(f"{item.id} (line {item.line}): {item.title}")
            for issue in item.issues:
                print(f"  - {issue}")
        return 0

    if cmd == "ask":
        blocking = blocking_doubts(workspace)
        if not blocking:
            print("No blocking doubts. Development is not held up by open questions.")
            return 0
        for index, item in enumerate(blocking, start=1):
            q = question(item)
            print(f"[{index}/{len(blocking)}] {q['id']}: {q['question']}")
            if q["why"]:
                print(f"  Why it matters: {q['why']}")
            if q["recommended"]:
                print(f"  Recommended: {q['recommended']}")
                print(f"  (from {q['recommended_source']})")
            else:
                print("  No recorded default - this needs a real answer.")
            print()
        return 0

    print(describe(workspace, verbose=getattr(args, "verbose", False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
