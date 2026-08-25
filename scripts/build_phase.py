#!/usr/bin/env python3
"""Deterministic build-phase router for /develop-product.

Planning already works this way: `plan_phase.py` computes which phase applies and
the skill loads exactly one `phases/*.md`. Development did not - its `Read First`
listed 32 items, 27 of them unconditional, and the five conditions were prose the
model had to evaluate for itself ("when requirements blocked"). So a session that
only needed to write a test still pulled in the agent-builder, deployment-plan and
security-compliance skills.

Same contract as the planning router: cheap state signals, rules first (`AGENTS.md`
non-negotiable #4), one phase file loaded.

Phases, in loop order:
    scaffold -> implement -> test -> converge -> release -> deploy
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PHASE_FILES = {
    "scaffold": "skills/develop-product/phases/scaffold.md",
    "implement": "skills/develop-product/phases/implement.md",
    "test": "skills/develop-product/phases/test.md",
    "converge": "skills/develop-product/phases/converge.md",
    "evaluate": "skills/eval-loop/SKILL.md",
    "release": "skills/develop-product/phases/release.md",
    "deploy": "skills/develop-product/phases/deploy.md",
}

# Skills worth loading per phase. Everything else stays unread until its phase.
PHASE_SKILLS = {
    "scaffold": ["skills/implementation-planner/SKILL.md", "skills/tool-orchestrator/SKILL.md"],
    "implement": ["skills/implementation-planner/SKILL.md", "skills/feature-workflow/SKILL.md"],
    "test": ["skills/qa-validation/SKILL.md"],
    "converge": ["skills/feature-converge/SKILL.md", "skills/code-reviewer/SKILL.md"],
    "evaluate": ["skills/eval-loop/SKILL.md"],
    "release": [
        "skills/security-compliance/SKILL.md",
        "skills/prod-gap/SKILL.md",
        "skills/deployment-plan/SKILL.md",
        "skills/cicd-release/SKILL.md",
    ],
    "deploy": [
        "skills/deploy/SKILL.md",
        "skills/deployment-plan/SKILL.md",
        "skills/cicd-release/SKILL.md",
        "skills/security-compliance/SKILL.md",
    ],
}

DONE = ("completed", "done", "complete")


def _tasks(workspace: Path) -> list[dict]:
    """The tasks this build should choose from.

    Scope-filtered when a sub-product is selected. Reading only the root `TASKS.yml`
    made `/develop-product work on payer forms` pick a *platform* task, because the
    scope's own tasks were never loaded - the session would announce one sub-product
    and then build something else entirely.

    Platform tasks stay in the list on purpose: platform work gates scope work, so a
    scope that could not see it would report itself unblocked when it is not.
    """
    try:
        import scope_paths as sp
        import scope_state

        if sp.list_scopes(workspace):
            active = sp.resolve(workspace)
            slug = active.scope.slug if active.scope is not None else None
            return scope_state.load_tasks(workspace, scope=slug)
    except Exception:  # noqa: BLE001 - a workspace without scopes reads as it always did
        pass
    try:
        from task_context import parse_tasks

        return parse_tasks(workspace)
    except Exception:
        return []


def _active(workspace: Path, tasks: list[dict]) -> dict | None:
    """The task to build now.

    When a sub-product is selected, its own tasks are considered first, and platform
    tasks only once it has nothing available. Otherwise the choice falls out of file
    order - a session that announced `payer-forms` would pick a platform task simply
    because platform tasks are listed first, which is not what the user asked for.
    """
    try:
        from task_context import active_task
    except Exception:
        return None

    try:
        import scope_paths as sp

        active = sp.resolve(workspace)
        if active.scope is not None:
            mine = [t for t in tasks if t.get("scope") == active.scope.slug]
            chosen = active_task(mine) if mine else None
            if chosen is not None:
                return chosen
    except Exception:  # noqa: BLE001
        pass

    try:
        return active_task(tasks)
    except Exception:
        return None


def _scope_code_roots(workspace: Path) -> tuple[Path | None, list[Path]]:
    """(active scope's code dir, every scope's code dir) - both may be empty.

    In a unified workspace the product's code lives under each scope's `code_dir`, not
    at the root. Looking only at the root reports "no source tree" for a platform whose
    sub-products are all built, which routes the build to `scaffold` - telling the user
    to create a repo that already exists, on top of code that already exists.
    """
    try:
        import scope_paths as sp

        scopes = sp.list_scopes(workspace)
        if not scopes:
            return None, []
        active = sp.resolve(workspace)
        active_root = None
        if active.scope is not None:
            path = active.scope.code_path(workspace)
            active_root = path if path and path.is_dir() else None
        roots = [p for p in (s.code_path(workspace) for s in scopes) if p and p.is_dir()]
        return active_root, roots
    except Exception:  # noqa: BLE001 - a workspace without scopes behaves as before
        return None, []


def _has_source_tree(workspace: Path) -> bool:
    try:
        from source_tree_scan import find_source_root
    except Exception:
        return False

    active_root, roots = _scope_code_roots(workspace)
    if active_root is not None:
        # A scope is selected: its own tree is the one that decides. Another scope
        # being built says nothing about whether this one has been scaffolded.
        return find_source_root(active_root) is not None
    try:
        if find_source_root(workspace) is not None:
            return True
    except Exception:
        return False
    # No scope selected and no root tree: if any sub-product is already built, this is
    # not a fresh product. Scaffolding here would be scaffolding over existing work.
    return any(find_source_root(root) is not None for root in roots)


def _release_gate_open(workspace: Path) -> bool:
    path = workspace / "GATES.yml"
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return "G-RELEASE-01" in text and "passed" not in text.split("G-RELEASE-01", 1)[1][:200]


def _evals_needed(workspace: Path) -> str:
    """Why the evals must run before anything else, or "" when they need not.

    Deterministic on purpose. The previous trigger was a line of prose telling the
    agent to run evals "after any change to agent behaviour", which asks the model to
    judge whether behaviour changed - exactly the kind of decision this harness
    computes instead. A recorded run carries a fingerprint of the behaviour surface;
    if that surface has moved, the score no longer describes the current agent.
    """
    try:
        import eval_suite
    except Exception:
        return ""
    if not eval_suite.discover_cases(workspace):
        return ""  # no suite: nothing to be stale about

    change = eval_suite.regressions(workspace)
    if change.get("regressed"):
        return f"{len(change['regressed'])} eval case(s) regressed"
    drift = eval_suite.behaviour_changed(workspace)
    if drift["stale"]:
        return drift["reason"]
    gate = eval_suite.gate_status(workspace)
    if not gate["ok"] and gate.get("score") is None:
        return "eval cases exist but no run has been recorded"
    return ""



def _deploy_requested(workspace: Path) -> str:
    """Why this build should be deploying rather than closing out, or "" when it should not.

    Deployment is the one phase that spends money and touches an account, so it is never
    entered by inference from "the build looks done". It needs a stated target and an
    unfinished environment: a `DEPLOYMENT_PLAN.md` naming a real provider, and at least
    one environment in it with nothing recorded in `plan/CLOUD_INVENTORY.md`.

    A product that has already deployed every environment its plan names falls through to
    converge, which is correct - re-deploying is a request, not a default.
    """
    plan = workspace / "DEPLOYMENT_PLAN.md"
    if not plan.is_file():
        return ""
    try:
        text = plan.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    match = re.search(r"^\|\s*Cloud provider\s*\|\s*([^|]+)\|", text, re.M)
    provider = (match.group(1).strip() if match else "").strip("`*_ ")
    if not provider or provider.upper() in {"TBD", "N/A", "-", "NONE"}:
        return ""

    try:
        import cloud_inventory

        recorded = {r.env for r in cloud_inventory.parse(workspace) if r.live}
    except Exception:  # noqa: BLE001 - no inventory yet is the normal first deploy
        recorded = set()

    wanted = {env for env in cloud_inventory_environments(text) if env not in recorded}
    if not wanted:
        return ""
    return (
        f"deployment target is {provider} and no resources are recorded for "
        + ", ".join(sorted(wanted))
    )


def cloud_inventory_environments(plan_text: str) -> set[str]:
    """Environments the deployment plan names. Defaults to dev - the safe one to start in."""
    found = {
        env
        for env in ("dev", "staging", "prod", "production")
        if re.search(rf"(?<![a-z]){env}(?![a-z])", plan_text, re.I)
    }
    found = {"prod" if e == "production" else e for e in found}
    return found or {"dev"}


def compute_build_phase(workspace: Path) -> dict:
    """Return {phase, file, skills, pipeline, reason} for the active workspace."""
    tasks = _tasks(workspace)
    task = _active(workspace, tasks)
    remaining = [t for t in tasks if str(t.get("status", "")).lower() not in DONE]

    evals = _evals_needed(workspace)
    if evals and _has_source_tree(workspace):
        # Ahead of implement and release both: building on an unscored change, or on
        # a regression, means finding out later and unpicking more.
        return {
            "phase": "evaluate",
            "file": PHASE_FILES["evaluate"],
            "skills": PHASE_SKILLS["evaluate"],
            "pipeline": list(PHASE_FILES),
            "reason": evals,
            "task": (task or {}).get("id"),
        }

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
        elif _deploy_requested(workspace):
            phase, reason = "deploy", _deploy_requested(workspace)
        else:
            phase, reason = "converge", "no task outstanding - verify the build matches the spec"
    else:
        phase_hint = str(task.get("phase", "")).lower()
        status = str(task.get("status", "")).lower()
        if "deploy" in phase_hint:
            phase, reason = "deploy", f"{task['id']} is deployment work"
        elif "release" in phase_hint:
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
        "- Router: `skills/develop-product/SKILL.md`",
    ]
    if result["task"]:
        lines.append(f"- Active task: `{result['task']}` - detail in `plan/BUILD_CONTEXT.md`")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

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
