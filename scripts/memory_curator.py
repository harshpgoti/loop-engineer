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


def char_count(text: str) -> int:
    return len(text.strip())


def split_entries(text: str) -> list[str]:
    if ENTRY_SEP.strip() in text:
        return [part.strip() for part in text.split("§") if part.strip()]
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    return lines


def join_entries(entries: list[str]) -> str:
    header = "# Memory\n\n" if entries else "# Memory\n\n"
    if not entries:
        return header + "_No curated entries yet._\n"
    body = ENTRY_SEP.join(entries)
    return header + body + "\n"


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
            "Legacy root `MEMORY.md` still exists — canonical memory is `memories/MEMORY.md`; "
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
    kept: list[str] = []
    dropped: list[str] = []
    for entry in entries:
        candidate = header + ENTRY_SEP.join(kept + [entry]) + "\n"
        if char_count(candidate) <= limit:
            kept.append(entry)
        else:
            dropped.append(entry)
    return kept, dropped


def propose_closeout_entries(workspace: Path, memory_text: str) -> list[str]:
    """Rule-based closeout proposals from recent state-file bullets."""
    proposals: list[str] = []
    memory_lower = memory_text.lower()
    for rel in ("DECISIONS.md", "HANDOFF.md"):
        path = workspace / rel
        if not path.exists():
            continue
        lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
        for line in lines[-30:]:
            if not line.startswith("- "):
                continue
            body = line[2:].strip()
            if len(body) < 20:
                continue
            key = re.sub(r"\s+", " ", body.lower())
            if key in memory_lower:
                continue
            proposals.append(body)
    return proposals[:5]


def propose_updates(workspace: Path) -> dict:
    ensure_memory_layout(workspace)
    mem_path = memory_file(workspace)
    user_path = user_file(workspace)
    mem_text = mem_path.read_text(encoding="utf-8") if mem_path.exists() else ""
    user_text = user_path.read_text(encoding="utf-8") if user_path.exists() else ""

    mem_entries = dedupe_entries(split_entries(mem_text))
    user_entries = dedupe_entries(split_entries(user_text))
    mem_kept, mem_dropped = trim_to_limit(mem_entries, MEMORY_CHAR_LIMIT)
    user_kept, user_dropped = trim_to_limit(user_entries, USER_CHAR_LIMIT, header="# User Profile\n\n")

    closeout = propose_closeout_entries(workspace, mem_text)

    return {
        "drift": detect_drift(workspace),
        "memory_usage": usage_report(mem_text, MEMORY_CHAR_LIMIT),
        "user_usage": usage_report(user_text, USER_CHAR_LIMIT),
        "memory_entries_before": len(mem_entries),
        "memory_entries_after": len(mem_kept),
        "memory_dropped": mem_dropped,
        "user_dropped": user_dropped,
        "memory_text": join_entries(mem_kept).replace("# Memory\n\n", "", 1).strip() if mem_kept else "",
        "memory_output": join_entries(mem_kept),
        "user_output": ("# User Profile\n\n" + ENTRY_SEP.join(user_kept) + "\n") if user_kept else user_text,
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


def apply_report(workspace: Path, report: dict, stage_only: bool) -> list[str]:
    actions: list[str] = []
    mem_path = memory_file(workspace)
    user_path = user_file(workspace)

    if stage_only:
        if report["memory_dropped"] or report["memory_entries_before"] != report["memory_entries_after"]:
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
    mem_path.write_text(report["memory_output"], encoding="utf-8")
    actions.append(f"updated `{mem_path.relative_to(workspace)}`")


    if report["user_dropped"]:
        user_path.write_text(report["user_output"], encoding="utf-8")
        actions.append(f"updated `{user_path.relative_to(workspace)}`")

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Curate bounded product memory files.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--apply", action="store_true", help="Apply curation directly.")
    parser.add_argument("--stage", action="store_true", help="Stage writes for approval instead of applying.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    report = propose_updates(workspace)
    output = workspace / "plan" / "MEMORY_REVIEW.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(workspace, report), encoding="utf-8")

    stage_only = args.stage or not args.apply
    if args.apply or args.stage:
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
        print("Memory over limit — run with --apply or --stage.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
