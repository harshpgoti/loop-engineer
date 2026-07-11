#!/usr/bin/env python3
"""Deterministic planning-phase router for the plan-loop orchestrator.

Rules-first (AGENTS.md rule 4): the harness - not the model - decides which
planning phase comes next, from cheap state signals. The orchestrator skill
(`skills/plan-loop/SKILL.md`) reads the emitted `PHASE:` line and loads only the
matching `phases/<name>.md` file (progressive disclosure).

Phases, in loop order:
    grill -> council -> [ultraplan if platform] -> spec-clarify -> spec-checklist -> task-compiler
"""
from __future__ import annotations

from pathlib import Path

# Phase name -> phase file, relative to the app's skills dir.
PHASE_FILES = {
    "grill": "skills/plan-loop/phases/grill.md",
    "council": "skills/plan-loop/phases/council.md",
    "ultraplan": "skills/plan-loop/phases/ultraplan.md",
    "spec-clarify": "skills/plan-loop/phases/spec-clarify.md",
    "spec-checklist": "skills/plan-loop/phases/spec-checklist.md",
    "task-compiler": "skills/plan-loop/phases/task-compiler.md",
}


def _is_initialized(workspace: Path) -> bool:
    main_plan = workspace / "plan" / "main_plan.md"
    if not main_plan.exists():
        return False
    try:
        text = main_plan.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "UNINITIALIZED" not in text.upper()


def _is_platform(workspace: Path) -> bool:
    try:
        from plan_paths import SCALE_PLATFORM, scale_file

        path = scale_file(workspace)
        if not path.exists():
            return False
        return SCALE_PLATFORM in path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return False


def _ultraplan_incomplete(workspace: Path) -> bool:
    try:
        from ultraplan_harness import find_next_incomplete

        return find_next_incomplete(workspace) is not None
    except Exception:
        return False


def _active_feature(workspace: Path) -> dict | None:
    try:
        from feature_paths import read_active_feature

        return read_active_feature(workspace)
    except Exception:
        return None


def _checklist_ready(feature: dict | None) -> bool:
    if not feature:
        return False
    abs_path = feature.get("abs_path")
    if not abs_path:
        return False
    checklist = Path(abs_path) / "spec-checklist.md"
    if not checklist.exists():
        return False
    text = checklist.read_text(encoding="utf-8", errors="ignore").lower()
    if "needs clarify" in text:
        return False
    return "ready for feature-plan" in text or "ready for feature plan" in text


def compute_plan_phase(workspace: Path) -> dict:
    """Return {phase, file, pipeline, reason} for the active workspace."""
    initialized = _is_initialized(workspace)
    platform = _is_platform(workspace)
    feature = _active_feature(workspace)

    if not initialized:
        phase, reason = "grill", "product plan is UNINITIALIZED - grill product inputs first"
    elif platform and _ultraplan_incomplete(workspace):
        phase, reason = "ultraplan", "platform scale with an incomplete ultraplan step"
    elif feature:
        if _checklist_ready(feature):
            phase, reason = "task-compiler", "active feature spec checklist is Ready - compile tasks"
        else:
            phase, reason = "spec-clarify", "active feature spec still has open questions"
    else:
        phase, reason = "council", "plan initialized, no active feature - council-review before the feature spec"

    pipeline = ["grill", "council"]
    if platform:
        pipeline.append("ultraplan")
    pipeline += ["spec-clarify", "spec-checklist", "task-compiler"]

    return {
        "phase": phase,
        "file": PHASE_FILES[phase],
        "pipeline": pipeline,
        "reason": reason,
    }


def render_phase_block(workspace: Path, *, heading: str = "## Plan phase") -> str:
    """Markdown block for PLAN_BOOTSTRAP.md / SESSION_MANIFEST.md."""
    result = compute_plan_phase(workspace)
    lines = [
        heading,
        "",
        f"PHASE: {result['phase']}",
        "",
        f"- Reason: {result['reason']}",
        f"- Load only: `{result['file']}` (progressive disclosure - do not preload all phases)",
        f"- Pipeline: {' -> '.join(result['pipeline'])}",
        "- Router: `skills/plan-loop/SKILL.md`",
    ]
    return "\n".join(lines)
