#!/usr/bin/env python3
"""Health-check the Loop Engineering OS runtime and active product workspace."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

from workspace_utils import ROOT, load_config, resolve_workspace


REQUIRED_TOOL_PATHS = [
    "AGENTS.md",
    "commands/plan-loop.md",
    "commands/product-develop.md",
    "commands/loop-engine.md",
    "skills/plan-loop/SKILL.md",
    "skills/product-develop/SKILL.md",
    "scripts/validate_template.py",
    "scripts/validate_outputs.py",
    "scripts/workspace_registry.py",
]

PRODUCT_STATE_FILES = [
    "plan/main_plan.md",
    "memories/MEMORY.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "HANDOFF.md",
    "CURRENT_STATE.md",
]

SCRIPT_IMPORTS = [
    "detect_workspace",
    "status",
    "sync_loop_state",
    "release_check",
    "deployment_plan",
    "deployment_topics",
    "loop_home",
    "workspace_resolver",
    "memory_paths",
    "memory_curator",
    "session_recall",
    "session_store",
    "session_search",
    "skill_resolver",
    "pending_writes",
    "loop_cli",
    "migrate_import",
    "loop_update",
    "migrate_workspace",
    "prod_gap",
    "compact_context",
    "source_tree_scan",
]


def check_exists(path: Path, label: str, errors: list[str], warnings: list[str], required: bool = True) -> None:
    if path.exists():
        return
    message = f"{label}: missing `{path}`"
    if required:
        errors.append(message)
    else:
        warnings.append(message)


def run_validator(script_name: str) -> tuple[bool, str]:
    script = ROOT / "scripts" / script_name
    if not script.exists():
        return False, f"missing script `{script_name}`"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip() or f"{script_name} exited {result.returncode}"


def check_script_imports(errors: list[str]) -> None:
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    for module_name in SCRIPT_IMPORTS:
        path = scripts_dir / f"{module_name}.py"
        if not path.exists():
            errors.append(f"script import check: missing `{path.name}`")
            continue
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            errors.append(f"script import check: cannot load `{module_name}.py`")
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - report import failures clearly
            errors.append(f"script import check: `{module_name}.py` failed to import ({exc})")


def check_template_repo_clean(errors: list[str], warnings: list[str]) -> None:
    main_plan = ROOT / "templates" / "starter" / "plan" / "main_plan.md"
    if main_plan.exists() and "Status: **UNINITIALIZED**" not in main_plan.read_text(encoding="utf-8", errors="ignore"):
        warnings.append("Starter template `templates/starter/plan/main_plan.md` is initialized; it must stay UNINITIALIZED.")

    step_files = list((ROOT / "plan").glob("step_*.md"))
    if step_files:
        warnings.append("Tool repo contains product step files; keep step plans in the product workspace.")


def load_template() -> str:
    return (ROOT / "templates" / "doctor.template.md").read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def bullet(items: list[str]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def check_memory_health(workspace: Path, errors: list[str], warnings: list[str], passes: list[str]) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from loop_home import loop_home, registry_path
    from memory_curator import detect_drift, usage_report
    from memory_paths import (
        MEMORY_CHAR_LIMIT,
        USER_CHAR_LIMIT,
        ensure_memory_layout,
        memory_file,
        soul_file,
        state_db,
        user_file,
    )
    from pending_writes import list_pending
    from session_store import connect, search_sessions
    from skill_resolver import validate_user_skills

    ensure_memory_layout(workspace)
    mem_path = memory_file(workspace)
    user_path = user_file(workspace)
    soul_path = soul_file(workspace)

    if mem_path.exists():
        mem_text = mem_path.read_text(encoding="utf-8", errors="ignore")
        usage = usage_report(mem_text, MEMORY_CHAR_LIMIT)
        if usage["over"]:
            warnings.append(f"Memory over limit: {usage['chars']}/{usage['limit']} chars in `{mem_path.name}`.")
        else:
            passes.append(f"Memory within limit: {usage['chars']}/{usage['limit']} chars.")
    else:
        warnings.append("Canonical memory file missing.")

    if user_path.exists():
        user_text = user_path.read_text(encoding="utf-8", errors="ignore")
        usage = usage_report(user_text, USER_CHAR_LIMIT)
        if usage["over"]:
            warnings.append(f"USER profile over limit: {usage['chars']}/{usage['limit']} chars.")
    else:
        warnings.append("Missing `memories/USER.md`.")

    if not soul_path.exists():
        warnings.append("Missing `memories/SOUL.md`.")

    drift = detect_drift(workspace)
    for item in drift:
        warnings.append(item)

    pending = list_pending(workspace)
    if pending:
        warnings.append(f"{len(pending)} pending staged write(s) under `.loop/pending/`.")

    db_path = state_db(workspace)
    if db_path.exists():
        try:
            conn = connect(db_path)
            conn.execute("SELECT COUNT(*) FROM sessions_fts").fetchone()
            search_sessions(db_path, "memory", limit=1)
            passes.append("state.db FTS5 index healthy.")
            conn.close()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"state.db FTS5 check failed: {exc}")
    else:
        warnings.append("Missing `state.db`; session recall unavailable.")

    skill_issues = validate_user_skills(workspace)
    for issue in skill_issues:
        warnings.append(issue)

    reg = registry_path()
    if reg.exists():
        passes.append(f"LOOP_HOME registry present: `{loop_home()}`")


def diagnose(workspace: Path | None) -> tuple[str, int]:
    errors: list[str] = []
    warnings: list[str] = []
    passes: list[str] = []

    for rel in REQUIRED_TOOL_PATHS:
        check_exists(ROOT / rel, "tool file", errors, warnings)

    config = load_config()
    if config.get("current"):
        passes.append(f"Workspace registry current: `{config['current']}`")
    else:
        warnings.append("No registered current workspace; scripts fall back to current directory.")

    if workspace is not None:
        for rel in PRODUCT_STATE_FILES:
            check_exists(workspace / rel, "product-state file", errors, warnings, required=False)
        from memory_paths import main_plan_file

        if main_plan_file(workspace).exists():
            passes.append(f"Product workspace resolved: `{workspace}`")
    else:
        warnings.append("Could not resolve a product workspace.")

    check_script_imports(errors)
    check_template_repo_clean(errors, warnings)

    template_ok, template_output = run_validator("validate_template.py")
    if template_ok:
        passes.append("Template validation passed.")
    else:
        errors.append(f"Template validation failed: {template_output}")

    if workspace is not None:
        outputs_ok, outputs_output = run_validator_with_workspace("validate_outputs.py", workspace)
        if outputs_ok:
            passes.append("Product output validation passed.")
        else:
            warnings.append(f"Product output validation: {outputs_output}")

    if workspace is not None:
        check_memory_health(workspace, errors, warnings, passes)

    healthy = not errors
    status = "HEALTHY" if healthy else "UNHEALTHY"
    if healthy and warnings:
        status = "HEALTHY WITH WARNINGS"

    template = load_template()
    content = render(
        template,
        {
            "UPDATED_DATE": date.today().isoformat(),
            "OVERALL_STATUS": status,
            "WORKSPACE_PATH": str(workspace) if workspace else "unresolved",
            "PASSES": bullet(passes),
            "WARNINGS": bullet(warnings),
            "ERRORS": bullet(errors),
            "NEXT_COMMAND": "/sync-loop-state" if warnings else "/loop-engine",
        },
    )
    return content, 0 if healthy else 1


def run_validator_with_workspace(script_name: str, workspace: Path) -> tuple[bool, str]:
    script = ROOT / "scripts" / script_name
    result = subprocess.run(
        [sys.executable, str(script), "--workspace", str(workspace)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Loop Engineering OS health checks.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for DOCTOR.md. Defaults to workspace DOCTOR.md or tool-root DOCTOR.md.",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    content, exit_code = diagnose(workspace)
    output = Path(args.output) if args.output else workspace / "DOCTOR.md"
    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")
    print(content.splitlines()[0])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
