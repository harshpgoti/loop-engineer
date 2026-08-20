#!/usr/bin/env python3
"""Deterministic build-phase router for /product-develop.

Planning already works this way: `plan_phase.py` computes which phase applies and
the skill loads exactly one `phases/*.md`. Development did not - its `Read First`
listed 32 items, 27 of them unconditional, and the five conditions were prose the
model had to evaluate for itself ("when requirements blocked"). So a session that
only needed to write a test still pulled in the agent-builder, deployment-plan and
security-compliance skills.

Same contract as the planning router: cheap state signals, rules first (`AGENTS.md`
non-negotiable #4), one phase file loaded.

Phases, in loop order:
    scaffold -> implement -> test -> converge -> release
"""

from __future__ import annotations

import argparse
from pathlib import Path

PHASE_FILES = {
    "scaffold": "skills/product-develop/phases/scaffold.md",
    "implement": "skills/product-develop/phases/implement.md",
    "test": "skills/product-develop/phases/test.md",
    "converge": "skills/product-develop/phases/converge.md",
    "release": "skills/product-develop/phases/release.md",
}

# Skills worth loading per phase. Everything else stays unread until its phase.
PHASE_SKILLS = {
    "scaffold": ["skills/implementation-planner/SKILL.md", "skills/tool-orchestrator/SKILL.md"],
    "implement": ["skills/implementation-planner/SKILL.md", "skills/feature-workflow/SKILL.md"],
    "test": ["skills/qa-validation/SKILL.md"],
    "converge": ["skills/feature-converge/SKILL.md", "skills/code-reviewer/SKILL.md"],
    "release": [
        "skills/security-compliance/SKILL.md",
        "skills/prod-gap/SKILL.md",
        "skills/deployment-plan/SKILL.md",
        "skills/cicd-release/SKILL.md",
    ],
}

DONE = ("completed", "done", "complete")


def _tasks(workspace: Path) -> list[dict]:
    try:
        from task_context import parse_tasks

        return parse_tasks(workspace)
    except Exception:
        return []


def _active(workspace: Path, tasks: list[dict]) -> dict | None:
    try:
        from task_context import active_task

        return active_task(tasks)
    except Exception:
        return None


def _has_source_tree(workspace: Path) -> bool:
    try:
        from source_tree_scan import find_source_root

        return find_source_root(workspace) is not None
    except Exception:
        return False


def _release_gate_open(workspace: Path) -> bool:
    path = workspace / "GATES.yml"
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "G-RELEASE-01" in text and "passed" not in text.split("G-RELEASE-01", 1)[1][:200]


def compute_build_phase(workspace: Path) -> dict:
    """Return {phase, file, skills, pipeline, reason} for the active workspace."""
    tasks = _tasks(workspace)
    task = _active(workspace, tasks)
    remaining = [t for t in tasks if str(t.get("status", "")).lower() not in DONE]

    if not _has_source_tree(workspace):
        phase, reason = "scaffold", "no product source tree yet - scaffold the repo before implementing"
    elif task is None:
        if remaining:
            phase, reason = (
                "implement",
                "no task is unblocked - clear a dependency or a gate before continuing",
            )
        elif _release_gate_open(workspace):
            phase, reason = "release", "all tasks complete and the release gate is still open"
        else:
            phase, reason = "converge", "no task outstanding - verify the build matches the spec"
    else:
        phase_hint = str(task.get("phase", "")).lower()
        status = str(task.get("status", "")).lower()
        if "release" in phase_hint or "deploy" in phase_hint:
            phase, reason = "release", f"{task['id']} is release-phase work"
        elif "test" in phase_hint or "qa" in phase_hint:
            phase, reason = "test", f"{task['id']} is a QA task"
        elif status in ("review", "verifying"):
            phase, reason = "converge", f"{task['id']} is built and awaiting verification"
        else:
            phase, reason = "implement", f"{task['id']} is the active build task"

    return {
        "phase": phase,
        "file": PHASE_FILES[phase],
        "skills": PHASE_SKILLS[phase],
        "pipeline": list(PHASE_FILES),
        "reason": reason,
        "task": task.get("id") if task else None,
    }


def render_phase_block(workspace: Path, *, heading: str = "## Build phase") -> str:
    """Markdown block for plan/SESSION_MANIFEST.md."""
    result = compute_build_phase(workspace)
    lines = [
        heading,
        "",
        f"BUILD PHASE: {result['phase']}",
        "",
        f"- Reason: {result['reason']}",
        f"- Load only: `{result['file']}` (progressive disclosure - do not preload all phases)",
        f"- Skills for this phase: {', '.join(f'`{s}`' for s in result['skills'])}",
        "- Everything else in `skills/` stays unread until its phase.",
        f"- Pipeline: {' -> '.join(result['pipeline'])}",
        "- Router: `skills/product-develop/SKILL.md`",
    ]
    if result["task"]:
        lines.append(f"- Active task: `{result['task']}` - detail in `plan/BUILD_CONTEXT.md`")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import resolve_workspace

    parser = argparse.ArgumentParser(description="Which development phase applies to this workspace.")
    parser.add_argument("--workspace", default=None)
    args = parser.parse_args()

    result = compute_build_phase(resolve_workspace(args.workspace))
    print(f"BUILD PHASE: {result['phase']}")
    print(f"  reason: {result['reason']}")
    print(f"  file:   {result['file']}")
    print(f"  skills: {', '.join(result['skills'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
