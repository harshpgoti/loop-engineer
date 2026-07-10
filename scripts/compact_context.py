#!/usr/bin/env python3
"""Create a durable COMPACT.md summary for long-running product loops."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from memory_paths import memory_file, state_db
from session_store import init_db, log_session
from workspace_utils import resolve_workspace


ROOT = Path(__file__).resolve().parents[1]

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


def read_excerpt(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return f"_Missing: {path.name}_"
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n_...truncated in compact summary_"


def extract_line(text: str, prefix: str, default: str = "TBD") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def load_template() -> str:
    template_path = ROOT / "templates" / "compact.template.md"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "# Compact Context\n\n{{WHAT_NOW}}\n"


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


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

    template = load_template()
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


def append_session_log(workspace: Path) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} — Context compacted\n\n"
            "- Updated `COMPACT.md`.\n"
            "- Next agent should read `COMPACT.md` and `HANDOFF.md` first.\n"
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
    content = summarize_workspace(workspace)
    output = workspace / "COMPACT.md"
    output.write_text(content, encoding="utf-8")
    append_session_log(workspace)

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
