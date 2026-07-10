#!/usr/bin/env python3
"""Reconcile product-loop state files and report drift."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from workspace_utils import ROOT, resolve_workspace


TARGET_FILES = [
    "MEMORY.md",
    "HANDOFF.md",
    "TASKS.yml",
    "GATES.yml",
    "COMPACT.md",
    "DEPLOYMENT_PLAN.md",
    "plan/PROD-GAP.md",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_next_command(text: str) -> str | None:
    for line in text.splitlines():
        lower = line.lower()
        if "next command" in lower or lower.startswith("/"):
            match = re.search(r"(/[\w-]+)", line)
            if match:
                return match.group(1)
    return None


def extract_active_gate(text: str) -> str | None:
    for line in text.splitlines():
        if "**Active gate" in line or "active gate" in line.lower():
            return line.split(":", 1)[-1].strip().strip("* ")
    return None


def ensure_handoff_pointer(handoff_text: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    updated = handoff_text
    if "COMPACT.md" not in handoff_text:
        updated += (
            "\n"
            f"## {date.today().isoformat()} — Sync note\n\n"
            "- Read `COMPACT.md` and `STATUS.md` before continuing.\n"
        )
        fixes.append("Appended COMPACT.md pointer to HANDOFF.md.")
    return updated, fixes


def ensure_memory_timestamp(memory_text: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    marker = f"## {date.today().isoformat()} — State sync"
    if marker not in memory_text:
        updated = memory_text.rstrip() + (
            "\n\n"
            f"{marker}\n\n"
            "- Loop state files were reconciled by `/sync-loop-state`.\n"
        )
        fixes.append("Appended sync note to MEMORY.md.")
        return updated, fixes
    return memory_text, fixes


def detect_drift(workspace: Path) -> tuple[list[str], list[str]]:
    drift: list[str] = []
    fixes: list[str] = []

    from memory_paths import memory_file

    memory = read_text(memory_file(workspace))
    handoff = read_text(workspace / "HANDOFF.md")
    compact = read_text(workspace / "COMPACT.md")
    current_state = read_text(workspace / "CURRENT_STATE.md")
    tasks = read_text(workspace / "TASKS.yml")
    gates = read_text(workspace / "GATES.yml")

    memory_cmd = extract_next_command(memory)
    handoff_cmd = extract_next_command(handoff)
    compact_cmd = extract_next_command(compact)

    if memory_cmd and handoff_cmd and memory_cmd != handoff_cmd:
        drift.append(f"Next command mismatch: MEMORY suggests `{memory_cmd}`, HANDOFF suggests `{handoff_cmd}`.")

    memory_gate = extract_active_gate(memory) or extract_active_gate(current_state)
    compact_gate = extract_active_gate(compact)
    if memory_gate and compact_gate and memory_gate != compact_gate:
        drift.append(f"Active gate mismatch: current state `{memory_gate}` vs COMPACT `{compact_gate}`.")

    if "blocked" in gates.lower() and handoff_cmd == "/plan-loop":
        drift.append("Gates show blocked status but HANDOFF points to `/plan-loop`.")

    if "status: blocked" in tasks.lower() and handoff_cmd == "/product-develop":
        drift.append("Blocked tasks exist; confirm HANDOFF is routing to the correct unblock work.")

    if not (workspace / "COMPACT.md").exists():
        drift.append("COMPACT.md is missing; run `/compact-loop` after sync if context is long.")

    if not (workspace / "STATUS.md").exists():
        drift.append("STATUS.md is missing; run `/status` for a quick snapshot.")

    updated_handoff, handoff_fixes = ensure_handoff_pointer(handoff)
    if handoff_fixes:
        (workspace / "HANDOFF.md").write_text(updated_handoff, encoding="utf-8")
        fixes.extend(handoff_fixes)

    updated_memory, memory_fixes = ensure_memory_timestamp(memory)
    if memory_fixes:
        memory_file(workspace).write_text(updated_memory, encoding="utf-8")
        fixes.extend(memory_fixes)

    return drift, fixes


def load_template() -> str:
    return (ROOT / "templates" / "sync_loop_state.template.md").read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def bullet(items: list[str]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile loop state files in a product workspace.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    drift, fixes = detect_drift(workspace)

    report = render(
        load_template(),
        {
            "UPDATED_DATE": date.today().isoformat(),
            "WORKSPACE_PATH": str(workspace),
            "TARGET_FILES": bullet([f"`{name}`" for name in TARGET_FILES]),
            "DRIFT_ITEMS": bullet(drift),
            "FIXES_APPLIED": bullet(fixes),
            "NEXT_COMMAND": "/status" if drift else "/loop-engine",
        },
    )

    output = workspace / "SYNC_REPORT.md"
    output.write_text(report, encoding="utf-8")

    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} — Loop state sync\n\n"
            f"- Updated `{output.name}`.\n"
            f"- Drift items: {len(drift)}.\n"
            f"- Fixes applied: {len(fixes)}.\n"
        )

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
