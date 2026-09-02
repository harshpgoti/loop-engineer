#!/usr/bin/env python3
"""Chain catalog: a single command that emits the full chain surface as one
Markdown page.

Walks `manifests/`, `skills/`, `commands/`, and `harnesses/` and emits a
catalog that lists every skill (with class and capability), every command
(with capability and target skill), every role (with class, model,
skills, and handoffs), and every harness. The output is a single
discoverable page for a maintainer or a new contributor.

Usage:
    python scripts/chain_catalog.py --root <le-app>
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path, *, default: dict | list = None) -> Any:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def _first_paragraph(path: Path) -> str:
    """Extract the first paragraph of a skill's body for the catalog."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if lines:
                break
            continue
        lines.append(stripped)
        if len(" ".join(lines)) > 280:
            break
    return " ".join(lines)[:280]


def build(root: Path) -> dict[str, Any]:
    policy = _load_json(root / "manifests" / "skill_policy.json")
    capabilities = _load_json(root / "manifests" / "capabilities.json")
    agents = _load_json(root / "manifests" / "agents.json")
    profiles = _load_json(root / "manifests" / "install_profiles.json")

    assignments = policy.get("assignments", {})
    skill_caps: dict[str, list[str]] = defaultdict(list)
    cmd_caps: dict[str, list[str]] = defaultdict(list)
    cap_meta: dict[str, dict[str, Any]] = {}
    for cap in capabilities.get("capabilities", []):
        cap_meta[cap["id"]] = {
            "summary": cap.get("summary", ""),
            "context_cost": cap.get("context_cost", 0),
            "requires": cap.get("requires", []),
        }
        for skl in cap.get("skills", []):
            skill_caps[skl].append(cap["id"])
        for cmd in cap.get("commands", []):
            cmd_caps[cmd].append(cap["id"])

    skills: list[dict[str, Any]] = []
    for p in sorted((root / "skills").glob("*/SKILL.md")):
        name = p.parent.name
        skills.append({
            "name": name,
            "class": assignments.get(name, "?"),
            "capabilities": skill_caps.get(name, []),
            "summary": _first_paragraph(p),
        })

    commands: list[dict[str, Any]] = []
    for p in sorted((root / "commands").glob("*.md")):
        name = p.stem
        commands.append({
            "name": name,
            "capabilities": cmd_caps.get(name, []),
            "summary": _first_paragraph(p),
        })

    roles = agents.get("roles", [])

    harnesses: list[dict[str, str]] = []
    for p in sorted((root / "harnesses").glob("*.json")):
        if p.name in {"worker_versions.json"}:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        harnesses.append({
            "name": p.stem,
            "trust": data.get("trust", ""),
            "invocation": data.get("invocation", ""),
        })

    return {
        "version": 1,
        "root": str(root),
        "skills": skills,
        "commands": commands,
        "roles": roles,
        "capabilities": cap_meta,
        "profiles": profiles.get("profiles", []),
        "harnesses": harnesses,
    }


def render_markdown(report: dict[str, Any]) -> str:
    skills = report["skills"]
    commands = report["commands"]
    roles = report["roles"]
    caps = report["capabilities"]
    profiles = report["profiles"]
    harnesses = report["harnesses"]

    lines: list[str] = [
        "# Loop Engineer — Chain Catalog",
        "",
        f"Root: `{report['root']}`",
        "",
        "A single-page catalog of every skill, command, role, capability,",
        "and harness in the chain. Useful for a maintainer onboarding,",
        "for a maintainer evaluating a new contribution, and for an",
        "agent discovering what's available.",
        "",
        "## Capabilities",
        "",
        "| Capability | Context cost | Summary |",
        "|---|---|---|",
    ]
    for cap_id, meta in sorted(caps.items()):
        lines.append(
            f"| `{cap_id}` | {meta['context_cost']} | {meta['summary']} |"
        )
    lines.append("")

    lines.append("## Skills")
    lines.append("")
    lines.append(f"Total: **{len(skills)}**")
    lines.append("")
    lines.append("| Skill | Class | Capabilities | Summary |")
    lines.append("|---|---|---|---|")
    for s in skills:
        caps_str = ", ".join(f"`{c}`" for c in s["capabilities"]) or "—"
        lines.append(
            f"| `{s['name']}` | {s['class']} | {caps_str} | {s['summary']} |"
        )
    lines.append("")

    lines.append("## Commands")
    lines.append("")
    lines.append(f"Total: **{len(commands)}**")
    lines.append("")
    lines.append("| Command | Capabilities | Summary |")
    lines.append("|---|---|---|")
    for c in commands:
        caps_str = ", ".join(f"`{cap}`" for cap in c["capabilities"]) or "—"
        lines.append(f"| `/{c['name']}` | {caps_str} | {c['summary']} |")
    lines.append("")

    lines.append("## Roles")
    lines.append("")
    lines.append(f"Total: **{len(roles)}**")
    lines.append("")
    lines.append("| Role | Class | Model | may_mutate | Skills | Hands off to | Independent from |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in roles:
        skills_str = ", ".join(r.get("skills", [])) or "—"
        hands_str = ", ".join(r.get("hands_off_to", [])) or "—"
        indep_str = ", ".join(r.get("independent_from", [])) or "—"
        lines.append(
            f"| `{r.get('id', '?')}` | {r.get('class', '?')} | {r.get('model', '?')} | "
            f"{r.get('may_mutate', False)} | {skills_str} | {hands_str} | {indep_str} |"
        )
    lines.append("")

    lines.append("## Install Profiles")
    lines.append("")
    for p in profiles:
        caps = ", ".join(f"`{c}`" for c in p.get("capabilities", []))
        lines.append(f"- **`{p.get('id', '?')}`** — {p.get('summary', '')}. Capabilities: {caps}. Budget: {p.get('context_budget', 0)}.")
    lines.append("")

    lines.append("## Harnesses")
    lines.append("")
    lines.append(f"Total: **{len(harnesses)}**")
    lines.append("")
    lines.append("| Harness | Trust | Invocation |")
    lines.append("|---|---|---|")
    for h in harnesses:
        lines.append(f"| `{h['name']}` | {h['trust']} | `{h['invocation']}` |")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None, help="Write the catalog to this file")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = build(root)
    if args.json:
        output = json.dumps(report, indent=2)
    else:
        output = render_markdown(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())