#!/usr/bin/env python3
"""Write a quick STATUS.md snapshot for the active product workspace."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from workspace_utils import ROOT, load_config, resolve_workspace
from workspace_utils import console_utf8


STATE_FILES = [
    "main_plan.md",
    "MEMORY.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "CURRENT_STATE.md",
    "HANDOFF.md",
    "COMPACT.md",
    "plan/PROD-GAP.md",
]


def read_text(path: Path, max_chars: int = 3000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n_...truncated_"


def extract_line(text: str, prefix: str, default: str = "TBD") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def find_active_task(tasks_text: str) -> str:
    for line in tasks_text.splitlines():
        lower = line.lower()
        if "status:" in lower and any(token in lower for token in ("in_progress", "active", "doing")):
            return line.strip()
        if lower.startswith("- id:") or lower.startswith("id:"):
            return line.strip()
    return "See `TASKS.yml`."


def find_human_blockers(workspace: Path, prod_gap_text: str) -> list[str]:
    """Blocking doubts, plus the gap report's own human-required section.

    This used to substring-match `- ` bullets for words like "sign" and "account",
    which on a real workspace surfaced the *resolution* text of an already-closed
    doubt and matched "sign" inside "design partner". Blocking doubts are now read
    from the parser, where they carry an id.
    """
    blockers: list[str] = []
    try:
        from doubts import blocking_doubts

        blockers.extend(f"`{d.id}` {d.question or d.title}" for d in blocking_doubts(workspace))
    except Exception:
        pass

    in_section = False
    for line in prod_gap_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            in_section = "human-required" in stripped.lower()
            continue
        if in_section and stripped.startswith("- "):
            blockers.append(stripped[2:])
    return blockers[:8]


def recommend_next_command(main_plan: str, current_state: str, gates: str, tasks: str) -> str:
    if "Status: **UNINITIALIZED**" in main_plan:
        return "/plan-loop"
    if "blocked" in gates.lower():
        if "status: blocked" in tasks.lower():
            return "/product-develop"
        return "/loop-engine"
    if "in_progress" in tasks.lower() or "active" in tasks.lower():
        return "/product-develop"
    if "G-RELEASE-01" in gates and "pass" not in gates.lower():
        return "/release-check"
    return "/loop-engine"


def load_template() -> str:
    path = ROOT / "templates" / "status.template.md"
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def bullet(items: list[str]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def _hierarchy(workspace: Path) -> dict:
    """Sub-product roll-up for the snapshot. Failure-safe - never blocks /status."""
    try:
        from hierarchy_sync import readiness

        return readiness(workspace)
    except Exception:
        return {"lines": [], "blockers": []}


def summarize(workspace: Path) -> str:
    config = load_config()
    current_name = config.get("current")
    workspace_entry = config.get("workspaces", {}).get(current_name or "", {})
    registered_path = workspace_entry.get("path", str(workspace))

    from memory_paths import main_plan_file

    main_plan = read_text(main_plan_file(workspace))
    current_state = read_text(workspace / "CURRENT_STATE.md")
    doubts = read_text(workspace / "DOUBTS.md")
    tasks = read_text(workspace / "TASKS.yml")
    gates = read_text(workspace / "GATES.yml")
    handoff = read_text(workspace / "HANDOFF.md")
    prod_gap = read_text(workspace / "plan" / "PROD-GAP.md")

    product_name = extract_line(main_plan, "- **Name", "Uninitialized")
    phase = extract_line(current_state, "**Phase", "Unknown")
    active_gate = extract_line(current_state, "**Active gate", "Unknown")
    active_task = find_active_task(tasks)
    next_command = recommend_next_command(main_plan, current_state, gates, tasks)
    human_blockers = find_human_blockers(workspace, prod_gap)

    # One parser, whole file. The old regex ran over a 3,000-char excerpt and
    # matched any bullet containing "open" - it reported 3 for a file with 13.
    try:
        from doubts import counts as doubt_counts

        open_doubt_count = doubt_counts(workspace)["open"]
    except Exception:
        open_doubt_count = 0

    hierarchy = _hierarchy(workspace)
    human_blockers.extend(hierarchy["blockers"])

    template = load_template()
    return render(
        template,
        {
            "UPDATED_DATE": date.today().isoformat(),
            "WORKSPACE_PATH": str(workspace),
            "REGISTERED_NAME": current_name or "embedded/current",
            "REGISTERED_PATH": registered_path,
            "PRODUCT_NAME": product_name,
            "PHASE": phase,
            "ACTIVE_GATE": active_gate,
            "ACTIVE_TASK": active_task,
            "NEXT_COMMAND": next_command,
            "OPEN_DOUBTS_COUNT": str(open_doubt_count),
            "HIERARCHY": "\n".join(hierarchy["lines"]) or "- Standalone product (no linked sub-products).",
            "HUMAN_BLOCKERS": bullet(human_blockers),
            "HANDOFF_EXCERPT": handoff or "_No HANDOFF.md yet._",
            "SOURCE_FILES": bullet([f"`{item}`" for item in STATE_FILES]),
        },
    )


def append_session_log(workspace: Path) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} - Status snapshot\n\n"
            "- Updated `STATUS.md`.\n"
        )


def main() -> int:
    console_utf8()
    parser = argparse.ArgumentParser(description="Write STATUS.md for a product workspace.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    output = workspace / "STATUS.md"
    output.write_text(summarize(workspace), encoding="utf-8")
    append_session_log(workspace)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
