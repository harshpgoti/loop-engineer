#!/usr/bin/env python3
"""Deterministic planning-phase router for the plan-loop orchestrator.

Rules-first (AGENTS.md rule 4): the harness - not the model - decides which
planning phase comes next, from cheap state signals. The orchestrator skill
(`skills/plan-loop/SKILL.md`) reads the emitted `PHASE:` line and loads only the
matching `phases/<name>.md` file (progressive disclosure).

Phases, in loop order:
    grill -> [resolve-doubts whenever a blocking doubt is answerable]
    -> council -> [ultraplan if platform] -> spec-clarify -> spec-checklist
    -> task-compiler
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
    "resolve-doubts": "skills/plan-loop/phases/resolve-doubts.md",
    "task-compiler": "skills/plan-loop/phases/task-compiler.md",
}

# Skills worth loading per phase. The phase files were already progressively
# disclosed; the *skills* were not - all twelve loaded every session, 51KB of them,
# including `revise-plan` (a different command) and `agent-builder` (only relevant
# when the product is an agent). Same contract as `build_phase.PHASE_SKILLS`.
PHASE_SKILLS = {
    "grill": ["skills/research-search/SKILL.md"],
    "council": [],
    "ultraplan": ["skills/tool-orchestrator/SKILL.md"],
    "spec-clarify": ["skills/feature-workflow/SKILL.md"],
    "spec-checklist": ["skills/feature-workflow/SKILL.md"],
    "resolve-doubts": ["skills/research-search/SKILL.md"],
    "task-compiler": ["skills/feature-workflow/SKILL.md"],
}

# Loaded on top of the phase's own list when the workspace signals it.
CONDITIONAL_SKILLS = (
    ("plan/AUTO_AGENT_SKILLS.md", "skills/agent-builder/SKILL.md"),
    ("plan/AUTO_SKILLS.md", "skills/frontend-animation/SKILL.md"),
)


def phase_skills(workspace: Path, phase: str) -> list[str]:
    skills = list(PHASE_SKILLS.get(phase, []))
    for signal, skill in CONDITIONAL_SKILLS:
        if (workspace / signal).exists() and skill not in skills:
            skills.append(skill)
    return skills


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


def _has_open_doubts(workspace: Path) -> bool:
    """True if a *blocking* doubt is still open.

    Was a substring test for `status: open` over the whole file, which fired on any
    open item at all - so a single commercial question explicitly annotated "does not
    block the build" pinned a workspace before `task-compiler` indefinitely. Both of
    this repo's real workspaces were stuck that way. `doubts.has_blocking` reads the
    same file with one parser every command shares.

    Uses the *frontier* - the blocking doubts answerable this round - rather than every
    blocking doubt. A deferred one, or one waiting on an earlier answer, must not pin the
    phase: deferring is the documented way to proceed without an answer.
    """
    try:
        from doubts import frontier, selected_scope

        return bool(frontier(workspace, scope=selected_scope(workspace)))
    except Exception:
        return False


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
    elif _has_open_doubts(workspace):
        # Ahead of the feature spec and of packing the next row. A blocking doubt is a
        # question the plan already knows it cannot answer for itself, and each carries
        # a recorded default as its recommendation - so this is one round of questions,
        # not a stall. Gating it behind "a feature is active" meant a platform could
        # plan every step with the blockers never asked.
        phase, reason = (
            "resolve-doubts",
            "blocking doubts can be answered now - clear them before planning further",
        )
    elif feature and not _checklist_ready(feature):
        # An active feature outranks packing the next map row. The documented loop is
        # "ultraplan one step -> feature spec -> clarify -> checklist -> doubts ->
        # tasks", and packing first stranded the spec: on a four-row platform the
        # router pulled every session back to `ultraplan` until all four packs existed,
        # so `spec-clarify`, `spec-checklist`, `resolve-doubts` and `task-compiler`
        # were unreachable and the spec just written sat untouched.
        phase, reason = "spec-clarify", "active feature spec still has open questions"
    elif platform and _ultraplan_incomplete(workspace):
        # The active feature is finished through its checklist and doubts, so the next
        # row's pack is the next real work. This is what returns the loop to ultraplan
        # after a step has been planned all the way to tasks.
        phase, reason = "ultraplan", "platform scale with an incomplete ultraplan step"
    elif feature:
        phase, reason = "task-compiler", "active feature spec checklist is Ready - compile tasks"
    else:
        phase, reason = "council", "plan initialized, no active feature - council-review before the feature spec"

    pipeline = ["grill"]
    pipeline.append("council")
    if platform:
        pipeline.append("ultraplan")
    pipeline += ["spec-clarify", "spec-checklist", "resolve-doubts", "task-compiler"]

    return {
        "phase": phase,
        "file": PHASE_FILES[phase],
        "skills": phase_skills(workspace, phase),
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
        f"- Skills for this phase: {', '.join(f'`{s}`' for s in result['skills']) or 'none beyond the always-read set'}",
        "- Every other skill stays unread until a phase names it.",
        f"- Pipeline: {' -> '.join(result['pipeline'])}",
        "- Router: `skills/plan-loop/SKILL.md`",
    ]
    return "\n".join(lines)
