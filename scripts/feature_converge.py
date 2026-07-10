#!/usr/bin/env python3
"""Compare active feature spec/plan/tasks against TASKS.yml and repo signals."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from feature_paths import feature_artifact_paths, read_active_feature
from workspace_utils import resolve_workspace


def read_text(path: Path, limit: int = 8000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]


def extract_task_ids(tasks_yml: str) -> set[str]:
    return set(re.findall(r"id:\s*(TASK-\d+)", tasks_yml))


def extract_feature_task_lines(tasks_md: str) -> list[str]:
    lines: list[str] = []
    for line in tasks_md.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]") or stripped.startswith("- [x]") or stripped.startswith("- [X]"):
            lines.append(stripped)
        elif re.match(r"^-\s+TASK-\d+", stripped):
            lines.append(stripped)
    return lines


def unchecked_feature_tasks(tasks_md: str) -> list[str]:
    return [ln for ln in extract_feature_task_lines(tasks_md) if ln.startswith("- [ ]")]


def render_report(
    workspace: Path,
    feature: dict,
    artifacts: dict[str, Path],
    gaps: list[str],
    suggestions: list[str],
) -> str:
    lines = [
        "# Feature Converge Report",
        "",
        f"**Updated:** {date.today().isoformat()}",
        f"**Feature:** `{feature.get('path')}` — {feature.get('title', '')}",
        "",
        "## Artifact status",
        "",
    ]
    for name, path in artifacts.items():
        status = "ok" if path.exists() else "missing"
        rel = path.relative_to(workspace).as_posix() if path.exists() else str(path.name)
        lines.append(f"- `{rel}` ({status})")
    lines.extend(["", "## Gaps", ""])
    if gaps:
        lines.extend(f"- {g}" for g in gaps)
    else:
        lines.append("- No critical gaps detected.")
    lines.extend(["", "## Suggested follow-ups", ""])
    if suggestions:
        lines.extend(f"- {s}" for s in suggestions)
    else:
        lines.append("- Continue `/product-develop` on unchecked tasks.")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- Update `TASKS.yml` via `skills/task-compiler/SKILL.md` if gaps are real.",
            "- Re-run `/feature-converge` after implementation slices.",
            "",
        ]
    )
    return "\n".join(lines)


def converge(workspace: Path) -> tuple[Path | None, list[str]]:
    feature = read_active_feature(workspace)
    if not feature:
        return None, ["No active feature. Run `loop feature new \"<title>\"` first."]
    feat = Path(feature["abs_path"])
    artifacts = feature_artifact_paths(feat)
    gaps: list[str] = []
    suggestions: list[str] = []

    if not artifacts["spec"].exists():
        gaps.append("Missing spec.md — run `/feature-new` or complete spec during `/plan`.")
    if not artifacts["tasks"].exists():
        gaps.append("Missing tasks.md — run `skills/task-compiler/SKILL.md` after feature-plan.")
    if artifacts["spec"].exists() and not artifacts["clarifications"].exists():
        suggestions.append("Run `/spec-clarify` before locking feature-plan.")
    if artifacts["spec"].exists() and not artifacts["checklist"].exists():
        suggestions.append("Run `/spec-checklist` to validate requirement quality.")

    tasks_md = read_text(artifacts["tasks"])
    open_tasks = unchecked_feature_tasks(tasks_md)
    if tasks_md and open_tasks:
        suggestions.append(f"{len(open_tasks)} unchecked task(s) in tasks.md — continue `/product-develop`.")
    elif tasks_md:
        suggestions.append("All feature tasks checked — run `/prod-gap` for release readiness.")

    tasks_yml = read_text(workspace / "TASKS.yml")
    if tasks_md and tasks_yml:
        yaml_ids = extract_task_ids(tasks_yml)
        if yaml_ids and not any("TASK-" in ln for ln in extract_feature_task_lines(tasks_md)):
            gaps.append("tasks.md does not reference TASKS.yml ids — sync via task-compiler.")

    report_path = artifacts["converge"]
    report_path.write_text(
        render_report(workspace, feature, artifacts, gaps, suggestions),
        encoding="utf-8",
    )
    return report_path, gaps + suggestions


def main() -> int:
    parser = argparse.ArgumentParser(description="Converge active feature vs tasks and plan state.")
    parser.add_argument("--workspace", default=None)
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    report, messages = converge(workspace)
    if report is None:
        for msg in messages:
            print(msg)
        return 1
    for msg in messages:
        print(msg)
    print(f"Wrote {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
