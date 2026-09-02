#!/usr/bin/env python3
"""Self-audit the Loop Engineer chain's own state.

Walks the LE app at the configured root and reports drift between the
four manifests, the skill/command/role inventories, and the install
profiles. Output is a deterministic Markdown report.

This is the chain's self-doctor. The product-facing /doctor is a
different script; this one is about the LE app itself.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Skills that a user can invoke directly with a /<name> command. The
# command name may equal the skill name (typical) or be a short alias
# declared in COMMAND_TO_SKILL. Every entry here MUST have a corresponding
# commands/<name>.md file.
DIRECT_INVOCATION_SKILLS = {
    "agent-eval",
    "agent-sort",
    "api-design",
    "ask-loop",
    "code-reviewer",
    "codebase-onboarding",
    "compact-loop",
    "config-gc",
    "contract-first",
    "council",
    "council-multi-model",
    "data-engineering",
    "decision-ledger",
    "deploy",
    "deployment-plan",
    "develop-product",
    "dev-team",
    "diagnose-loop",
    "doctor",
    "docs",
    "dynamic-workflow",
    "error-handling",
    "eval-loop",
    "feature-converge",
    "feature-new",
    "feature-workflow",
    "frontend-animation",
    "gateguard",
    "hookify-rules",
    "inherit-legacy-style",
    "living-docs-governance",
    "loop-design-check",
    "loop-engine",
    "memory-review",
    "ml-engineering",
    "migrate-import",
    "onboard",
    "operations",
    "plan-loop",
    "plan-orchestrate",
    "prod-gap",
    "qa-validation",
    "release-check",
    "research-search",
    "resolve-doubts",
    "revise-plan",
    "safeguard",
    "scope",
    "security-compliance",
    "self-audit",
    "session-end",
    "session-recall",
    "session-start",
    "setup-loop-engine",
    "skill-scout",
    "spec-checklist",
    "spec-clarify",
    "tdd",
    "ultraplan-loop",
    "upgrade-loop-engineer",
}
# Map from command name (the user types /<name>) to the skill folder name.
# Use this when a command is intentionally named differently from its
# underlying skill (e.g. /adr -> skills/architecture-decision-records/).
COMMAND_TO_SKILL = {
    "adr": "architecture-decision-records",
    "decision-ledger": "recursive-decision-ledger",
    "dynamic-workflow": "dynamic-workflow-mode",
}


def _check_command_skill_consistency(root: Path, actual_skills: set[str], actual_commands: set[str]) -> list[str]:
    """Every DIRECT_INVOCATION_SKILLS entry must have a corresponding
    commands/<name>.md file. The COMMAND_TO_SKILL allowlist covers
    intentional command-name vs skill-name divergences.
    """
    findings: list[str] = []
    for skl in sorted(DIRECT_INVOCATION_SKILLS):
        # Find the command name (either the same as the skill, or via the allowlist)
        cmd = next((c for c, s in COMMAND_TO_SKILL.items() if s == skl), skl)
        if cmd not in actual_commands:
            findings.append(
                f"direct-invocation skill {skl!r} has no commands/{cmd}.md"
            )
    return findings

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path, *, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def _walk_inventory(root: Path) -> dict[str, set[str]]:
    """Return the actual on-disk inventory of skills and commands."""
    skills = {p.parent.name for p in (root / "skills").glob("*/SKILL.md")}
    commands = {p.stem for p in (root / "commands").glob("*.md")}
    return {"skills": skills, "commands": commands}


def _check_skill_policy(root: Path, policy: dict[str, Any], actual_skills: set[str]) -> list[str]:
    findings: list[str] = []
    assignments = policy.get("assignments", {})
    actual = set(assignments)
    for name in sorted(actual_skills - actual):
        findings.append(f"skill {name!r} has no policy class assignment")
    for name in sorted(actual - actual_skills):
        findings.append(f"skill policy references missing skill: {name!r}")
    return findings


def _check_capabilities(root: Path, capabilities: dict[str, Any], actual_skills: set[str], actual_commands: set[str]) -> list[str]:
    findings: list[str] = []
    all_commands: list[str] = []
    all_skills: list[str] = []
    for cap in capabilities.get("capabilities", []):
        for cmd in cap.get("commands", []):
            all_commands.append(cmd)
            if cmd not in actual_commands:
                findings.append(f"capability {cap['id']!r} declares missing command: {cmd!r}")
        for skl in cap.get("skills", []):
            all_skills.append(skl)
            if skl not in actual_skills:
                findings.append(f"capability {cap['id']!r} declares missing skill: {skl!r}")
    # Detect multi-owner commands and skills
    cmd_dups = [name for name, count in Counter(all_commands).items() if count > 1]
    if cmd_dups:
        findings.append(f"commands with multiple owners: {', '.join(cmd_dups)}")
    skl_dups = [name for name, count in Counter(all_skills).items() if count > 1]
    if skl_dups:
        findings.append(f"skills with multiple owners: {', '.join(skl_dups)}")
    # Detect command files that have no capability
    unowned_cmds = actual_commands - set(all_commands)
    if unowned_cmds:
        findings.append(f"command files with no capability owner: {', '.join(sorted(unowned_cmds))}")
    unowned_skls = actual_skills - set(all_skills)
    if unowned_skls:
        findings.append(f"skill files with no capability owner: {', '.join(sorted(unowned_skls))}")
    return findings


def _check_profiles(capabilities: dict[str, Any], profiles: dict[str, Any], registry: CapabilityRegistry | None = None) -> list[str]:
    findings: list[str] = []
    cap_map = {c["id"]: int(c.get("context_cost", 0)) for c in capabilities.get("capabilities", [])}
    # Avoid the import path; use plain dict-based closure cost.
    def _closure_cost(cap_ids: list[str], seen: set[str] | None = None) -> tuple[int, set[str]]:
        if seen is None:
            seen = set()
        cost = 0
        for cid in cap_ids:
            if cid in seen or cid not in cap_map:
                continue
            seen.add(cid)
            cap = next(c for c in capabilities["capabilities"] if c["id"] == cid)
            for dep in cap.get("requires", []):
                child_cost, _ = _closure_cost([dep], seen)
                cost += child_cost
            cost += cap_map[cid]
        return cost, seen
    for profile in profiles.get("profiles", []):
        cost, _ = _closure_cost(profile.get("capabilities", []))
        budget = int(profile.get("context_budget", 0))
        if cost > budget:
            findings.append(
                f"profile {profile['id']!r} exceeds context budget: {cost} > {budget}"
            )
    return findings


def _check_agents(root: Path, agents: dict[str, Any], actual_skills: set[str]) -> list[str]:
    findings: list[str] = []
    role_ids = {r["id"] for r in agents.get("roles", [])}
    for role in agents.get("roles", []):
        for skill in role.get("skills", []):
            if skill not in actual_skills:
                findings.append(f"role {role['id']!r} references unknown skill: {skill!r}")
        for other in role.get("independent_from", []) + role.get("hands_off_to", []):
            if other not in role_ids:
                findings.append(f"role {role['id']!r} references unknown role: {other!r}")
    return findings


def _check_skill_activation_paths(root: Path, actual_skills: set[str], actual_commands: set[str]) -> list[str]:
    """Surface skills and commands that have NO activation path anywhere.

    A skill's activation path can be: AGENTS.md, a command, another skill,
    or a phase file under skills/<name>/phases/. The skill_audit script
    already enforces reachability as a strict rule; the self-audit
    only reports the count for a quick at-a-glance check.
    """
    activation_sources = {(root / "AGENTS.md").read_text(encoding="utf-8")}
    for base in (root / "commands", root / "skills"):
        for path in base.rglob("*.md"):
            activation_sources.add(path.read_text(encoding="utf-8"))
    unreachable_skills: list[str] = []
    for skl in actual_skills:
        canonical = f"skills/{skl}/SKILL.md"
        if not any(canonical in src for src in activation_sources):
            unreachable_skills.append(skl)
    unreachable_cmds: list[str] = []
    for cmd in actual_commands:
        canonical = f"commands/{cmd}.md"
        if not any(canonical in src for src in activation_sources):
            unreachable_cmds.append(cmd)
    findings: list[str] = []
    if unreachable_skills:
        findings.append(f"{len(unreachable_skills)} skills with no activation path: {', '.join(sorted(unreachable_skills)[:10])}{'...' if len(unreachable_skills) > 10 else ''}")
    if unreachable_cmds:
        findings.append(f"{len(unreachable_cmds)} commands with no activation path: {', '.join(sorted(unreachable_cmds)[:10])}{'...' if len(unreachable_cmds) > 10 else ''}")
    return findings


def _check_command_template(root: Path) -> list[str]:
    """Run command_audit.py as a subprocess to check command-template compliance."""
    audit_script = root / "scripts" / "command_audit.py"
    if not audit_script.exists():
        return []
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), "--root", str(root), "--json"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    if result.returncode not in (0, 1):
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    findings: list[str] = []
    for finding in data.get("findings", []):
        cmd = finding.get("command", "?")
        missing = finding.get("missing", "?")
        findings.append(f"command {cmd!r} missing canonical sections: {missing}")
    return findings


def _check_living_docs_drift(root: Path) -> list[str]:
    """Run living_docs_audit.py as a subprocess; surface drift findings as info."""
    audit_script = root / "scripts" / "living_docs_audit.py"
    if not audit_script.exists():
        return []
    try:
        result = subprocess.run(
            [sys.executable, str(audit_script), "--workspace", str(root), "--json"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return []
    if result.returncode not in (0, 1):
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    findings: list[str] = []
    for finding in data.get("findings", []):
        cat = finding.get("category", "?")
        sev = finding.get("severity", "?")
        doc = finding.get("doc", "?")
        line = finding.get("line", "?")
        rem = finding.get("remediation", "?")
        if sev in ("high", "medium"):
            findings.append(f"living-docs drift ({sev}/{cat}) at {doc}:{line}: {rem}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="LE app root")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    policy = _load(root / "manifests" / "skill_policy.json")
    capabilities = _load(root / "manifests" / "capabilities.json")
    agents = _load(root / "manifests" / "agents.json")
    profiles = _load(root / "manifests" / "install_profiles.json")
    inventory = _walk_inventory(root)

    findings: list[str] = []
    findings.extend(_check_skill_policy(root, policy, inventory["skills"]))
    findings.extend(_check_capabilities(root, capabilities, inventory["skills"], inventory["commands"]))
    findings.extend(_check_profiles(capabilities, profiles))
    findings.extend(_check_agents(root, agents, inventory["skills"]))
    findings.extend(_check_skill_activation_paths(root, inventory["skills"], inventory["commands"]))
    findings.extend(_check_command_skill_consistency(root, inventory["skills"], inventory["commands"]))
    findings.extend(_check_command_template(root))
    findings.extend(_check_living_docs_drift(root))

    if args.json:
        print(json.dumps({
            "version": 1,
            "root": str(root),
            "skills_total": len(inventory["skills"]),
            "commands_total": len(inventory["commands"]),
            "findings": findings,
        }, indent=2))
    else:
        lines = [
            "# Loop Engineer Self-Audit",
            "",
            f"- Skills: **{len(inventory['skills'])}**",
            f"- Commands: **{len(inventory['commands'])}**",
            f"- Roles: **{len(agents.get('roles', []))}**",
            f"- Capabilities: **{len(capabilities.get('capabilities', []))}**",
            f"- Profiles: **{len(profiles.get('profiles', []))}**",
            "",
            f"## Findings ({len(findings)})",
            "",
        ]
        if findings:
            for finding in findings:
                lines.append(f"- {finding}")
        else:
            lines.append("No drift detected across the four manifests and the on-disk inventory.")
        print("\n".join(lines))

    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())