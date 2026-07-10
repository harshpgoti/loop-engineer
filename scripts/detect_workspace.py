#!/usr/bin/env python3
"""Detect candidate product workspaces."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from workspace_resolver import find_local_workspace, resolve_effective_workspace
from workspace_utils import ROOT, load_config


MARKER_FILES = ("plan/main_plan.md", "memories/MEMORY.md", "TASKS.yml", "main_plan.md", "MEMORY.md")


@dataclass
class Candidate:
    path: Path
    reason: str
    score: int


def has_product_markers(path: Path) -> bool:
    return any((path / name).exists() for name in MARKER_FILES)


def score_candidate(path: Path) -> int:
    score = 0
    for name in MARKER_FILES:
        if (path / name).exists():
            score += 1
    if (path / "plan").exists():
        score += 1
    if (path / "HANDOFF.md").exists():
        score += 1
    return score


def collect_candidates() -> list[Candidate]:
    candidates: dict[str, Candidate] = {}

    def add(path: Path, reason: str) -> None:
        resolved = path.resolve()
        key = str(resolved)
        if key in candidates:
            return
        if not resolved.exists() or not resolved.is_dir():
            return
        if not has_product_markers(resolved):
            return
        candidates[key] = Candidate(
            path=resolved,
            reason=reason,
            score=score_candidate(resolved),
        )

    add(ROOT, "current directory contains product-state files")
    local = find_local_workspace()
    if local is not None:
        add(local, "auto-detected local loop data")
    add(ROOT.parent / "product", "sibling ../product directory")
    add(ROOT / "product", "child ./product directory")

    config = load_config()
    for name, data in config.get("workspaces", {}).items():
        raw_path = data.get("path", "")
        path = (ROOT / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
        add(path, f"registered workspace '{name}'")

    return sorted(candidates.values(), key=lambda item: (-item.score, str(item.path)))


def suggest_register_command(candidate: Candidate) -> str:
    try:
        rel = candidate.path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = candidate.path.as_posix()
    return f"python scripts/workspace_registry.py register --name product --path {rel} --set-current"


def format_report(candidates: list[Candidate]) -> str:
    config = load_config()
    current = config.get("current")
    lines = ["# Workspace Detection", ""]

    if current:
        workspace = config.get("workspaces", {}).get(current, {})
        lines.append(f"- **Registered current:** `{current}` -> `{workspace.get('path', 'unknown')}`")
    else:
        lines.append("- **Registered current:** none")

    if not candidates:
        lines.append("- **Candidates:** none detected")
        lines.append("- **Suggestion:** run `/setup-loop-engine` or create a product workspace with `main_plan.md`.")
        return "\n".join(lines) + "\n"

    lines.append("- **Candidates:**")
    for item in candidates:
        lines.append(f"  - `{item.path}` ({item.reason}, score={item.score})")

    best = candidates[0]
    lines.append(f"- **Best candidate:** `{best.path}`")
    lines.append(f"- **Suggested register command:** `{suggest_register_command(best)}`")
    if len(candidates) > 1:
        lines.append("- **Note:** multiple candidates found; confirm the correct product workspace before registering.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect candidate product workspaces.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    auto_path, mode = resolve_effective_workspace()
    if not args.json:
        print(f"Auto-resolved: {auto_path} ({mode})")
        if mode == "local":
            print("Local loop data detected in current folder tree.")
        else:
            print("No local loop data; using global ~/.loop-engineer/.")

    candidates = collect_candidates()
    if args.json:
        for item in candidates:
            print(item.path)
        return 0

    print(format_report(candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
