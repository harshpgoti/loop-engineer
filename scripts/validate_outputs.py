#!/usr/bin/env python3
"""Validate product-loop outputs after /plan or /product-develop.

This is intentionally lightweight. It checks structure, not quality of prose.
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

from workspace_utils import resolve_workspace


ROOT = Path(__file__).resolve().parents[1]

MAIN_PLAN_SECTIONS = [
    "## Product",
    "## Deployment & Infrastructure",
    "## Product Thesis",
    "## Step Plan Index",
    "## Current Product State",
]

STEP_SECTIONS = [
    "## Purpose",
    "## Users",
    "## Problem",
    "## MVP Scope",
    "## Technical Plan",
    "## Acceptance Criteria",
    "## Gates",
]


def check_sections(path: Path, required: list[str], errors: list[str]) -> None:
    display_path = path.as_posix()
    try:
        display_path = path.relative_to(ROOT).as_posix()
    except ValueError:
        pass

    if not path.exists():
        errors.append(f"missing file: {display_path}")
        return

    text = path.read_text(encoding="utf-8", errors="ignore")
    for section in required:
        if section not in text:
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
            check_sections(step_file, STEP_SECTIONS, errors)

    if errors:
        print("Output validation failed:\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Output validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
