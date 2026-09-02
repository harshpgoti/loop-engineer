#!/usr/bin/env python3
"""Chain benchmark: measure the chain's own behaviour over time.

Reads the chain's own state (`state.db`, `plan/`, scripts counts) and emits
a small benchmark report. Useful for tracking chain health across sessions.

Tracks:
- Total canonical skills, commands, roles, capabilities, profiles
- Skills per class (read-only / stateful / mutating / assurance)
- Test count from the last test run (or reads `state.db` if present)
- Plan files: count, size, freshness
- Documentation: docs/ size, ADRs, runbooks
- Recent changes (last 5 sessions from state.db if present)
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _collect_skill_metrics(workspace: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "skills_total": 0,
        "by_class": {"read-only": 0, "stateful": 0, "mutating": 0, "assurance": 0},
    }
    if not (workspace / "skills").exists():
        return metrics
    policy = _load_json(workspace / "manifests" / "skill_policy.json")
    assignments = policy.get("assignments", {})
    for p in (workspace / "skills").glob("*/SKILL.md"):
        metrics["skills_total"] += 1
        cls = assignments.get(p.parent.name, "?")
        if cls in metrics["by_class"]:
            metrics["by_class"][cls] += 1
    return metrics


def _collect_command_metrics(workspace: Path) -> dict[str, Any]:
    metrics = {
        "commands_total": 0,
        "by_capability": {},
    }
    if not (workspace / "commands").exists():
        return metrics
    capabilities = _load_json(workspace / "manifests" / "capabilities.json")
    for cap in capabilities.get("capabilities", []):
        metrics["by_capability"][cap["id"]] = len(cap.get("commands", []))
        metrics["commands_total"] += len(cap.get("commands", []))
    return metrics


def _collect_role_metrics(workspace: Path) -> dict[str, Any]:
    metrics = {"roles_total": 0, "by_class": {}}
    if not (workspace / "manifests" / "agents.json").exists():
        return metrics
    agents = _load_json(workspace / "manifests" / "agents.json")
    for role in agents.get("roles", []):
        metrics["roles_total"] += 1
        cls = role.get("class", "?")
        metrics["by_class"][cls] = metrics["by_class"].get(cls, 0) + 1
    return metrics


def _collect_plan_metrics(workspace: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "main_plan_exists": False,
        "main_plan_size_bytes": 0,
        "step_files": 0,
        "feature_specs": 0,
        "docts": 0,
    }
    plan = workspace / "plan"
    if plan.exists():
        main = plan / "main_plan.md"
        if main.exists():
            metrics["main_plan_exists"] = True
            metrics["main_plan_size_bytes"] = main.stat().st_size
        metrics["step_files"] = len(list(plan.glob("step_*.md")))
        features = plan / "features"
        if features.exists():
            metrics["feature_specs"] = sum(
                1 for f in features.glob("*/spec.md")
            )
    docts = workspace / "DOUBTS.md"
    if docts.exists():
        with docts.open(encoding="utf-8") as f:
            content = f.read()
        # Count question lines (rough heuristic).
        metrics["docts"] = len(re.findall(r"^-\s*\[", content, re.MULTILINE))
    return metrics


def _collect_state_db_metrics(workspace: Path) -> dict[str, Any]:
    """Read recent sessions from .loop/state.db if present."""
    metrics: dict[str, Any] = {
        "state_db_exists": False,
        "total_sessions": 0,
        "recent_sessions": [],
    }
    db_path = workspace / ".loop" / "state.db"
    if not db_path.exists():
        return metrics
    metrics["state_db_exists"] = True
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cur.fetchall()}
            if "sessions" in tables:
                cur = conn.execute("SELECT COUNT(*) FROM sessions")
                metrics["total_sessions"] = cur.fetchone()[0]
                cur = conn.execute(
                    "SELECT id, started_at, command FROM sessions ORDER BY started_at DESC LIMIT 5"
                )
                for row in cur.fetchall():
                    metrics["recent_sessions"].append(
                        {"id": row[0], "started_at": row[1], "command": row[2]}
                    )
        finally:
            conn.close()
    except sqlite3.Error:
        pass
    return metrics


def _collect_test_metrics(workspace: Path) -> dict[str, Any]:
    """Count test files; reading pass/fail is best-effort."""
    metrics = {"test_files": 0}
    tests_dir = workspace / "scripts"
    if not tests_dir.exists():
        return metrics
    metrics["test_files"] = sum(1 for p in tests_dir.glob("test_*.py"))
    return metrics


def benchmark(workspace: Path) -> dict[str, Any]:
    return {
        "version": 1,
        "timestamp": int(time.time()),
        "workspace": str(workspace),
        "skills": _collect_skill_metrics(workspace),
        "commands": _collect_command_metrics(workspace),
        "roles": _collect_role_metrics(workspace),
        "plan": _collect_plan_metrics(workspace),
        "state_db": _collect_state_db_metrics(workspace),
        "tests": _collect_test_metrics(workspace),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Chain Benchmark",
        "",
        f"Workspace: `{report['workspace']}`",
        "",
        "## Skills",
        f"- Total: **{report['skills']['skills_total']}**",
        "- By class: " + ", ".join(
            f"`{k}`: {v}" for k, v in report['skills']['by_class'].items()
        ),
        "",
        "## Commands",
        f"- Total: **{report['commands']['commands_total']}**",
        "- By capability: " + ", ".join(
            f"`{k}`: {v}" for k, v in report['commands']['by_capability'].items()
        ),
        "",
        "## Roles",
        f"- Total: **{report['roles']['roles_total']}**",
        "- By class: " + ", ".join(
            f"`{k}`: {v}" for k, v in report['roles']['by_class'].items()
        ),
        "",
        "## Plan",
        f"- `main_plan.md` exists: **{report['plan']['main_plan_exists']}** ({report['plan']['main_plan_size_bytes']} bytes)",
        f"- Step files: **{report['plan']['step_files']}**",
        f"- Feature specs: **{report['plan']['feature_specs']}**",
        f"- Open doubts (rough): **{report['plan']['docts']}**",
        "",
        "## Tests",
        f"- Test files: **{report['tests']['test_files']}**",
        "",
        "## State",
        f"- `state.db` exists: **{report['state_db']['state_db_exists']}**",
        f"- Total sessions: **{report['state_db']['total_sessions']}**",
    ]
    if report['state_db']['recent_sessions']:
        lines.append("- Recent sessions:")
        for s in report['state_db']['recent_sessions']:
            lines.append(f"  - `{s.get('id', '?')}` {s.get('started_at', '?')} {s.get('command', '?')}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    report = benchmark(workspace)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())