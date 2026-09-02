#!/usr/bin/env python3
"""Generate `scripts/_INDEX.md` and `scripts/README.md` from the actual
scripts in the folder.

Each non-test, non-underscore-prefixed Python file is treated as a
top-level script. We extract the first-line docstring (if any) as a
one-line purpose. The output is a Markdown table sorted alphabetically.

Run as part of the chain's self-audit (or as a one-off after a round
of script additions).
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
README = SCRIPTS / "README.md"
INDEX = SCRIPTS / "_INDEX.md"


def _extract_purpose(path: Path) -> str:
    """Extract a one-line purpose from a Python file.

    Strategy: parse the module docstring. If absent, fall back to the
    first non-blank, non-comment line that looks like a summary.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return ""
    docstring = ast.get_docstring(tree)
    if docstring:
        first_line = docstring.strip().splitlines()[0]
        # Strip trailing period for table use.
        return first_line.rstrip(".")
    # Fall back: first comment line.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and len(stripped) > 2:
            return stripped.lstrip("#").strip().rstrip(".")
    return ""


def _discover(into: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    base = into if into is not None else SCRIPTS
    for path in sorted(base.glob("*.py")):
        name = path.stem
        if name.startswith("test_") or name.startswith("_"):
            continue
        purpose = _extract_purpose(path)
        rows.append({"name": name, "purpose": purpose, "path": path})
    return rows


def render(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# scripts/",
        "",
        f"{len(rows)} top-level scripts. Each is a deterministic Python module called by the chain's commands and lifecycle hooks.",
        "",
        "| Script | Purpose |",
        "|---|---|",
    ]
    for row in rows:
        name = f"`{row['name']}.py`"
        purpose = row["purpose"] or "_no docstring; check source_"
        lines.append(f"| {name} | {purpose} |")
    lines.extend([
        "",
        "## Conventions",
        "",
        "- Every script reads its inputs from `sys.argv` and `--workspace` (where applicable).",
        "- Every script writes to the workspace, never to the LE app repo (except diagnostics and benchmarks).",
        "- Every script imports the canonical `app_root = Path(__file__).resolve().parents[1]` and uses it for `manifests/`, `skills/`, `commands/`, `harnesses/`.",
        "- Every script has a test in `test_<name>.py` if its logic is non-trivial.",
        "",
        "## Conventions for new scripts",
        "",
        "When you add a new script:",
        "1. Add a one-line docstring at the top of the file: `\\\"\\\"\\\"Run X for Y.\\\"\\\"\\\"`.",
        "2. Add it to the right capability in `manifests/capabilities.json` (if it backs a public command).",
        "3. Run `python scripts/_index.py` (this file) to regenerate this index.",
        "4. Add a `test_<name>.py` covering the happy path and one error path.",
        "5. Run `python -m unittest discover -s scripts -p \"test_*.py\"`.",
        "",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit non-zero if README.md is out of date")
    parser.add_argument("--root", type=Path, default=None, help="LE app root (default: parent of this script)")
    args = parser.parse_args(argv)
    base = args.root if args.root is not None else SCRIPTS.parent
    rows = _discover(base / "scripts")
    new_content = render(rows)
    current = README.read_text(encoding="utf-8") if README.exists() else ""
    if args.check:
        if current != new_content:
            print(f"README.md is out of date (regenerate with: python scripts/_index.py)")
            return 1
        return 0
    README.write_text(new_content, encoding="utf-8")
    INDEX.write_text(new_content, encoding="utf-8")
    print(f"Wrote {len(rows)} script entries to {README.name} and {INDEX.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())