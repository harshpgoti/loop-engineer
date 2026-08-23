#!/usr/bin/env python3
"""Validate the Loop Engineering OS template before publishing.

This script intentionally uses only the Python standard library so it works in
fresh clones and direct agent environments.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "AGENTS.md",
    "README.md",
    ".gitignore",
    "loop.config.example.yml",
    "CURSOR.md",
    "CLAUDE.md",
    "CODEX.md",
    "OPENCODE.md",
    "GROK.md",
    "commands/setup-loop-engine.md",
    "commands/plan-loop.md",
    "commands/revise-plan.md",
    "commands/ask-loop.md",
    "commands/product-develop.md",
    "commands/loop-engine.md",
    "commands/prod-gap.md",
    "commands/status.md",
    "commands/doctor.md",
    "commands/sync-loop-state.md",
    "commands/release-check.md",
    "commands/deployment-plan.md",
    "commands/compact-loop.md",
    "commands/session-recall.md",
    "commands/memory-review.md",
    "commands/migrate-import.md",
    "commands/session-start.md",
    "commands/session-end.md",
    "commands/frontend-animation.md",
    "commands/feature-new.md",
    "commands/spec-clarify.md",
    "commands/spec-checklist.md",
    "commands/resolve-doubts.md",
    "commands/feature-converge.md",
    "commands/product-tree.md",
    "commands/eval-loop.md",
    "commands/ultraplan-loop.md",
    "commands/upgrade-loop-engineer.md",
    "skills/setup-loop-engine/SKILL.md",
    "skills/plan-loop/SKILL.md",
    "skills/revise-plan/SKILL.md",
    "skills/ask-loop/SKILL.md",
    "skills/product-develop/SKILL.md",
    "skills/loop-engine/SKILL.md",
    "skills/prod-gap/SKILL.md",
    "skills/status/SKILL.md",
    "skills/doctor/SKILL.md",
    "skills/sync-loop-state/SKILL.md",
    "skills/release-check/SKILL.md",
    "skills/deployment-plan/SKILL.md",
    "skills/compact-loop/SKILL.md",
    "skills/session-recall/SKILL.md",
    "skills/memory-review/SKILL.md",
    "skills/migrate-import/SKILL.md",
    "skills/frontend-animation/SKILL.md",
    "skills/session-lifecycle/SKILL.md",
    "skills/feature-workflow/SKILL.md",
    "skills/plan-loop/phases/spec-clarify.md",
    "skills/plan-loop/phases/spec-checklist.md",
    "skills/plan-loop/phases/resolve-doubts.md",
    "skills/feature-converge/SKILL.md",
    "skills/plan-loop/phases/ultraplan.md",
    "skills/frontend-animation/references/ui-motion.md",
    "skills/frontend-animation/references/gsap-animation.md",
    "skills/frontend-animation/references/3d-rendering.md",
    "skills/frontend-animation/references/modern-web-design.md",
    "skills/frontend-animation/references/motion-reference.md",
    "skills/frontend-animation/references/3d-reference.md",
    "skills/frontend-animation/references/design-patterns.md",
    "skills/frontend-animation/references/quality-checklists.md",
    "skills/frontend-animation/examples/motion-patterns.md",
    "skills/upgrade-loop-engineer/SKILL.md",
    "skills/plan-loop/phases/council.md",
    "skills/plan-loop/phases/task-compiler.md",
    "skills/implementation-planner/SKILL.md",
    "skills/code-reviewer/SKILL.md",
    "templates/main_plan.template.md",
    "templates/step_plan.template.md",
    "templates/prd.template.md",
    "templates/adr.template.md",
    "templates/risks.template.md",
    "templates/metrics.template.md",
    "templates/acceptance_criteria.template.md",
    "templates/test_plan.template.md",
    "templates/prod_gap.template.md",
    "templates/status.template.md",
    "templates/doctor.template.md",
    "templates/sync_loop_state.template.md",
    "templates/release_check.template.md",
    "templates/deployment_plan.template.md",
    "templates/USER.template.md",
    "templates/SOUL.template.md",
    "templates/CONTEXT.template.md",
    "templates/session_recall.template.md",
    "templates/memory_review.template.md",
    "templates/plan_deployment_questions.md",
    "templates/compact.template.md",
    "templates/starter/docs/ACCEPTANCE_CRITERIA.md",
    "templates/starter/docs/TEST_PLAN.md",
    "templates/starter/docs/interview_script.md",
    "docs/PROCESS.md",
    "docs/UPGRADE.md",
    "docs/DATA_LAYOUT.md",
    "docs/WORKSPACES.md",
    "docs/FRONTEND_ANIMATION.md",
    "templates/feature_spec.template.md",
    "templates/feature_plan.template.md",
    "templates/feature_tasks.template.md",
    "templates/feature_clarifications.template.md",
    "templates/feature_research.template.md",
    "templates/feature_spec_checklist.template.md",
    "templates/product_map.template.md",
    "templates/subproducts.template.md",
    "skills/product-tree/SKILL.md",
    "skills/eval-loop/SKILL.md",
    "skills/plan-loop/phases/hierarchy.md",
    "scripts/workspace_tree.py",
    "scripts/hierarchy_drift.py",
    "scripts/dependency_ledger.py",
    "scripts/graph_index.py",
    "scripts/graph_schema.py",
    "scripts/evidence_review.py",
    "scripts/eval_suite.py",
    "scripts/task_context.py",
    "scripts/freshness.py",
    "scripts/hierarchy_sync.py",
    "scripts/subproducts_report.py",
    "scripts/parent_context.py",
    "docs/PRODUCT_HIERARCHY.md",
    "templates/ultraplan_overview.template.md",
    "templates/ultraplan_prd.template.md",
    "templates/ultraplan_architecture.template.md",
    "templates/ultraplan_agents.template.md",
    "templates/ultraplan_data.template.md",
    "templates/ultraplan_integrations.template.md",
    "templates/ultraplan_risks.template.md",
    "templates/ultraplan_acceptance.template.md",
    "docs/FEATURE_WORKFLOW.md",
    "docs/ULTRAPLAN.md",
    "docs/SESSION_LIFECYCLE.md",
    "migrations/README.md",
    "migrations/001_add_compact.py",
    "migrations/002_add_prod_gap.py",
    "migrations/003_add_release_check.py",
    "migrations/004_add_status_doctor_sync.py",
    "migrations/005_add_deployment_plan.py",
    "migrations/006_memory_layout.py",
    "migrations/007_session_bootstrap.py",
    "migrations/008_organize_memory_layout.py",
    "templates/starter/.loop-workspace-version",
    "evals/plan_quality_rubric.md",
    "evals/development_quality_rubric.md",
    "scripts/setup_loop_engine.py",
    "scripts/setup_options.py",
    "scripts/workspace_resolver.py",
    "scripts/init_product.py",
    "scripts/workspace_utils.py",
    "scripts/workspace_registry.py",
    "scripts/prod_gap.py",
    "scripts/source_tree_scan.py",
    "scripts/detect_workspace.py",
    "scripts/status.py",
    "scripts/doctor.py",
    "scripts/sync_loop_state.py",
    "scripts/release_check.py",
    "scripts/deployment_plan.py",
    "scripts/deployment_topics.py",
    "scripts/migrate_workspace.py",
    "scripts/loop_home.py",
    "scripts/memory_paths.py",
    "scripts/session_store.py",
    "scripts/session_search.py",
    "scripts/migrate_import.py",
    "scripts/import_scanner.py",
    "scripts/frontend_skill_router.py",
    "scripts/session_lifecycle.py",
    "scripts/feature_paths.py",
    "scripts/new_feature.py",
    "scripts/feature_converge.py",
    "scripts/plan_paths.py",
    "scripts/plan_scale.py",
    "scripts/plan_extract.py",
    "scripts/plan_idea.py",
    "scripts/ultraplan_harness.py",
    "scripts/loop_update.py",
    "scripts/loop_cli.py",
    "scripts/install_skills.py",
    "scripts/auto_update.py",
    "scripts/team_init.py",
    "docs/DISTRIBUTION.md",
    "docs/CONTINUATION.md",
    "scripts/memory_curator.py",
    "scripts/session_recall.py",
    "scripts/skill_resolver.py",
    "scripts/pending_writes.py",
    "loop.cmd",
    "loop",
    "install.sh",
    "install.ps1",
    "scripts/compact_context.py",
    "scripts/upgrade_loop_engineer.py",
    "scripts/validate_outputs.py",
    "templates/starter/COMPACT.md",
    "templates/starter/plan/main_plan.md",
    "templates/starter/plan/README.md",
    "templates/starter/DOUBTS.md",
    "templates/starter/TASKS.yml",
    "templates/starter/GATES.yml",
    "templates/starter/HANDOFF.md",
    "templates/starter/CURRENT_STATE.md",
    "templates/starter/DECISIONS.md",
    "templates/starter/EVIDENCE_LOG.md",
    "templates/starter/.ai/SESSION_LOG.md",
    "templates/MEMORY.template.md",
]

# Product-specific terms should not appear in the open-source template.
# Keep the default list empty so this repo stays product-neutral. Maintainers
# can create a local `.template-banned-terms` file with one regex per line.
BANNED_PATTERNS: list[str] = []

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tmp"}

FEATURE_WIRING = [
    ("AGENTS.md", "/feature-new"),
    ("AGENTS.md", "/feature-converge"),
    ("commands/plan-loop.md", "PLAN_BOOTSTRAP"),
    ("commands/plan-loop.md", "loop plan-loop"),
    ("commands/loop-engine.md", "PLAN_BOOTSTRAP"),
    ("skills/plan-loop/SKILL.md", "PLAN_BOOTSTRAP"),
    ("commands/plan-loop.md", "loop feature new"),
    ("commands/plan-loop.md", "loop session-end"),
    ("commands/product-develop.md", "feature converge"),
    ("commands/product-develop.md", "AUTO_SKILLS"),
    ("commands/product-develop.md", "loop session-end"),
    ("commands/loop-engine.md", "session-start"),
    ("commands/loop-engine.md", "feature-converge"),
    ("commands/loop-engine.md", "commands/plan-loop.md"),
    ("commands/loop-engine.md", "commands/product-develop.md"),
    ("skills/loop-engine/SKILL.md", "feature-converge"),
    ("skills/loop-engine/SKILL.md", "session-start"),
    ("skills/plan-loop/phases/task-compiler.md", "tasks.md"),
    ("skills/product-develop/SKILL.md", "feature-converge"),
    ("skills/plan-loop/SKILL.md", "spec-clarify"),
    ("AGENTS.md", "docs/CONTINUATION.md"),
    ("skills/plan-loop/SKILL.md", "terminus"),
    ("skills/loop-engine/SKILL.md", "Continuation"),
    ("skills/plan-loop/phases/spec-clarify.md", "Continue automatically"),
    ("skills/plan-loop/phases/spec-checklist.md", "Continue automatically"),
    ("skills/plan-loop/phases/task-compiler.md", "Continue automatically"),
    ("scripts/loop_cli.py", "feature"),
    ("scripts/memory_paths.py", "session_bootstrap_feature_paths"),
    ("scripts/session_lifecycle.py", "read_active_feature"),
]

MAIN_LOOP_COMMANDS = ["commands/plan-loop.md", "commands/product-develop.md", "commands/loop-engine.md"]

MAIN_LOOP_FEATURES = [
    "session-start",
    "PLAN_BOOTSTRAP",
    "ultraplan",
    "session-end",
    "SESSION_MANIFEST",
    "feature new",
    "spec-clarify",
    "spec-checklist",
    "task-compiler",
    "AUTO_SKILLS",
    "feature converge",
    "prod-gap",
    "memory review",
]
TEXT_SUFFIXES = {
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    ".py",
    ".ps1",
    ".sh",
}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            files.append(path)
    return files


def check_required_paths(errors: list[str]) -> None:
    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            errors.append(f"missing required path: {rel}")


def check_uninitialized_template(errors: list[str]) -> None:
    main_plan = ROOT / "templates" / "starter" / "plan" / "main_plan.md"
    if main_plan.exists() and "Status: **UNINITIALIZED**" not in main_plan.read_text(encoding="utf-8"):
        errors.append("templates/starter/plan/main_plan.md must remain UNINITIALIZED")

    step_files = [
        path
        for path in (ROOT / "plan").glob("step_*.md")
        if path.name != "README.md"
    ]
    if step_files:
        joined = ", ".join(str(path.relative_to(ROOT)) for path in step_files)
        errors.append(f"template repo must not contain product step files: {joined}")

    feature_dirs = [
        path
        for path in (ROOT / "plan" / "features").iterdir()
        if path.is_dir()
    ] if (ROOT / "plan" / "features").is_dir() else []
    if feature_dirs:
        joined = ", ".join(str(path.relative_to(ROOT)) for path in feature_dirs)
        errors.append(f"template repo must not contain product feature folders: {joined}")

    active_feature = ROOT / ".loop" / "active-feature.json"
    if active_feature.exists():
        errors.append("template repo must not contain .loop/active-feature.json")


def check_banned_terms(errors: list[str]) -> None:
    local_terms = ROOT / ".template-banned-terms"
    raw_patterns = list(BANNED_PATTERNS)
    if local_terms.exists():
        raw_patterns.extend(
            line.strip()
            for line in local_terms.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in raw_patterns]
    for path in iter_text_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            if pattern.search(text):
                errors.append(f"product-specific term {pattern.pattern!r} found in {rel}")


# A `loop` subcommand that no skill or command file mentions is unreachable in
# practice: users type slash commands, and the agent works from the files listed here.
# Four checks shipped in exactly that state - `loop evidence`, `loop fresh`,
# `loop graph` and `loop archive` - reachable only by someone who already knew they
# existed, which is the same way the approval queue reached 164 entries nobody drained.
#
# Anything genuinely manual belongs below with the reason it cannot be automatic.
# Each of these needs an argument the harness cannot derive, or acts outside the
# workspace, so firing it on its own would be wrong rather than merely unhelpful.
MANUAL_BY_DESIGN = {
    "setup": "creates the workspace; must be intentional",
    "update": "updates the runtime the agent is running from",
    "migrate": "needs a --source path only the user knows",
    "team-init": "commits a bootstrap to the repo for teammates",
    "skills": "writes routers outside the workspace; setup and update already call it",
    "home": "diagnostic; prints the layout and changes nothing",
    "bootstrap": "diagnostic; prints the session read order",
    "session": "ad-hoc search over past sessions",
    "pending": "the opt-in --stage memory path only",
}


def loop_subcommands() -> list[str]:
    """Top-level `loop` subcommands, read from the parser that defines them."""
    source = (ROOT / "scripts" / "loop_cli.py").read_text(encoding="utf-8", errors="ignore")
    # `sub` is the top-level subparser; nested groups use their own variable names,
    # so this deliberately matches only the outermost level.
    return sorted(set(re.findall(r'\bsub\.add_parser\(\s*"([a-z][a-z-]*)"', source)))


def check_command_reachability(errors: list[str]) -> None:
    surface_files = list((ROOT / "skills").rglob("*.md")) + list((ROOT / "commands").rglob("*.md"))
    surface = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in surface_files)

    for name in loop_subcommands():
        if name in MANUAL_BY_DESIGN:
            continue
        # Reachable in any form the surface actually uses: the CLI form, a slash
        # command, or a skill directory. `compact` is reached as `/compact-loop` and
        # `sync` as `/sync-loop-state`, so matching only `loop <name>` reports
        # capabilities that are wired perfectly well.
        escaped = re.escape(name)
        if re.search(
            rf"\bloop {escaped}\b|/{escaped}\b|/{escaped}-|skills/{escaped}\b|skills/{escaped}-",
            surface,
        ):
            continue
        errors.append(
            f"`loop {name}` is named in no skill or command file, so nothing will ever run it. "
            f"Wire it into the skill that owns the capability, or add it to "
            f"MANUAL_BY_DESIGN in {Path(__file__).name} with the reason it cannot be automatic."
        )

    stale = sorted(set(MANUAL_BY_DESIGN) - set(loop_subcommands()))
    for name in stale:
        errors.append(f"MANUAL_BY_DESIGN lists `loop {name}`, which is no longer a command - drop it.")


# A skill nothing points at is as unreachable as a CLI command nothing names. Users type
# slash commands, so the only skills that ever run are the ones a command file reaches -
# directly, or through another skill it already reaches. Reference skills such as
# `codebase-design` are reached that way and are fine; a skill reached by nothing is dead
# weight that still costs a reader's attention every time they scan the folder.
def _skill_refs(text: str, known: set[str]) -> set[str]:
    return set(re.findall(r"skills/([a-z0-9-]+)/", text)) & known


def check_skill_reachability(errors: list[str]) -> None:
    skills = {p.parent.name: p.parent for p in (ROOT / "skills").glob("*/SKILL.md")}
    if not skills:
        return
    entry = list(ROOT.glob("*.md")) + list((ROOT / "commands").glob("*.md"))
    queue = [
        name
        for path in entry
        for name in _skill_refs(path.read_text(encoding="utf-8", errors="ignore"), set(skills))
    ]
    seen: set[str] = set()
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for path in skills[name].rglob("*.md"):
            queue += _skill_refs(path.read_text(encoding="utf-8", errors="ignore"), set(skills))

    for name in sorted(set(skills) - seen):
        errors.append(
            f"`skills/{name}/` is reached by no command file and by no skill a command "
            "reaches, so nothing will ever load it. Point at it from the command that owns "
            "the capability, or from a skill that command already reads."
        )


def check_skill_frontmatter(errors: list[str]) -> None:
    for skill_path in (ROOT / "skills").glob("*/SKILL.md"):
        text = skill_path.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---\n"):
            errors.append(f"skill missing YAML frontmatter: {skill_path.relative_to(ROOT)}")
            continue
        frontmatter = text.split("---", 2)[1]
        if "name:" not in frontmatter or "description:" not in frontmatter:
            errors.append(f"skill frontmatter needs name and description: {skill_path.relative_to(ROOT)}")


def check_feature_wiring(errors: list[str]) -> None:
    for rel, needle in FEATURE_WIRING:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"feature wiring file missing: {rel}")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if needle not in text:
            errors.append(f"feature workflow not wired: {rel} must mention {needle!r}")


def check_main_loop_coverage(errors: list[str]) -> None:
    """Ensure /plan-loop, /product-develop, /loop-engine each reference core cycle features."""
    combined = ""
    for rel in MAIN_LOOP_COMMANDS:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"main loop command missing: {rel}")
            continue
        combined += path.read_text(encoding="utf-8", errors="ignore") + "\n"
    if not combined:
        return
    for feature in MAIN_LOOP_FEATURES:
        if feature not in combined:
            errors.append(
                f"main loop gap: none of {MAIN_LOOP_COMMANDS} mention {feature!r}"
            )
    for rel in MAIN_LOOP_COMMANDS:
        text = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        if "Cycle checklist" not in text:
            errors.append(f"main loop command missing cycle checklist: {rel}")


def main() -> int:
    errors: list[str] = []
    check_required_paths(errors)
    check_uninitialized_template(errors)
    check_banned_terms(errors)
    check_skill_frontmatter(errors)
    check_feature_wiring(errors)
    check_main_loop_coverage(errors)
    check_command_reachability(errors)
    check_skill_reachability(errors)

    if errors:
        print("Template validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
