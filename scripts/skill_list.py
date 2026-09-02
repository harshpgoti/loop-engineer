#!/usr/bin/env python3
"""List the Loop Engineer chain's skills with class, capability, and reachability.

Emits a Markdown table by default; --json for tooling. The output is the
single source of truth for "what does the chain have?" — the user can
ask /skill-list and get an answer without grepping the directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path, *, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_owners(capabilities: dict[str, Any]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Return (skill->capability, command->capability) maps."""
    skill_owner: dict[str, str] = {}
    command_owner: dict[str, list[str]] = defaultdict(list)
    for cap in capabilities.get("capabilities", []):
        for skl in cap.get("skills", []):
            skill_owner[skl] = cap["id"]
        for cmd in cap.get("commands", []):
            command_owner[cmd].append(cap["id"])
    return skill_owner, dict(command_owner)


def _activation_paths(root: Path) -> dict[str, list[str]]:
    """For each skill, list the activation sources (AGENTS.md, command, etc.)."""
    sources: dict[str, list[str]] = {}
    ag = root / "AGENTS.md"
    ag_text = ag.read_text(encoding="utf-8") if ag.exists() else ""
    for path in (root / "skills").glob("*/SKILL.md"):
        skill = path.parent.name
        paths_found: list[str] = []
        if f"skills/{skill}/SKILL.md" in ag_text:
            paths_found.append("AGENTS.md")
        for cmd in (root / "commands").glob("*.md"):
            if f"skills/{skill}/SKILL.md" in cmd.read_text(encoding="utf-8", errors="ignore"):
                paths_found.append(f"commands/{cmd.stem}.md")
        for other in (root / "skills").glob("*/SKILL.md"):
            if other == path:
                continue
            if f"skills/{skill}/SKILL.md" in other.read_text(encoding="utf-8", errors="ignore"):
                paths_found.append(f"skills/{other.parent.name}/SKILL.md")
        sources[skill] = paths_found
    return sources


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--class", dest="class_filter", default=None, help="Filter by class (e.g. assurance)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    policy = _load_json(root / "manifests" / "skill_policy.json")
    capabilities = _load_json(root / "manifests" / "capabilities.json")
    assignments = policy.get("assignments", {})

    skills = sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md") if p.parent.name != "SKILL.md")
    skill_owner, _ = _build_owners(capabilities)
    sources = _activation_paths(root)

    if args.class_filter:
        skills = [s for s in skills if assignments.get(s) == args.class_filter]

    rows = [
        {
            "skill": skl,
            "class": assignments.get(skl, "?"),
            "capability": skill_owner.get(skl, "unowned"),
            "activation_paths": sources.get(skl, []),
        }
        for skl in skills
    ]

    if args.json:
        print(json.dumps({"version": 1, "count": len(rows), "skills": rows}, indent=2))
    else:
        lines = [
            "# Loop Engineer — Skill List",
            "",
            f"Total skills: **{len(rows)}**",
            "",
            "| Skill | Class | Capability | Activation paths |",
            "|---|---|---|---|",
        ]
        for row in rows:
            paths = ", ".join(row["activation_paths"]) if row["activation_paths"] else "—"
            lines.append(f"| `{row['skill']}` | {row['class']} | {row['capability']} | {paths} |")
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())