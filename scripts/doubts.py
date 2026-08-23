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

# `Ask:` names who holds the answer. These mean "the person running the loop", so the
# question is asked in-session; anything else is a question for someone who is not here,
# and goes out as a questionnaire instead of blocking the build until they wander past.
SELF_WORDS = {"user", "you", "me", "self", "owner", "founder", "the user", "us", "team"}


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
    depends_on: list[str] = field(default_factory=list)
    ask: str = ""
    issues: list[str] = field(default_factory=list)

    @property
    def owner(self) -> str:
        """Who holds the answer. Absent an `Ask:` field, the user does."""
        return self.ask.strip() or "user"

    @property
    def delegated(self) -> bool:
        """Whether somebody other than the user has to answer this."""
        return self.owner.strip().lower().rstrip(".") not in SELF_WORDS

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
        elif key.startswith(("depends", "blocked by", "after")):
            current.depends_on = [m.upper() for m in ID_IN_TEXT.findall(value.upper())]
        elif key == "ask" or key.startswith("ask "):
            current.ask = value
        elif key.startswith(("resolution", "resolved", "answer", "deferral")):
            # `answer` is what `state_archive` leaves behind when it compacts a
            # resolved entry - the rationale moves to plan/archive/, this stays.
            current.note = value

    close()
    _apply_supersessions(workspace, entries)
    _check_dependencies(entries)
    return entries


def _check_dependencies(entries: list[Doubt]) -> None:
    """Bad `Depends on:` references, reported rather than silently obeyed."""
    known = {d.id for d in entries}
    for item in entries:
        for ref in item.depends_on:
            if ref == item.id:
                item.issues.append("depends on itself")
            elif ref not in known:
                item.issues.append(f"depends on {ref}, which is not a doubt in this file")
    # Prerequisites written in prose instead of in a field. The real ones look like
    # `Default if unavailable: Decide when DQ-005 resolves.` - an ordering the author
    # already knows and the frontier cannot see, so the question gets asked a round early.
    open_ids = {d.id for d in entries if d.is_open and not d.superseded_by}
    for item in entries:
        if not item.is_open:
            continue
        prose = " ".join((item.question, item.why, item.default, item.title))
        for ref in sorted(set(ID_IN_TEXT.findall(prose.upper()))):
            if ref != item.id and ref in open_ids and ref not in item.depends_on:
                item.issues.append(
                    f"names {ref} but does not declare it - add `- **Depends on:** {ref}` "
                    "if this cannot be answered until that one is"
                )

    for cycle in _cycles(entries):
        loop = " -> ".join(cycle + [cycle[0]])
        for node in cycle:
            for item in entries:
                if item.id == node:
                    item.issues.append(f"prerequisite loop: {loop} - all of them get asked together")


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
    has_resolution = bool(doubt.note) or bool(re.search(r"\*\*(resolv|answer|deferral)", blob, re.I))

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


# ---------------------------------------------------------------------------
# the frontier - which questions can honestly be asked right now
# ---------------------------------------------------------------------------
#
# Asking every blocking doubt at once asks the user to answer questions whose answers
# depend on answers they have not given yet. On this repo's own sub-product that meant
# 17 questions in one wall of text, several of them unanswerable until earlier ones
# landed. So a doubt may declare `- **Depends on:** DQ-003` and the frontier is what is
# left once you remove everything still waiting on an unsettled question.
#
# Settled means resolved, deferred, or superseded. A deferral is a decision ("go with
# the default for now"), so it unblocks whatever waited on it.


def _settled_ids(entries: list[Doubt]) -> set[str]:
    return {d.id for d in entries if d.status != OPEN or d.superseded_by}


def _cycles(entries: list[Doubt]) -> list[list[str]]:
    """Prerequisite loops, which would otherwise wait on each other forever."""
    by_id = {d.id: d for d in entries}
    open_ids = {d.id for d in entries if d.is_open and not d.superseded_by}
    found: list[list[str]] = []
    seen: set[str] = set()

    def walk(node: str, path: list[str]) -> None:
        if node in path:
            cycle = path[path.index(node):]
            key = tuple(sorted(cycle))
            if key not in seen:
                seen.add(key)
                found.append(cycle)
            return
        if node not in open_ids:
            return
        for nxt in by_id[node].depends_on:
            if nxt in by_id:
                walk(nxt, path + [node])

    for item in entries:
        if item.is_open and not item.superseded_by:
            walk(item.id, [])
    return found


def waiting_on(doubt: Doubt, entries: list[Doubt]) -> list[str]:
    """Prerequisites of this doubt that are still open.

    A prerequisite id nobody recognises counts as settled, not as an eternal block. A
    typo in a `Depends on:` line would otherwise delete the question from every round
    without saying a word - the exact kind of silent disappearance this harness keeps
    finding. `lint` reports it instead.
    """
    known = {d.id for d in entries}
    settled = _settled_ids(entries)
    return [ref for ref in doubt.depends_on if ref in known and ref not in settled and ref != doubt.id]


def frontier(workspace: Path) -> list[Doubt]:
    """The blocking questions whose prerequisites are settled and whose answer is the user's.

    Ask this whole list in one round. Nothing else can be answered honestly yet.
    """
    entries = parse(workspace)
    in_a_cycle = {node for cycle in _cycles(entries) for node in cycle}
    ready = []
    for item in entries:
        if not (item.is_open and item.blocking) or item.delegated:
            continue
        # A cycle has no honest ordering, so ask all of it rather than ask none of it.
        if item.id in in_a_cycle or not waiting_on(item, entries):
            ready.append(item)
    return ready


def blocked_behind(workspace: Path) -> list[tuple[Doubt, list[str]]]:
    """Blocking questions held back this round, and the doubts each is waiting on."""
    entries = parse(workspace)
    in_a_cycle = {node for cycle in _cycles(entries) for node in cycle}
    held = []
    for item in entries:
        if not (item.is_open and item.blocking) or item.delegated or item.id in in_a_cycle:
            continue
        waiting = waiting_on(item, entries)
        if waiting:
            held.append((item, waiting))
    return held


def delegated_doubts(workspace: Path) -> list[Doubt]:
    """Open questions somebody other than the user has to answer."""
    return [d for d in open_doubts(workspace) if d.delegated]


def rounds(workspace: Path) -> list[list[str]]:
    """Every remaining round, so a plan can say how many exchanges are left."""
    entries = [d for d in parse(workspace) if d.is_open and d.blocking and not d.delegated]
    known = {d.id for d in parse(workspace)}
    settled = _settled_ids(parse(workspace))
    remaining = {d.id: [r for r in d.depends_on if r in known and r not in settled and r != d.id] for d in entries}
    result: list[list[str]] = []
    while remaining:
        ready = sorted(i for i, deps in remaining.items() if not any(dep in remaining for dep in deps))
        if not ready:  # a cycle - the rest go out together
            result.append(sorted(remaining))
            break
        result.append(ready)
        for i in ready:
            remaining.pop(i)
    return result


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
    depends_on: list[str] | None = None,
    ask: str = "",
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
    if depends_on:
        entry.append(f"- **Depends on:** {', '.join(depends_on)}")
    if ask:
        entry.append(f"- **Ask:** {ask}")

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
        "owner": doubt.owner,
        "depends_on": list(doubt.depends_on),
    }


# ---------------------------------------------------------------------------
# questionnaires - questions the user cannot answer alone
# ---------------------------------------------------------------------------
#
# Some doubts are not the user's to settle: what the payer actually returns on a 835,
# which regulator owns a field, what the incumbent charges. Left in DOUBTS.md they block
# development until somebody happens to be in the room. Marked `- **Ask:** <who>` they
# leave the build's critical path and go out as a document that person fills in async.


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-") or "questionnaire"


def recipients(workspace: Path) -> dict[str, list[Doubt]]:
    """Open questions grouped by who has to answer them, blocking ones first."""
    grouped: dict[str, list[Doubt]] = {}
    for item in delegated_doubts(workspace):
        grouped.setdefault(item.owner, []).append(item)
    for items in grouped.values():
        items.sort(key=lambda d: (not d.blocking, d.id))
    return grouped


def questionnaire(workspace: Path, recipient: str, *, product: str = "") -> str:
    """One recipient's questions as a document they can fill in without you present."""
    items = recipients(workspace).get(recipient, [])
    product = product or workspace.parent.name if workspace.name == ".loop-engineer" else workspace.name
    lines = [
        f"# Questions for {recipient}",
        "",
        f"**From:** the {product} team &nbsp;&nbsp; **To:** {recipient}",
        "",
        "**Why this exists:** each question below is currently blocking a build decision. "
        "Your answer goes straight into the product's decision log, so please answer the ones "
        "you can and say so plainly on the ones you cannot.",
        "",
        "## How to answer",
        "",
        "- Write under each **Answer:** line. Partial answers are useful.",
        '- "I do not know" is a real answer - it tells us to go find it elsewhere rather than assume.',
        "- Where a **Our assumption if we do not hear back** line appears, that is what we will do. "
        "Correcting it is the highest-value thing you can do here.",
        "",
    ]
    if not items:
        lines += ["## Questions", "", "_No open questions are currently assigned to this recipient._", ""]
        return "\n".join(lines)

    blocking = [d for d in items if d.blocking]
    other = [d for d in items if not d.blocking]
    for heading, group in (("Blocking the build", blocking), ("Also useful", other)):
        if not group:
            continue
        lines += [f"## {heading}", ""]
        for item in group:
            lines.append(f"### {item.id}: {item.question or item.title}")
            if item.why:
                lines.append(f"_Why this matters: {item.why}_")
            lines.append("")
            if item.default:
                lines.append(f"**Our assumption if we do not hear back:** {item.default}")
                lines.append("")
            lines.append("**Answer:**")
            lines.append("")
            lines.append("")
    lines += [
        "## Anything else?",
        "",
        "Is there something we did not ask that we should know about?",
        "",
        "**Answer:**",
        "",
    ]
    return "\n".join(lines)


def write_questionnaire(workspace: Path, recipient: str) -> Path:
    """Write the recipient's questionnaire and return its path."""
    path = workspace / "plan" / "questionnaires" / f"{_slug(recipient)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(questionnaire(workspace, recipient) + "\n", encoding="utf-8")
    return path


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
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

    parser = argparse.ArgumentParser(description="Read and update DOUBTS.md deterministically.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")

    listing = sub.add_parser("list", help="Open doubts and their status.")
    listing.add_argument("--verbose", action="store_true")

    sub.add_parser("ask", help="This round of questions: the ones whose prerequisites are settled.")
    q_p = sub.add_parser("questionnaire", help="Write out questions somebody other than the user must answer.")
    q_p.add_argument("recipient", nargs="?", default="", help="One recipient; omit to write every recipient's doc.")
    sub.add_parser("lint", help="Entries whose status contradicts their content.")
    sub.add_parser("counts", help="One authoritative count for every command to use.")

    resolve_p = sub.add_parser("resolve", help="Mark a doubt resolved, recording the answer.")
    resolve_p.add_argument("doubt_id")
    resolve_p.add_argument("answer")
    resolve_p.add_argument("--decision", default="", help="DECISIONS.md id to cross-link, e.g. D-014")

    defer_p = sub.add_parser("defer", help="Mark a doubt deferred, recording why.")
    defer_p.add_argument("doubt_id")
    defer_p.add_argument("reason")

    add_p = sub.add_parser("add", help="Record a new question so the next session inherits it.")
    add_p.add_argument("title")
    add_p.add_argument("question")
    add_p.add_argument("--why", default="")
    add_p.add_argument("--default", dest="default_answer", default="", help="The recommended answer.")
    add_p.add_argument("--depends-on", default="", help="Comma-separated doubt ids that come first.")
    add_p.add_argument("--ask", default="", help="Who holds the answer, when it is not the user.")
    add_p.add_argument("--non-blocking", action="store_true")

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

    if cmd == "add":
        new_id = add(
            workspace,
            title=args.title,
            question=args.question,
            why=args.why,
            default=args.default_answer,
            blocking=not args.non_blocking,
            depends_on=[p.strip().upper() for p in args.depends_on.split(",") if p.strip()],
            ask=args.ask,
        )
        if new_id is None:
            print("A doubt with that question is already recorded - nothing added.")
            return 0
        print(f"{new_id}: recorded")
        return 0

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

    if cmd == "questionnaire":
        grouped = recipients(workspace)
        if not grouped:
            print("No open doubt names anybody but the user - nothing to send out.")
            print("Mark one with `- **Ask:** <who>` to move it off the build's critical path.")
            return 0
        wanted = [args.recipient] if args.recipient else sorted(grouped)
        for who in wanted:
            if who not in grouped:
                print(f"No open doubts assigned to {who!r}. Known: {', '.join(sorted(grouped))}")
                return 1
            path = write_questionnaire(workspace, who)
            ids = ", ".join(d.id for d in grouped[who])
            print(f"{who}: {len(grouped[who])} question(s) -> {path}")
            print(f"  covers {ids}")
            print("  answers come back with `loop doubts resolve <id> \"<answer>\"`")
        return 0

    if cmd == "ask":
        ready = frontier(workspace)
        held = blocked_behind(workspace)
        away = delegated_doubts(workspace)
        blocking = blocking_doubts(workspace)

        if not blocking:
            print("No blocking doubts. Development is not held up by open questions.")
            if away:
                print(f"{len(away)} question(s) are out with someone else - `loop doubts questionnaire`.")
            return 0

        if not ready:
            # Every blocking question is waiting on someone who is not here. Saying
            # "no questions" would read as "you are clear to build", which is a lie.
            print(f"{len(blocking)} blocking question(s), none of them the user's to answer.")
            for item in away:
                print(f"  {item.id} -> {item.owner}: {item.question or item.title}")
            print("Run `loop doubts questionnaire` to send them out.")
            return 0

        rounds_left = len(rounds(workspace))
        print(f"ROUND 1 of {rounds_left} - {len(ready)} question(s) answerable now.")
        if held:
            print(f"{len(held)} more open once these land. {len(away)} are out with someone else.")
        print()
        for index, item in enumerate(ready, start=1):
            q = question(item)
            print(f"Q{index}. {q['id']} - {q['question']}")
            if q["why"]:
                print(f"  Why it matters: {q['why']}")
            if q["recommended"]:
                print(f"  -> Recommended: {q['recommended']}")
                print(f"     (from {q['recommended_source']})")
            else:
                print("  -> No recorded default - this one needs a real answer.")
            print()
        if held:
            print("Held for a later round:")
            for item, waiting in held:
                print(f"  {item.id} waits on {', '.join(waiting)} - {item.title}")
            print()
        return 0

    print(describe(workspace, verbose=getattr(args, "verbose", False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
