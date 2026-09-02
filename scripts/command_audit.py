"""Audit the chain's command files for canonical-template compliance.

Every command file should have these H2 sections, in this order:
- ## How To Interpret
- ## Required Reads
- ## Loop
- ## Output

Optionally:
- ## Continuation
- ## Related Skills
- ## Public invocation
- ## Stop Conditions (and / or ## Stop Conditions and Rollback)
- ## Script
- ## Trigger Conditions

This script reports which command files have which sections, and lists
the ones missing required sections.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Canonical sections and the legacy aliases that satisfy them.
# A command may use either the canonical name or a legacy alias.
REQUIRED_SECTIONS: dict[str, list[str]] = {
    "How To Interpret": ["## How To Interpret", "## Purpose"],
    "Required Reads": ["## Required Reads"],
    "Loop": ["## Loop", "## Process"],
    "Output": ["## Output"],
}
OPTIONAL_SECTIONS = [
    "## Continuation",
    "## Related Skills",
    "## Public invocation",
    "## Script",
    "## Trigger Conditions",
    "## Stop Conditions and Rollback",
    "## Stop Conditions",
    "## Rollback",
]

OPTIONAL_SECTIONS = [
    "## Continuation",
    "## Related Skills",
    "## Public invocation",
    "## Script",
    "## Trigger Conditions",
    "## Stop Conditions and Rollback",
    "## Stop Conditions",
    "## Rollback",
]


def _has_section(text: str, aliases: list[str]) -> bool:
    return any(alias in text for alias in aliases)


def audit(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for path in sorted((root / "commands").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        present = {s for s in OPTIONAL_SECTIONS if s in text}
        missing = [
            name for name, aliases in REQUIRED_SECTIONS.items()
            if not _has_section(text, aliases)
        ]
        if missing:
            findings.append({
                "command": path.stem,
                "path": f"commands/{path.name}",
                "missing": ",".join(missing),
            })
    return {
        "version": 1,
        "root": str(root),
        "total_commands": len(list((root / "commands").glob("*.md"))),
        "findings": findings,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Command-Template Audit",
        "",
        f"Total commands: **{result['total_commands']}**",
        f"Commands missing required sections: **{len(result['findings'])}**",
        "",
    ]
    if not result["findings"]:
        lines.append("All command files have the canonical sections.")
    else:
        lines.append("| Command | Missing sections |")
        lines.append("|---|---|")
        for finding in result["findings"]:
            lines.append(f"| `{finding['command']}` | {finding['missing']} |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    result = audit(root)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_markdown(result))
    return 0 if not result["findings"] else 1


if __name__ == "__main__":
    raise SystemExit(main())