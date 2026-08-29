#!/usr/bin/env python3
"""Select domain skills from deterministic workspace and task signals."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROUTES = {
    "data-engineering": ("migration", "schema", "database", "pipeline", "etl", "warehouse", "analytics", "retention", "lineage"),
    "ml-engineering": ("machine learning", "model training", "inference", "feature store", "dataset", "drift", "embedding", "classifier"),
    "operations": ("slo", "observability", "incident", "on-call", "backup", "restore", "capacity", "runbook", "production operations"),
}


def _workspace_text(workspace: Path, extra: str) -> str:
    chunks = [extra]
    for rel in ("plan/main_plan.md", "plan/BUILD_CONTEXT.md", "HANDOFF.md"):
        path = workspace / rel
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks).lower()


def select(workspace: Path, extra: str = "") -> list[tuple[str, list[str]]]:
    text = _workspace_text(workspace, extra)
    picks: list[tuple[str, list[str]]] = []
    for skill, signals in ROUTES.items():
        matched = sorted({signal for signal in signals if re.search(rf"\b{re.escape(signal)}\b", text)})
        if matched:
            picks.append((skill, matched))
    return picks


def render(picks: list[tuple[str, list[str]]]) -> str:
    lines = ["# Auto Domain Skills", "", "Generated deterministically from current product and task signals.", ""]
    if not picks:
        lines.append("No specialized data, ML, or operations skill selected.")
    else:
        for skill, signals in picks:
            lines.append(f"- `{skill}` — signals: {', '.join(signals)}")
    lines.extend(["", "Read only the selected skill files; this report does not grant external-action authority.", ""])
    return "\n".join(lines)


def run_router(workspace: Path, *, extra: str = "", write: bool = False) -> list[tuple[str, list[str]]]:
    picks = select(workspace, extra)
    if write:
        path = workspace / "plan" / "AUTO_DOMAIN_SKILLS.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(picks), encoding="utf-8")
    return picks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--text", default="")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    picks = run_router(args.workspace.resolve(), extra=args.text, write=args.write)
    print(render(picks), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
