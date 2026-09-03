#!/usr/bin/env python3
"""Create a durable COMPACT.md summary for long-running product loops."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from memory_paths import memory_file, state_db
from session_store import init_db, log_session
from workspace_utils import append_session_log, extract_line, load_template, render_template as render, resolve_workspace

STATE_FILES = [
    "MEMORY.md",
    "DOUBTS.md",
    "CURRENT_STATE.md",
    "main_plan.md",
    "TASKS.yml",
    "GATES.yml",
    "DECISIONS.md",
    "EVIDENCE_LOG.md",
    "HANDOFF.md",
]


# COMPACT.md is read at the start of every session, so it is a standing cost on
# every command. `memories/MEMORY.md` has had a character budget from the start;
# this file had none and grew to be the single largest thing in the read order.
COMPACT_CHAR_LIMIT = 8000
EXCERPT_CHAR_LIMIT = 1200


def read_excerpt(path: Path, max_chars: int = EXCERPT_CHAR_LIMIT) -> str:
    if not path.exists():
        return f"_Missing: {path.name}_"
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + f"\n\n_...truncated - full text in `{path.name}`_"


def enforce_limit(content: str, limit: int = COMPACT_CHAR_LIMIT) -> str:
    """Trim from the end, on a section boundary, so the summary stays readable.

    Earlier sections are the durable ones (product, phase, active task); the tail is
    per-file excerpts that can always be read from the file itself.
    """
    if len(content) <= limit:
        return content

    sections = content.split("\n## ")
    kept, total = [sections[0]], len(sections[0])
    for section in sections[1:]:
        chunk = "\n## " + section
        if total + len(chunk) > limit:
            break
        kept.append(section)
        total += len(chunk)

    trimmed = kept[0] + "".join("\n## " + s for s in kept[1:])
    dropped = len(sections) - len(kept)
    return trimmed.rstrip() + (
        f"\n\n_...{dropped} section(s) trimmed to stay under {limit:,} chars. "
        "Read the source files directly when you need them._\n"
    )


def summarize_workspace(workspace: Path) -> str:
    from memory_paths import main_plan_file, memory_file

    memory = read_excerpt(memory_file(workspace), 2500)
    current_state = read_excerpt(workspace / "CURRENT_STATE.md", 2000)
    main_plan = read_excerpt(main_plan_file(workspace), 2500)
    doubts = read_excerpt(workspace / "DOUBTS.md", 2500)
    decisions = read_excerpt(workspace / "DECISIONS.md", 2500)
    evidence = read_excerpt(workspace / "EVIDENCE_LOG.md", 2500)
    handoff = read_excerpt(workspace / "HANDOFF.md", 2500)
    tasks = read_excerpt(workspace / "TASKS.yml", 2500)
    gates = read_excerpt(workspace / "GATES.yml", 2500)

    product_name = extract_line(main_plan, "- **Name", "Uninitialized")
    phase = extract_line(current_state, "**Phase", "Unknown")
    active_gate = extract_line(current_state, "**Active gate", "Unknown")

    important_files = "\n".join(f"- `{name}`" for name in STATE_FILES)

    template = load_template("compact.template.md", "# Compact Context\n\n{{WHAT_NOW}}\n")
    return render(
        template,
        {
            "UPDATED_DATE": date.today().isoformat(),
            "PRODUCT_NAME": product_name,
            "PHASE": phase,
            "ACTIVE_GATE": active_gate,
            "ACTIVE_TASK": tasks,
            "WHAT_HAPPENED": memory,
            "WHAT_NOW": current_state + "\n\n" + main_plan,
            "OPEN_DOUBTS": doubts,
            "DECISIONS": decisions,
            "EVIDENCE_STATUS": evidence,
            "IMPORTANT_FILES": important_files,
            "DO_NOT_DO": "Follow `HANDOFF.md` and `GATES.yml`. Do not invent missing product details.",
            "NEXT_ACTION": handoff,
            "NEXT_COMMAND": "/loop-engine",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create COMPACT.md for a product workspace.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Product workspace where state files live. Defaults to registered current workspace or current directory.",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    content = enforce_limit(summarize_workspace(workspace))
    output = workspace / "COMPACT.md"
    output.write_text(content, encoding="utf-8")
    append_session_log(
        workspace,
        "Context compacted",
        ["Updated `COMPACT.md`.", "Next agent should read `COMPACT.md` and `HANDOFF.md` first."],
    )

    db = state_db(workspace)
    init_db(db)
    memory_path = memory_file(workspace)
    log_session(
        db,
        workspace=str(workspace),
        command="/compact-loop",
        title="Context compacted",
        body=f"Updated COMPACT.md. Canonical memory: {memory_path.name}",
        tags="compact memory",
    )
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
