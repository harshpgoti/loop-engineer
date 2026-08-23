#!/usr/bin/env python3
"""Shrink finished work in place, without letting the plan forget it happened.

About half of a mature `TASKS.yml` and `DOUBTS.md` is finished work - 24 of 38 tasks
and 9 of 20 doubts on the workspace this was built against. A planning session reads
both files whole, so it pays for that every time, and the share only grows.

The obvious fix - move completed entries into an archive file - breaks the plan in
exactly the way that produces re-work:

- `blocked_by: [TASK-024]` stops resolving once TASK-024 is gone
- `feature_converge` cross-references `tasks.md` ids against `TASKS.yml`
- `deployment_plan` dedupes by `doubt_id in doubts_text`, so an archived
  `DQ-DEP-*` gets **re-asked and re-appended**
- "reuse, don't re-ask" depends on a resolved doubt's answer being readable

So nothing is moved. Each finished entry is **compacted**: identity, outcome and
answer stay inline; the deliberation that produced them goes to `plan/archive/`.

    - id: TASK-020                    - id: TASK-020
      title: Capability registry        title: Capability registry
      phase: step02                     status: completed
      gate: G-AGENT-API-01      -->     gate: G-AGENT-API-01
      status: completed
      priority: P0
      acceptance:
        - app/agent/catalog.py ...
        - router_core enforces ...

The answer is small. The argument that produced it is large. Keep the answer.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ARCHIVE_DIR = "plan/archive"
TASKS_ARCHIVE = "plan/archive/TASKS_DONE.yml"
DOUBTS_ARCHIVE = "plan/archive/DOUBTS_RESOLVED.md"

# Below these, compaction is not worth the churn - a small workspace is left alone.
TASKS_BUDGET = 10_000
DOUBTS_BUDGET = 8_000

# The most recently finished entries stay in full, so a session can still see what
# it just did without opening the archive.
KEEP_RECENT = 3

DONE_STATUSES = ("completed", "done", "complete")
# Fields worth keeping inline on a finished task: identity, outcome, and the gate it
# satisfied. Everything else is how it got there.
TASK_KEEP_FIELDS = ("id", "title", "status", "gate")

TASK_START = re.compile(r"^(\s*)-\s+id:\s*(?P<id>\S+)\s*$")
FIELD = re.compile(r"^\s+(?P<key>[a-z_]+):\s*(?P<value>.*)$")
DOUBT_HEADING = re.compile(r"^#{2,4}\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\s*[:.]\s*(?P<title>.+?)\s*$")


def archive_dir(workspace: Path) -> Path:
    return workspace / ARCHIVE_DIR


def _archived_ids(path: Path, pattern: re.Pattern) -> set[str]:
    """IDs already in an archive. Compaction is idempotent: they are skipped."""
    if not path.is_file():
        return set()
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()
    return {m.group("id") for m in (pattern.match(l.strip()) for l in text.splitlines()) if m}


def _append_archive(path: Path, header: str, blocks: list[str]) -> None:
    """Append before rewriting the source - the archive is never the thing that is lost."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else header
    body = existing.rstrip() + "\n\n" + "\n\n".join(b.rstrip() for b in blocks) + "\n"
    path.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# TASKS.yml
# ---------------------------------------------------------------------------


def _task_blocks(lines: list[str]) -> list[dict]:
    """Every `- id:` block with its line range and parsed fields."""
    blocks: list[dict] = []
    current: dict | None = None
    for index, line in enumerate(lines):
        start = TASK_START.match(line)
        if start:
            if current:
                current["end"] = index
            current = {
                "id": start.group("id").strip().strip("\"'"),
                "indent": start.group(1),
                "start": index,
                "end": len(lines),
                "fields": {},
            }
            blocks.append(current)
            continue
        if current is None:
            continue
        field = FIELD.match(line)
        if field and field.group("value").strip():
            current["fields"].setdefault(field.group("key"), field.group("value").strip())
    return blocks


def compact_tasks(workspace: Path, *, budget: int = TASKS_BUDGET, keep: int = KEEP_RECENT) -> dict:
    """Shrink completed tasks in TASKS.yml, full text to the archive."""
    path = workspace / "TASKS.yml"
    result = {"file": "TASKS.yml", "compacted": [], "before": 0, "after": 0, "skipped": ""}
    if not path.is_file():
        result["skipped"] = "no TASKS.yml"
        return result

    text = path.read_text(encoding="utf-8", errors="ignore")
    result["before"] = len(text)
    if len(text) <= budget:
        result["skipped"] = f"under budget ({len(text):,} <= {budget:,})"
        result["after"] = len(text)
        return result

    lines = text.splitlines()
    blocks = _task_blocks(lines)
    done = [b for b in blocks if b["fields"].get("status", "").lower() in DONE_STATUSES]
    already = _archived_ids(workspace / TASKS_ARCHIVE, re.compile(r"^#\s*(?P<id>TASK\S*)\b"))

    # Reserve the most recent finished ones *first*, from the full list. Filtering by
    # `already` before slicing meant a second run treated the reserved ones as the
    # only remaining candidates and compacted exactly what it had just protected.
    compactable = done[: max(len(done) - keep, 0)]
    candidates = [b for b in compactable if b["id"] not in already]
    if not candidates:
        result["skipped"] = "nothing new to compact"
        result["after"] = len(text)
        return result

    archive_blocks = []
    for block in candidates:
        body = "\n".join(lines[block["start"] : block["end"]]).rstrip()
        archive_blocks.append(f"# {block['id']}\n{body}")

    _append_archive(
        workspace / TASKS_ARCHIVE,
        "# Completed tasks - full detail\n\n"
        "# Compacted out of TASKS.yml by `loop archive`. Their id, title, status and\n"
        "# gate remain in TASKS.yml so dependencies resolve and nothing is recompiled.\n",
        archive_blocks,
    )

    drop: set[int] = set()
    replace: dict[int, list[str]] = {}
    for block in candidates:
        indent = block["indent"]
        kept = [f"{indent}- id: {block['id']}"]
        for key in TASK_KEEP_FIELDS:
            if key == "id" or key not in block["fields"]:
                continue
            kept.append(f"{indent}  {key}: {block['fields'][key]}")
        # A resolvable pointer, not just a status. `status: completed` is a
        # presupposition - it silently licenses assumptions about what the task
        # established. Sun & He (arXiv:2608.01619) measured agents recalling
        # *explicit* stale statements at 0.44-1.0 but *presupposed* ones at 0.06-0.38.
        # This turns the presupposition into something checkable.
        kept.append(f"{indent}  detail: {TASKS_ARCHIVE}#{block['id']}")
        replace[block["start"]] = kept
        drop.update(range(block["start"] + 1, block["end"]))

    out: list[str] = []
    for index, line in enumerate(lines):
        if index in replace:
            out.extend(replace[index])
            continue
        if index in drop:
            continue
        out.append(line)

    new_text = "\n".join(out).rstrip() + "\n"
    new_text = _note_archive(new_text, TASKS_ARCHIVE, comment="#")
    path.write_text(new_text, encoding="utf-8")

    result["compacted"] = [b["id"] for b in candidates]
    result["after"] = len(new_text)
    return result


def _note_archive(text: str, archive_rel: str, *, comment: str) -> str:
    marker = f"{comment} Completed detail: `{archive_rel}`"
    if marker in text:
        return text
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("tasks:"):
            lines.insert(index, marker)
            lines.insert(index + 1, "")
            return "\n".join(lines) + "\n"
    return marker + "\n" + text


# ---------------------------------------------------------------------------
# DOUBTS.md
# ---------------------------------------------------------------------------


def _doubt_blocks(lines: list[str]) -> list[dict]:
    blocks: list[dict] = []
    current: dict | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        heading = DOUBT_HEADING.match(stripped)
        if heading:
            if current:
                current["end"] = index
            current = {
                "id": heading.group("id"),
                "title": heading.group("title"),
                "start": index,
                "end": len(lines),
                "fields": {},
            }
            blocks.append(current)
            continue
        if current is None:
            continue
        if stripped.startswith("#"):
            current["end"] = min(current["end"], index)
            current = None
            continue
        match = re.match(r"^[-*]\s+\*\*(?P<key>[^:*]+):?\*\*:?\s*(?P<value>.*)$", stripped)
        if match:
            current["fields"].setdefault(match.group("key").strip().lower(), match.group("value").strip())
    return blocks


def compact_doubts(workspace: Path, *, budget: int = DOUBTS_BUDGET, keep: int = KEEP_RECENT) -> dict:
    """Shrink resolved doubts to id + status + answer; rationale to the archive."""
    from doubts import OPEN, parse

    path = workspace / "DOUBTS.md"
    result = {"file": "DOUBTS.md", "compacted": [], "before": 0, "after": 0, "skipped": ""}
    if not path.is_file():
        result["skipped"] = "no DOUBTS.md"
        return result

    text = path.read_text(encoding="utf-8", errors="ignore")
    result["before"] = len(text)
    if len(text) <= budget:
        result["skipped"] = f"under budget ({len(text):,} <= {budget:,})"
        result["after"] = len(text)
        return result

    closed = {d.id for d in parse(workspace) if d.status != OPEN and not d.superseded_by}
    lines = text.splitlines()
    blocks = [b for b in _doubt_blocks(lines) if b["id"] in closed]
    already = _archived_ids(workspace / DOUBTS_ARCHIVE, DOUBT_HEADING)

    # Only compact an entry that records its answer. Most closed doubts in a real
    # file predate `loop doubts resolve` and have no `Resolution:` field at all -
    # compacting those would strip the question and leave nothing in its place, which
    # is exactly how "reuse, don't re-ask" would start re-asking. `loop doubts lint`
    # already flags them; they stay in full until someone records the answer.
    def _answer(block: dict) -> str:
        for key, value in block["fields"].items():
            if key.startswith(("resolution", "resolved", "deferral", "answer")):
                return value
        return ""

    answered = [b for b in blocks if _answer(b)]
    result["unanswered"] = [b["id"] for b in blocks if not _answer(b)]

    compactable = answered[: max(len(answered) - keep, 0)]
    candidates = [b for b in compactable if b["id"] not in already]
    if not candidates:
        result["skipped"] = "nothing new to compact"
        result["after"] = len(text)
        return result

    _append_archive(
        workspace / DOUBTS_ARCHIVE,
        "# Resolved doubts - full detail\n\n"
        "Compacted out of `DOUBTS.md` by `loop archive`. Each one's id, status and\n"
        "answer remain there, so `reuse, don't re-ask` still works without this file.\n"
        "Search it with `loop doubts search <term>`.\n",
        ["\n".join(lines[b["start"] : b["end"]]).rstrip() for b in candidates],
    )

    drop: set[int] = set()
    replace: dict[int, list[str]] = {}
    for block in candidates:
        answer = _answer(block)
        kept = [
            f"### {block['id']}: {block['title']}",
            f"- **Status:** {block['fields'].get('status', 'resolved').split('(')[0].strip()}",
        ]
        if answer:
            kept.append(f"- **Answer:** {answer}")
        kept.append(f"- **Detail:** `{DOUBTS_ARCHIVE}`")
        replace[block["start"]] = kept
        drop.update(range(block["start"] + 1, block["end"]))

    out: list[str] = []
    for index, line in enumerate(lines):
        if index in replace:
            out.extend(replace[index])
            continue
        if index in drop:
            continue
        out.append(line)

    new_text = "\n".join(out).rstrip() + "\n"
    path.write_text(new_text, encoding="utf-8")

    result["compacted"] = [b["id"] for b in candidates]
    result["after"] = len(new_text)
    return result


# ---------------------------------------------------------------------------
# EVIDENCE_LOG.md and DECISIONS.md - compact what is settled, keep what is live
# ---------------------------------------------------------------------------

EVIDENCE_ARCHIVE = "plan/archive/EVIDENCE_SETTLED.md"
DECISIONS_ARCHIVE = "plan/archive/DECISIONS_DETAIL.md"

EVIDENCE_BUDGET = 12_000
DECISIONS_BUDGET = 12_000

ENTRY_HEADING = re.compile(r"^(?P<hashes>#{2,4})\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\s*[:.]?\s*(?P<title>.*)$")
REF_ID = re.compile(r"\b([A-Z]{1,3}(?:-[A-Z]+)*-\d+)\b")

# Kept inline on a settled entry. The heading already states the finding; these are
# the fields something downstream reads or a reader needs to judge weight.
EVIDENCE_KEEP = ("type", "confidence")
DECISION_KEEP = ("date", "decision", "supersedes")


def _entry_blocks(lines: list[str]) -> list[dict]:
    """`### ID: title` blocks with their line range and `- **Key:** value` fields."""
    blocks: list[dict] = []
    current: dict | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        heading = ENTRY_HEADING.match(stripped)
        if heading:
            if current:
                current["end"] = index
            current = {
                "id": heading.group("id"),
                "hashes": heading.group("hashes"),
                "title": heading.group("title").strip(),
                "start": index,
                "end": len(lines),
                "fields": {},
            }
            blocks.append(current)
            continue
        if current is None:
            continue
        if stripped.startswith("#"):
            current["end"] = min(current["end"], index)
            current = None
            continue
        field = re.match(r"^[-*]\s+\*\*(?P<key>[^:*]+):?\*\*:?\s*(?P<value>.*)$", stripped)
        if field:
            current["fields"].setdefault(field.group("key").strip().lower(), field.group("value").strip())
    return blocks


def live_references(workspace: Path) -> set[str]:
    """IDs reachable from work that is still in play.

    Evidence backing an open question or an unfinished task is still being argued
    about - it stays in full. Evidence that only backs a settled decision has done its
    job: the finding stays readable in its heading, the sourcing moves to the archive.

    Resolved through `graph_index`, which follows citations *transitively* - an open
    task cites a doubt, the doubt cites the evidence. Scraping IDs out of four files'
    raw text, as this used to, could only see the first hop, so evidence one step
    removed from live work read as settled and got compacted.

    Falls back to the flat scan if the graph cannot be built, so a malformed file
    degrades to the old behaviour rather than archiving something it should not.
    """
    try:
        import graph_index

        graph = graph_index.build(workspace)
        live = graph_index.live_nodes(graph)
        # Depth 3: task -> doubt -> decision -> evidence is the longest real chain.
        return graph_index.reachable_from(graph, live, depth=3)
    except Exception:
        return _live_references_by_scan(workspace)


def _live_references_by_scan(workspace: Path) -> set[str]:
    """First-hop-only fallback. Kept so a parse failure cannot cause over-archiving."""
    import doubts as doubts_mod
    from task_context import DONE_STATUSES, parse_tasks

    parts: list[str] = []
    for entry in doubts_mod.parse(workspace):
        if entry.status == doubts_mod.OPEN:
            parts.append(f"{entry.title} {entry.question} {entry.why} {entry.default}")
    for task in parse_tasks(workspace):
        if str(task.get("status", "")).lower() not in DONE_STATUSES:
            parts.append("\n".join(task.get("raw", [])))
    for rel in ("plan/main_plan.md", "HANDOFF.md"):
        path = workspace / rel
        if path.is_file():
            parts.append(path.read_text(encoding="utf-8", errors="ignore"))
    return set(REF_ID.findall("\n".join(parts)))


def _compact_entries(
    workspace: Path,
    *,
    source: str,
    archive_rel: str,
    budget: int,
    keep: int,
    keep_fields: tuple[str, ...],
    archive_header: str,
) -> dict:
    path = workspace / source
    result = {"file": source, "compacted": [], "before": 0, "after": 0, "skipped": ""}
    if not path.is_file():
        result["skipped"] = f"no {source}"
        return result

    text = path.read_text(encoding="utf-8", errors="ignore")
    result["before"] = result["after"] = len(text)
    if len(text) <= budget:
        result["skipped"] = f"under budget ({len(text):,} <= {budget:,})"
        return result

    lines = text.splitlines()
    blocks = _entry_blocks(lines)
    if not blocks:
        result["skipped"] = "no structured entries"
        return result

    live = live_references(workspace)
    already = _archived_ids(workspace / archive_rel, ENTRY_HEADING)
    settled = [b for b in blocks if b["id"] not in live]

    compactable = settled[: max(len(settled) - keep, 0)]
    candidates = [b for b in compactable if b["id"] not in already]
    result["live"] = [b["id"] for b in blocks if b["id"] in live]
    if not candidates:
        result["skipped"] = "nothing settled to compact"
        return result

    _append_archive(
        workspace / archive_rel,
        archive_header,
        ["\n".join(lines[b["start"] : b["end"]]).rstrip() for b in candidates],
    )

    drop: set[int] = set()
    replace: dict[int, list[str]] = {}
    for block in candidates:
        kept = [f"{block['hashes']} {block['id']}: {block['title']}"]
        for key in keep_fields:
            if key in block["fields"]:
                kept.append(f"- **{key.title()}:** {block['fields'][key]}")
        kept.append(f"- **Detail:** `{archive_rel}`")
        replace[block["start"]] = kept
        drop.update(range(block["start"] + 1, block["end"]))

    out: list[str] = []
    for index, line in enumerate(lines):
        if index in replace:
            out.extend(replace[index])
            continue
        if index not in drop:
            out.append(line)

    new_text = "\n".join(out).rstrip() + "\n"
    path.write_text(new_text, encoding="utf-8")
    result["compacted"] = [b["id"] for b in candidates]
    result["after"] = len(new_text)
    return result


def compact_evidence(workspace: Path, *, budget: int = EVIDENCE_BUDGET, keep: int = KEEP_RECENT) -> dict:
    return _compact_entries(
        workspace,
        source="EVIDENCE_LOG.md",
        archive_rel=EVIDENCE_ARCHIVE,
        budget=budget,
        keep=keep,
        keep_fields=EVIDENCE_KEEP,
        archive_header=(
            "# Settled evidence - full detail\n\n"
            "Compacted out of `EVIDENCE_LOG.md` by `loop archive`. Each entry's id and\n"
            "headline finding stay there, so every `E-*` citation still resolves.\n"
            "Evidence cited by an open doubt, an unfinished task, the live plan or\n"
            "HANDOFF.md is never compacted. Search with `loop archive --search <term>`.\n"
        ),
    )


def compact_decisions(workspace: Path, *, budget: int = DECISIONS_BUDGET, keep: int = KEEP_RECENT) -> dict:
    """Keep the decision; archive the argument.

    `hierarchy_drift.decision_entries()` keys on the ADR heading and reads
    `- **Decision:**`, and `doubts.supersessions()` reads `- **Supersedes:**`. Both
    stay inline, so cross-workspace supersession and conflict detection are unaffected.
    """
    return _compact_entries(
        workspace,
        source="DECISIONS.md",
        archive_rel=DECISIONS_ARCHIVE,
        budget=budget,
        keep=keep,
        keep_fields=DECISION_KEEP,
        archive_header=(
            "# Decision detail - rationale, evidence and consequences\n\n"
            "Compacted out of `DECISIONS.md` by `loop archive`. The decision itself, its\n"
            "date and any `Supersedes:` stay there - drift checks and supersession read\n"
            "them. A decision still referenced by open work is never compacted.\n"
        ),
    )


RECALL_LOG = ".loop/archive-recall.json"


def _record_recall(workspace: Path, term: str, hits: int) -> None:
    """Count how often the archive is actually opened.

    An archive nobody reads is lossy extraction with extra steps, and the measured
    penalty for that is large - verbatim context beat extracted artifacts by 15-25pp
    on multi-hop questions (arXiv:2601.00821). ARC is explicit that an
    ID-addressable archive guarantees *recoverability*, not that anything recalls.
    So: measure it. If this stays at zero, the archive is not earning its place.
    """
    import json
    from datetime import date

    path = workspace / RECALL_LOG
    try:
        log = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (json.JSONDecodeError, OSError):
        log = {}
    log["searches"] = int(log.get("searches", 0)) + 1
    log["hits"] = int(log.get("hits", 0)) + hits
    log["last"] = {"term": term, "hits": hits, "at": date.today().isoformat()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(log, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError:
        pass


def recall_stats(workspace: Path) -> dict:
    import json

    path = workspace / RECALL_LOG
    if not path.exists():
        return {"searches": 0, "hits": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"searches": 0, "hits": 0}



def search_archive(workspace: Path, term: str) -> list[str]:
    """Find an answer in the archive without loading it into context."""
    hits: list[str] = []
    lowered = term.lower()
    for rel in (DOUBTS_ARCHIVE, TASKS_ARCHIVE, EVIDENCE_ARCHIVE, DECISIONS_ARCHIVE):
        path = workspace / rel
        if not path.is_file():
            continue
        block: list[str] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("### ") or line.startswith("# TASK"):
                if block and any(lowered in b.lower() for b in block):
                    hits.append("\n".join(block[:8]))
                block = [line]
            else:
                block.append(line)
        if block and any(lowered in b.lower() for b in block):
            hits.append("\n".join(block[:8]))
    _record_recall(workspace, term, len(hits))
    return hits


BUDGETS = (
    ("TASKS.yml", TASKS_BUDGET),
    ("DOUBTS.md", DOUBTS_BUDGET),
    ("EVIDENCE_LOG.md", EVIDENCE_BUDGET),
    ("DECISIONS.md", DECISIONS_BUDGET),
)


def run(workspace: Path, *, dry_run: bool = False) -> list[dict]:
    if dry_run:
        results = []
        for name, budget in BUDGETS:
            path = workspace / name
            size = len(path.read_text(encoding="utf-8", errors="ignore")) if path.is_file() else 0
            results.append(
                {
                    "file": name,
                    "before": size,
                    "after": size,
                    "compacted": [],
                    "skipped": "dry run" if size > budget else f"under budget ({size:,} <= {budget:,})",
                }
            )
        return results
    return [
        compact_tasks(workspace),
        compact_doubts(workspace),
        compact_evidence(workspace),
        compact_decisions(workspace),
    ]


def describe(results: list[dict]) -> str:
    lines = []
    for item in results:
        if item["skipped"]:
            lines.append(f"{item['file']}: {item['skipped']}")
            continue
        saved = item["before"] - item["after"]
        lines.append(
            f"{item['file']}: {item['before']:,} -> {item['after']:,} chars "
            f"(-{saved:,}), {len(item['compacted'])} entry(ies) compacted"
        )
        unanswered = item.get("unanswered") or []
        if unanswered:
            lines.append(
                f"  left in full: {', '.join(unanswered[:6])}"
                f"{' ...' if len(unanswered) > 6 else ''} - closed with no recorded answer "
                "(`loop doubts lint`)"
            )
    return "\n".join(lines) or "Nothing to compact."


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

    parser = argparse.ArgumentParser(description="Compact finished work; keep the ledger inline.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--search", default=None, help="Find an answer in the archive.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if args.search:
        hits = search_archive(workspace, args.search)
        print("\n\n".join(hits) if hits else f"No archived entry mentions {args.search!r}.")
        return 0

    print(describe(run(workspace, dry_run=args.dry_run)))
    stats = recall_stats(workspace)
    archived = any((workspace / rel).is_file() for rel in (TASKS_ARCHIVE, DOUBTS_ARCHIVE, EVIDENCE_ARCHIVE, DECISIONS_ARCHIVE))
    if archived and not stats.get("searches"):
        print(
            "\nNothing has ever been recalled from the archive. If that stays true, the "
            "detail is not being used and compaction is losing it in practice, not just on paper."
        )
    elif stats.get("searches"):
        print(f"\nArchive recalled {stats['searches']} time(s), {stats.get('hits', 0)} hit(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
