#!/usr/bin/env python3
"""Select governed agent roles from command, task, risk, and domain signals."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def select(command: str, text: str, domain_skills: list[str] | None = None) -> list[str]:
    command = (command or "").lower()
    text = (text or "").lower()
    selected: list[str] = []

    def add(*roles: str) -> None:
        for role in roles:
            if role not in selected:
                selected.append(role)

    if any(token in command for token in ("plan", "revise", "feature", "resolve-doubts")):
        add("strategist", "researcher", "product-manager", "architect")
    if any(token in command for token in ("develop", "loop-engine")):
        add("architect", "builder", "code-reviewer", "qa-evaluator", "security-reviewer")
    if "diagnose" in command or re.search(r"\b(bug|failure|broken|regression|build error)\b", text):
        add("build-repairer", "qa-evaluator", "code-reviewer")
    if any(token in command for token in ("release", "deploy", "prod-gap")):
        add("release-manager", "operations-reviewer", "security-reviewer", "qa-evaluator")
    if re.search(r"\b(doc|documentation|readme|runbook)\b", text):
        add("documentation-reviewer")
    if re.search(r"\b(accessibility|a11y|frontend|ui|motion|animation)\b", text):
        add("accessibility-reviewer")
    for skill, role in (("data-engineering", "data-reviewer"), ("ml-engineering", "ml-reviewer"), ("operations", "operations-reviewer")):
        if skill in (domain_skills or []):
            add(role)
    if not selected:
        add("loop-operator")
    return selected


def render(roles: list[str], root: Path = ROOT) -> str:
    registry = {item["id"]: item for item in json.loads((root / "manifests" / "agents.json").read_text(encoding="utf-8"))["roles"]}
    lines = ["# Auto Agent Roles", "", "Selected deterministically from the active command, task, risk, and domain signals.", ""]
    for role in roles:
        item = registry[role]
        boundary = f"; independent from {', '.join(item['independent_from'])}" if item["independent_from"] else ""
        lines.append(f"- `{role}` — {item['class']}; skills: {', '.join(item['skills'])}{boundary}")
    lines.extend(["", "Selection grants no authority beyond the active command and approved product plan.", ""])
    return "\n".join(lines)


def run_router(workspace: Path, *, command: str = "", text: str = "", domain_skills: list[str] | None = None, write: bool = False) -> list[str]:
    roles = select(command, text, domain_skills)
    if write:
        path = workspace / "plan" / "AUTO_AGENTS.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(roles), encoding="utf-8")
    return roles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--command", default="")
    parser.add_argument("--text", default="")
    parser.add_argument("--domain-skill", action="append", default=[])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    roles = run_router(args.workspace.resolve(), command=args.command, text=args.text, domain_skills=args.domain_skill, write=args.write)
    print(render(roles), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
