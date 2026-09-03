#!/usr/bin/env python3
"""Curate bounded memory files and detect drift."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from memory_paths import (
    MEMORY_CHAR_LIMIT,
    USER_CHAR_LIMIT,
    ensure_memory_layout,
    memory_file,
    soul_file,
    user_file,
)
from memory_paths import state_db
from pending_writes import list_pending, stage_memory_write
from session_store import init_db, log_session
from workspace_utils import resolve_workspace


ENTRY_SEP = "\n§\n"

SECTION_SIGN = "§"


def char_count(text: str) -> int:
    return len(text.strip())


def uses_section_sign(text: str) -> bool:
    """Whether this file already uses § as a record separator.

    Files that never adopted the separator are plain markdown and must stay
    that way: writing § into them fragments hand-authored structure on the
    next run (the §-splitter re-parses what was just written).
    """
    return SECTION_SIGN in text


def _header_lines(text: str, header: str = "# Memory") -> int:
    """Standalone header lines only - inline `code` mentions do not count."""
    return sum(1 for line in text.splitlines() if line.strip() == header)


def normalize_header(text: str, header: str = "# Memory") -> str:
    """Collapse stacked duplicate headers to exactly one leading header.

    Repeated closeouts used to prepend "# Memory\\n\\n" without stripping the
    existing one, so headers accumulated (7x observed). Any standalone header
    line beyond the first is residue - inline mentions (e.g. `` `# Memory` ``
    in a warning banner) are left alone. Idempotent.
    """
    lines = text.splitlines()
    kept: list[str] = []
    seen_header = False
    for line in lines:
        if line.strip() == header:
            if seen_header:
                continue
            seen_header = True
        kept.append(line)
    rest = "\n".join(kept).strip()
    if not rest:
        return header + "\n\n"
    if rest.startswith(header):
        return rest + "\n"
    return header + "\n\n" + rest + "\n"


def strip_leading_header(text: str, header: str = "# Memory") -> str:
    """Body without the leading header block (for entry parsing)."""
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    while idx < len(lines) and lines[idx].strip() == header:
        idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
    return "\n".join(lines[idx:])


def split_entries(text: str) -> list[str]:
    """Parse entries without destroying document structure.

    - §-files: split on §, but first remove the leading "# Memory" header
      block so it is not kept as entry content (the header-stacking bug), and
      keep every other `#`/`##` heading line inside its entry (the
      heading-loss bug dropped all of them).
    - Plain markdown: return each non-empty, non-header line as an entry for
      *analysis only* (dedupe/usage). Callers must NOT `join_entries` these
      back over the original file - that reformatting is what flattened
      hand-authored `## Recent` diaries into §-shards.
    """
    if uses_section_sign(text):
        body = strip_leading_header(text)
        return [part.strip() for part in body.split(SECTION_SIGN) if part.strip()]
    lines = [
        line.strip()
        for line in strip_leading_header(text).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return lines


def join_entries(entries: list[str]) -> str:
    """Rejoin §-parsed entries with exactly one header.

    Only valid for content parsed from a §-file. Never call this on entries
    parsed from plain markdown and write the result back - use the original
    text plus a markdown append instead (see `apply_report`).
    """
    header = "# Memory\n\n"
    cleaned: list[str] = []
    for entry in entries:
        body = entry.strip()
        while body.startswith("# Memory"):
            body = body[len("# Memory"):].strip().lstrip("\n").strip()
        if body:
            cleaned.append(body)
    if not cleaned:
        return header + "_No curated entries yet._\n"
    return header + ENTRY_SEP.join(cleaned) + "\n"


def usage_report(text: str, limit: int) -> dict:
    count = char_count(text)
    pct = int((count / limit) * 100) if limit else 0
    return {"chars": count, "limit": limit, "percent": pct, "over": count > limit}


def detect_drift(workspace: Path) -> list[str]:
    issues: list[str] = []
    root = workspace / "MEMORY.md"
    canonical = memory_file(workspace)
    if root.exists() and canonical.exists() and root.resolve() != canonical.resolve():
        issues.append(
            "Legacy root `MEMORY.md` still exists - canonical memory is `memories/MEMORY.md`; "
            "run `loop migrate workspace` to relocate it."
        )
    return issues


def dedupe_entries(entries: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for entry in entries:
        key = re.sub(r"\s+", " ", entry.lower()).strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def trim_to_limit(entries: list[str], limit: int, header: str = "# Memory\n\n") -> tuple[list[str], list[str]]:
    """Trim §-entries to `limit`, keeping the intro plus the NEWEST entries.

    The old version kept the OLDEST entries and silently dropped the newest
    closeout work once the file went over budget - memory stopped updating.
    The first entry (file intro / top matter) is always preserved; the rest
    is newest-first.
    """
    if not entries:
        return [], []
    full = header + ENTRY_SEP.join(entries) + "\n"
    if char_count(full) <= limit:
        return list(entries), []
    intro = entries[:1]
    rest = entries[1:]
    kept_newest: list[str] = []
    for entry in reversed(rest):
        # Build newest-first: entry goes before what we already kept.
        candidate = header + ENTRY_SEP.join(intro + ([entry] + kept_newest)) + "\n"
        if char_count(candidate) <= limit:
            kept_newest.insert(0, entry)
        else:
            continue
    kept = intro + kept_newest
    kept_keys = {id(e) for e in kept}
    dropped = [e for e in entries if id(e) not in kept_keys]
    return kept, dropped


def trim_markdown_recent(text: str, limit: int, *, max_drop_fraction: float = 0.30) -> tuple[str, list[str]]:
    """Trim only the oldest top-level bullets under `## Recent` until fit.

    Everything before `## Recent` (warning banners, intro, standing context)
    is never touched. If there is no `## Recent` section, nothing is trimmed -
    the caller reports over-budget and leaves the file to a human rather than
    reformatting it. Trimming is also capped: at most `max_drop_fraction` of
    the file's chars go in one run, so a diary that grew 4x over budget is
    reported over-budget (human compacts it) rather than mass-deleted by a
    closeout. Returns (new_text, dropped_bullets).
    """
    if char_count(text) <= limit:
        return text, []
    original_chars = char_count(text)
    lines = text.splitlines()
    head_idx = next(
        (i for i, l in enumerate(lines) if l.strip().lower() == "## recent"), None
    )
    if head_idx is None:
        return text, []
    # Top-level bullets start at column 0 with "- ".
    bullet_idx = [i for i in range(head_idx + 1, len(lines)) if lines[i].startswith("- ")]
    if len(bullet_idx) <= 1:
        return text, []
    dropped: list[str] = []
    current = list(lines)
    removed_chars = 0
    for bi in bullet_idx:
        # Recompute bullet positions after each removal.
        cur_bullets = [i for i, l in enumerate(current) if l.startswith("- ") and i > head_idx]
        if len(cur_bullets) <= 1:
            break
        if char_count("\n".join(current)) <= limit:
            break
        if removed_chars / max(original_chars, 1) >= max_drop_fraction:
            break
        first = cur_bullets[0]
        # Remove the bullet line plus its indented continuation lines.
        end = first + 1
        while end < len(current) and (current[end].startswith("  ") or not current[end].strip()):
            if current[end].startswith("  "):
                end += 1
            else:
                break
        removed_chars += char_count("\n".join(current[first:end]))
        dropped.append(current[first][:120])
        del current[first:end]
    return "\n".join(current).rstrip() + "\n", dropped


# Bullets scraped from state files must clear this bar before becoming memory.
CLOSEOUT_MIN_LEN = 40
CLOSEOUT_BOILERPLATE = (
    "commands/",
    "skills/",
    "cursor.md",
    "claude.md",
    "codex.md",
    "opencode.md",
    "grok.md",
    "adapters.md",
    "api_usage.md",
    "use `/plan",
    "use `/product",
    "use `/loop",
    "keep reusable logic",
    "always update `memory",
    "populate `tasks",
    "create `plan/step",
    "ask product initialization",
    "waiting for the user to run",
    "on `/plan`,",
    "run `/plan`.",
    "created reusable loop command contracts",
    "created canonical cross-tool skill pack",
    "added adapters",
    "created `plan/main_plan.md` as an uninitialized",
    "created `plan/` for future step plans",
    "compact.md",
    "read `compact",
    "sync note",
    "loop state files were reconciled",
    "was updated.",
    "may continue with safe",
    "ask the user to resolve human-required",
)


def _closeout_candidate_ok(body: str) -> bool:
    if len(body) < CLOSEOUT_MIN_LEN:
        return False
    if SECTION_SIGN in body or body.startswith("#"):
        return False
    lowered = body.lower()
    if lowered.startswith("warning"):
        return False
    return not any(marker in lowered for marker in CLOSEOUT_BOILERPLATE)


def propose_closeout_entries(workspace: Path, memory_text: str) -> list[str]:
    """Rule-based closeout proposals from recent state-file bullets.

    Quality-gated: template boilerplate, warning banners, and §-fragments
    are never proposed (they were the bulk of the staged-queue spam).
    """
    proposals: list[str] = []
    memory_lower = memory_text.lower()
    # An entry sitting unapproved in the queue is not in MEMORY.md yet, so the
    # memory check alone would re-propose it every session. Treat queued content
    # as already proposed.
    queued = {
        re.sub(r"\s+", " ", str(item.get("content", "")).strip().lower())
        for item in list_pending(workspace)
        if item.get("kind") == "memory"
    }
    for rel in ("DECISIONS.md", "HANDOFF.md"):
        path = workspace / rel
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-30:]
        # Group consecutive bullets: one decision's fields (`- **Decision:**`,
        # `- **Scope:**`, ...) arrive as adjacent lines and only make sense
        # together. A lone line is its own group.
        runs: list[list[str]] = []
        current: list[str] = []
        for line in raw + [""]:
            stripped = line.strip()
            if stripped.startswith("- "):
                current.append(stripped[2:].strip())
            elif current:
                runs.append(current)
                current = []
        for parts in runs:
            # Drop the parts memory (or the queue) already holds, so a group
            # never re-adds known text beside one new line. Drop repeats
            # inside the group too (triplicated log lines propose once).
            seen_parts: set[str] = set()
            unique: list[str] = []
            for p in parts:
                key = re.sub(r"\s+", " ", p.lower())
                if key in seen_parts:
                    continue
                seen_parts.add(key)
                unique.append(p)
            fresh = [
                p for p in unique
                if re.sub(r"\s+", " ", p.lower()) not in memory_lower
                and re.sub(r"\s+", " ", p.lower()) not in queued
            ]
            if not fresh:
                continue
            body = " ".join(fresh)
            if len(body) > 600:
                body = body[:600].rsplit(" ", 1)[0]
            if not _closeout_candidate_ok(body):
                continue
            proposals.append(body)
    return proposals[:5]


def backup_memory_file(path: Path, workspace: Path) -> Path | None:
    """Copy the pre-write file into `.loop/backups/memories/`, prune to 10."""
    try:
        if not path.exists():
            return None
        from datetime import datetime, timezone

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest_dir = workspace / ".loop" / "backups" / "memories"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{path.stem}-{stamp}.md"
        dest.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        existing = sorted(dest_dir.glob(f"{path.stem}-*.md"))
        for old in existing[:-10]:
            old.unlink(missing_ok=True)
        return dest
    except Exception:
        return None


def validate_memory_output(before: str, after: str, header: str = "# Memory") -> list[str]:
    """Refuse conditions that previously destroyed MEMORY.md. Returns errors."""
    errors: list[str] = []
    if _header_lines(after, header) > 1:
        errors.append(f"refused: output stacks {_header_lines(after, header)}x `{header}` headers")
    if SECTION_SIGN not in before and SECTION_SIGN in after:
        errors.append("refused: output injects § into a file that never used it")
    if len(before.strip()) > 500 and len(after.strip()) < len(before.strip()) // 2:
        errors.append(
            f"refused: output collapses {len(before.strip())} -> {len(after.strip())} chars (>50% loss)"
        )
    return errors


def append_markdown_entries(base: str, entries: list[str]) -> str:
    """Append entries to plain markdown without introducing §."""
    body = base.rstrip() + "\n" if base.strip() else "# Memory\n\n"
    for entry in entries:
        text = entry.strip()
        if not text:
            continue
        if text.startswith(("-", "*", "#")) or text[0].isdigit():
            body += "\n" + text + "\n"
        else:
            body += "\n- " + text + "\n"
    return body


def propose_updates(workspace: Path) -> dict:
    ensure_memory_layout(workspace)
    mem_path = memory_file(workspace)
    user_path = user_file(workspace)
    mem_text = mem_path.read_text(encoding="utf-8") if mem_path.exists() else ""
    user_text = user_path.read_text(encoding="utf-8") if user_path.exists() else ""

    mem_sectioned = uses_section_sign(mem_text)
    if mem_sectioned:
        mem_entries = dedupe_entries(split_entries(mem_text))
        mem_kept, mem_dropped = trim_to_limit(mem_entries, MEMORY_CHAR_LIMIT)
        memory_output = join_entries(mem_kept)
        memory_text = strip_leading_header(memory_output).strip()
        trim_suggestion: list[str] = []
    else:
        # Plain markdown: analyze only. The file is preserved verbatim;
        # reformatting it through split/join is what destroyed diaries.
        # Hand-written diaries are append-only: over budget is reported with
        # a trim suggestion for a human, never auto-deleted by a closeout.
        mem_entries = dedupe_entries(split_entries(mem_text))
        base = normalize_header(mem_text) if mem_text.strip() else "# Memory\n\n_No curated entries yet._\n"
        _, suggested = trim_markdown_recent(base, MEMORY_CHAR_LIMIT)
        memory_output = base
        mem_kept, mem_dropped = mem_entries, []
        trim_suggestion = [f"## Recent trim suggestion: {d}" for d in suggested]
        memory_text = strip_leading_header(memory_output).strip()

    user_sectioned = uses_section_sign(user_text)
    if user_sectioned:
        user_entries = dedupe_entries(split_entries(user_text))
        user_kept, user_dropped = trim_to_limit(user_entries, USER_CHAR_LIMIT, header="# User Profile\n\n")
        user_output = "# User Profile\n\n" + ENTRY_SEP.join(user_kept) + "\n" if user_kept else user_text
    else:
        user_entries = dedupe_entries(split_entries(user_text))
        user_output = normalize_header(user_text, "# User Profile") if user_text.strip() else user_text
        user_kept, user_dropped = user_entries, []

    closeout = propose_closeout_entries(workspace, mem_text)

    return {
        "drift": detect_drift(workspace),
        "memory_usage": usage_report(mem_text, MEMORY_CHAR_LIMIT),
        "user_usage": usage_report(user_text, USER_CHAR_LIMIT),
        "memory_entries_before": len(mem_entries),
        "memory_entries_after": len(mem_kept),
        "memory_dropped": mem_dropped,
        "memory_trim_suggestion": trim_suggestion,
        "user_dropped": user_dropped,
        "memory_text": memory_text,
        "memory_output": memory_output,
        "user_output": user_output,
        "soul_exists": soul_file(workspace).exists(),
        "closeout_proposals": closeout,
        "pending_count": len(list_pending(workspace)),
    }


def render_report(workspace: Path, report: dict) -> str:
    lines = [
        "# Memory Review",
        "",
        f"**Updated:** {date.today().isoformat()}",
        f"**Workspace:** `{workspace}`",
        "",
        "## Usage",
        "",
        f"- Memory: {report['memory_usage']['chars']}/{report['memory_usage']['limit']} chars ({report['memory_usage']['percent']}%)",
        f"- User: {report['user_usage']['chars']}/{report['user_usage']['limit']} chars ({report['user_usage']['percent']}%)",
        "",
        "## Drift",
        "",
    ]
    lines.extend(f"- {item}" for item in report["drift"]) or lines.append("- None.")
    lines.extend(["", "## Curator Actions", ""])
    if report["memory_entries_before"] != report["memory_entries_after"]:
        lines.append(f"- Deduped/trimmed memory entries: {report['memory_entries_before']} -> {report['memory_entries_after']}")
    if report["memory_dropped"]:
        lines.append(f"- Dropped {len(report['memory_dropped'])} memory entry(ies) over limit.")
    if report.get("memory_trim_suggestion"):
        lines.append(
            f"- Memory is over budget and hand-written, so nothing was auto-deleted. "
            f"Oldest-first candidates to trim by hand: {len(report['memory_trim_suggestion'])}."
        )
        for suggestion in report["memory_trim_suggestion"][:5]:
            lines.append(f"  - {suggestion[:140]}")
    if report["user_dropped"]:
        lines.append(f"- Dropped {len(report['user_dropped'])} user entry(ies) over limit.")
    if not report["memory_dropped"] and not report["user_dropped"] and not report["drift"]:
        lines.append("- Memory files are within limits.")
    if report.get("closeout_proposals"):
        lines.append(f"- Proposed {len(report['closeout_proposals'])} closeout memory entry(ies) from state files.")
    if report.get("pending_count"):
        lines.append(f"- Pending staged writes: {report['pending_count']} (run `loop pending list`).")
    lines.extend(["", "## SOUL", "", f"- `memories/SOUL.md` exists: {report['soul_exists']}", ""])
    if report.get("closeout_proposals"):
        lines.extend(["", "## Closeout Proposals", ""])
        for entry in report["closeout_proposals"]:
            lines.append(f"- {entry}")
    return "\n".join(lines) + "\n"


def apply_report(workspace: Path, report: dict, stage_only: bool = False) -> list[str]:
    """Write this workspace's own memory.

    Memory curation and closeout entries are same-workspace, rule-derived, and
    reversible - the loop maintaining itself. They are not the "high-risk
    external actions" that AGENTS.md non-negotiable #5 gates on human approval,
    so they apply directly. Routing them through the approval queue is what
    stalled the loop: closeout runs every session, nobody approves 100+ notices,
    and memory silently stops updating.

    The approval queue still guards writes that genuinely need a human: a parent
    workspace proposing into a sub-product (which plan is wrong is a judgment
    call) and agent-authored skill files. Those never come through here.

    `stage_only` keeps the old behavior for callers that want a dry gate.
    """
    actions: list[str] = []
    mem_path = memory_file(workspace)
    user_path = user_file(workspace)

    if stage_only:
        if report["memory_dropped"] or report["memory_entries_before"] != report["memory_entries_after"]:
            errors = validate_memory_output(
                mem_path.read_text(encoding="utf-8") if mem_path.exists() else "",
                report["memory_output"],
            )
            if errors:
                actions.append("curator replace withheld: " + "; ".join(errors))
            else:
                stage_memory_write(
                    workspace,
                    target="memory",
                    action="replace",
                    content=report["memory_output"],
                    reason="Memory curator trim/dedupe",
                )
                actions.append("staged memory curation for approval")
        for entry in report.get("closeout_proposals", []):
            stage_memory_write(
                workspace,
                target="memory",
                action="append",
                content=entry,
                reason="Closeout proposal from DECISIONS/HANDOFF",
            )
            actions.append("staged closeout memory proposal")
        return actions

    mem_path.parent.mkdir(parents=True, exist_ok=True)
    memory_output = report["memory_output"]
    closeout = [e for e in report.get("closeout_proposals", []) if _closeout_candidate_ok(e)]
    if closeout:
        # Curation alone only rewrites what is already there; without this the
        # closeout entries are computed, reported, and then dropped on the floor.
        # Plain-markdown files get markdown bullets; §-files keep their separator.
        if uses_section_sign(memory_output):
            body = memory_output.rstrip()
            for entry in closeout:
                body = (body + ENTRY_SEP + entry.strip()) if body.strip() else entry.strip()
            memory_output = body + "\n"
        else:
            memory_output = append_markdown_entries(memory_output, closeout)
        if uses_section_sign(memory_output) and char_count(memory_output) > MEMORY_CHAR_LIMIT:
            # §-files are the curator's own format: re-trim newest-kept.
            kept, _ = trim_to_limit(
                dedupe_entries(split_entries(memory_output)), MEMORY_CHAR_LIMIT
            )
            memory_output = join_entries(kept)
        elif char_count(memory_output) > MEMORY_CHAR_LIMIT:
            # Hand-written diaries stay over budget rather than lose history:
            # no auto-trim. The review report carries the trim suggestion.
            actions.append(
                f"note: `memories/MEMORY.md` is {char_count(memory_output)}/{MEMORY_CHAR_LIMIT} chars "
                f"(over budget; see trim suggestions in `plan/MEMORY_REVIEW.md`)"
            )
    before = mem_path.read_text(encoding="utf-8") if mem_path.exists() else ""
    errors = validate_memory_output(before, memory_output)
    if errors:
        actions.append("memory write withheld: " + "; ".join(errors))
        actions.append("left `memories/MEMORY.md` untouched; see `plan/MEMORY_REVIEW.md`")
        return actions
    backup_memory_file(mem_path, workspace)
    mem_path.write_text(memory_output, encoding="utf-8")
    actions.append(f"updated `{mem_path.relative_to(workspace)}`")
    if closeout:
        actions.append(f"appended {len(closeout)} closeout memory entry(ies)")

    if report["user_dropped"]:
        user_before = user_path.read_text(encoding="utf-8") if user_path.exists() else ""
        user_errors = validate_memory_output(user_before, report["user_output"], header="# User Profile")
        if user_errors:
            actions.append("user write withheld: " + "; ".join(user_errors))
        else:
            backup_memory_file(user_path, workspace)
            user_path.write_text(report["user_output"], encoding="utf-8")
            actions.append(f"updated `{user_path.relative_to(workspace)}`")

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate bounded product memory files.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply curation directly (default).")
    parser.add_argument("--stage", action="store_true", help="Stage writes for approval instead of applying.")
    parser.add_argument("--review-only", action="store_true", help="Write plan/MEMORY_REVIEW.md and change nothing.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    report = propose_updates(workspace)
    output = workspace / "plan" / "MEMORY_REVIEW.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(workspace, report), encoding="utf-8")

    stage_only = args.stage
    if not args.review_only:
        actions = apply_report(workspace, report, stage_only=stage_only)
        for action in actions:
            print(action)
    elif report.get("closeout_proposals"):
        print(f"{len(report['closeout_proposals'])} closeout proposal(s) recorded; run with --stage to queue approval.")

    db = state_db(workspace)
    init_db(db)
    log_session(
        db,
        workspace=str(workspace),
        command="/memory-review",
        title="Memory review",
        body=output.read_text(encoding="utf-8")[:2000],
        tags="memory review curator",
    )

    print(f"Wrote {output}")
    if report["memory_usage"]["over"]:
        print("Memory over limit - run with --apply or --stage.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
