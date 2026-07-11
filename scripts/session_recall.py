#!/usr/bin/env python3
"""Recall relevant past sessions at loop start and write plan/SESSION_RECALL.md."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from memory_paths import state_db
from session_store import init_db, log_session, recent_sessions, search_sessions
from workspace_utils import resolve_workspace


def extract_keywords(workspace: Path) -> list[str]:
    from memory_paths import main_plan_file

    keywords: list[str] = []
    for path in (main_plan_file(workspace), workspace / "CURRENT_STATE.md", workspace / "HANDOFF.md"):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if "**Name" in line or "**Active" in line or "**Phase" in line:
                value = line.split(":", 1)[-1].strip().strip("* ")
                if value and value.upper() != "TBD":
                    keywords.extend(value.split())
    cleaned = []
    for word in keywords:
        token = re.sub(r"[^a-zA-Z0-9_-]", "", word)
        if len(token) >= 3:
            cleaned.append(token)
    return list(dict.fromkeys(cleaned))[:8]


def build_query(keywords: list[str]) -> str:
    if not keywords:
        return "plan OR develop OR deployment OR gate"
    safe: list[str] = []
    for kw in keywords:
        token = re.sub(r'[^a-zA-Z0-9_-]', '', kw)
        if len(token) >= 3:
            safe.append(f'"{token}"')
    if not safe:
        return "plan OR develop OR deployment OR gate"
    return " OR ".join(safe)


def render_recall(workspace: Path, hits: list[dict]) -> str:
    lines = [
        "# Session Recall",
        "",
        f"**Updated:** {date.today().isoformat()}",
        "",
        "Auto-generated from `state.db` at loop start. Reuse prior decisions; do not re-ask unless the user wants to change them.",
        "",
    ]
    if not hits:
        lines.append("_No relevant past sessions found yet._")
        return "\n".join(lines) + "\n"

    for row in hits:
        lines.append(f"## {row.get('created_at', 'unknown')} - {row.get('title', 'session')}")
        lines.append("")
        if row.get("command"):
            lines.append(f"- **Command:** `{row['command']}`")
        excerpt = (row.get("body") or "").strip().replace("\n", " ")
        if len(excerpt) > 400:
            excerpt = excerpt[:400].rstrip() + "..."
        lines.append(f"- **Excerpt:** {excerpt}")
        lines.append("")
    return "\n".join(lines) + "\n"


def append_handoff_pointer(workspace: Path) -> None:
    handoff = workspace / "HANDOFF.md"
    if not handoff.exists():
        handoff.write_text("# Handoff\n\n", encoding="utf-8")
    note = (
        f"\n## {date.today().isoformat()} - Session recall refreshed\n\n"
        "- Read `plan/SESSION_RECALL.md` for relevant past loop decisions.\n"
    )
    if "SESSION_RECALL.md" in handoff.read_text(encoding="utf-8", errors="ignore"):
        return
    with handoff.open("a", encoding="utf-8") as handle:
        handle.write(note)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recall relevant past sessions into plan/SESSION_RECALL.md.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--query", default=None, help="Override FTS query.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    db = state_db(workspace)
    init_db(db)

    keywords = extract_keywords(workspace)
    query = args.query or build_query(keywords)
    hits = search_sessions(db, query, limit=args.limit)
    if not hits:
        hits = recent_sessions(db, limit=args.limit)

    output = workspace / "plan" / "SESSION_RECALL.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_recall(workspace, hits), encoding="utf-8")
    append_handoff_pointer(workspace)

    db = state_db(workspace)
    init_db(db)
    log_session(
        db,
        workspace=str(workspace),
        command="/session-recall",
        title="Session recall refreshed",
        body=f"query={query!r}; hits={len(hits)}",
        tags="recall session",
    )

    print(f"Wrote {output} ({len(hits)} hit(s), query={query!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
