#!/usr/bin/env python3
"""Validate product-loop outputs after /plan-loop or /develop-product.

This is intentionally lightweight. It checks structure, not quality of prose.
"""

from __future__ import annotations

import sys
import argparse
import re
from pathlib import Path

from workspace_utils import resolve_workspace


ROOT = Path(__file__).resolve().parents[1]

MAIN_PLAN_SECTIONS = {
    "Product": ("Product",),
    "Deployment & Infrastructure": ("Deployment & Infrastructure",),
    "Product Thesis": ("Product Thesis", "The honest position"),
    "Step Plan Index": ("Step Plan Index", "Module roadmap"),
    "Current Product State": ("Current Product State", "Current state", "As-built state", "The honest position"),
}

STEP_SECTIONS = {
    "Purpose": ("Purpose", "Why this step exists", "Why this is"),
    "Scope": ("Scope", "MVP Scope"),
    "Acceptance Criteria": ("Acceptance Criteria", "Acceptance criteria"),
    "Risks": ("Risks", "Risk"),
    "Definition of done": ("Definition of done", "Gates", "Master gates"),
}


def _headings(text: str) -> set[str]:
    """Return normalized level-2 headings, accepting numbered plan headings."""
    found: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^##\s+(?:\d+[.)]\s+)?(.+?)\s*$", line)
        if match:
            found.add(match.group(1).casefold())
    return found


def _has_any(headings: set[str], aliases: tuple[str, ...]) -> bool:
    normalized = tuple(alias.casefold() for alias in aliases)
    return any(
        any(heading == alias or heading.startswith(alias + " ") for alias in normalized)
        for heading in headings
    )


def check_sections(path: Path, required: dict[str, tuple[str, ...]], errors: list[str]) -> None:
    display_path = path.as_posix()
    try:
        display_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        pass

    if not path.exists():
        errors.append(f"missing file: {display_path}")
        return

    text = path.read_text(encoding="utf-8", errors="ignore")
    headings = _headings(text)
    for section, aliases in required.items():
        if not _has_any(headings, aliases):
            errors.append(f"{display_path} missing section: {section}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate product-loop output structure.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Product workspace where state files live. Defaults to registered current workspace or current directory.",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    errors: list[str] = []
    from memory_paths import main_plan_file

    main_plan = main_plan_file(workspace)
    check_sections(main_plan, MAIN_PLAN_SECTIONS, errors)

    step_files = sorted((workspace / "plan").glob("step_*.md"))
    if "Status: **UNINITIALIZED**" not in main_plan.read_text(encoding="utf-8", errors="ignore"):
        if not step_files:
            errors.append("initialized product needs at least one plan/step_*.md file")
        for step_file in step_files:
            text = step_file.read_text(encoding="utf-8", errors="ignore")
            headings = _headings(text)
            # A delegated sub-product index has a different, intentional shape from
            # a deep-planned step. Validate either recognized form without inventing
            # mandatory prose headings the plan never chose.
            if _has_any(headings, ("What it is", "As-built state")):
                required = {"Purpose": ("What it is",), "Current Product State": ("As-built state",)}
            else:
                required = STEP_SECTIONS
            check_sections(step_file, required, errors)

    if errors:
        print("Output validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Output validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
