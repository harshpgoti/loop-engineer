#!/usr/bin/env python3
"""Verify every command in commands/ resolves to a known skill folder.

Allowed aliases (per AGENTS.md):
  adr                  -> architecture-decision-records
  decision-ledger      -> recursive-decision-ledger
  dynamic-workflow     -> dynamic-workflow-mode
  compact-loop         -> compact-loop   (canonical)
  session-start        -> session-lifecycle
  session-end          -> session-lifecycle
  session-recall       -> session-recall   (canonical)
  skill-list           -> chain-meta (the skill folder); chain-meta/SKILL.md is what backs /skill-list
  roles                -> chain-meta (the skill folder)
  self-audit           -> chain-meta
  onboard              -> contributor-onboarding
  lint/test/format/commit -> dev-tooling
  front-end-animation / frontend-animation -> frontend-animation
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(r"H:\Raghav-Health\Loop engineering")

COMMANDS_DIR = ROOT / "commands"
SKILLS_DIR = ROOT / "skills"

# Build the set of skill folder names that actually exist on disk
EXISTING_SKILLS = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}

# Read every command body, find the first reference to `skills/<x>/SKILL.md`
SLASH_REF = re.compile(r"skills/([a-z0-9\-]+)/", re.IGNORECASE)

# Aliases: command-stem -> skill-folder-name
ALIASES = {
    "adr": "architecture-decision-records",
    "decision-ledger": "recursive-decision-ledger",
    "dynamic-workflow": "dynamic-workflow-mode",
    "session-start": "session-lifecycle",
    "session-end": "session-lifecycle",
    "skill-list": "chain-meta",
    "roles": "chain-meta",
    "self-audit": "chain-meta",
    "onboard": "contributor-onboarding",
    "lint": "dev-tooling",
    "test": "dev-tooling",
    "format": "dev-tooling",
    "commit": "dev-tooling",
}

def resolve(command_stem: str) -> str:
    if command_stem in ALIASES:
        return ALIASES[command_stem]
    return command_stem

problems: list[tuple[str, str, str]] = []  # (cmd_file, found_pattern, reason)
matches: list[tuple[str, str]] = []  # (cmd_file, skill_folder)

for cmd_file in sorted(COMMANDS_DIR.iterdir()):
    if cmd_file.suffix != ".md":
        continue
    stem = cmd_file.stem
    text = cmd_file.read_text(encoding="utf-8")
    refs = SLASH_REF.findall(text)
    if not refs:
        problems.append((str(cmd_file.relative_to(ROOT)), "<no skills/<x>/SKILL.md ref>", "no-ref"))
        continue
    # Take the first reference; that's the canonical skill backing the command
    target_skill = resolve(refs[0])
    matches.append((str(cmd_file.relative_to(ROOT)), target_skill))
    if target_skill not in EXISTING_SKILLS:
        problems.append(
            (str(cmd_file.relative_to(ROOT)), f"-> skills/{target_skill}/SKILL.md", "missing-skill-folder")
        )

print(f"# Commands scanned: {len(matches)}")
print(f"# Problems: {len(problems)}")
if problems:
    print("\n## PROBLEMS:")
    for cmd, pat, reason in problems:
        print(f"  - {cmd}: {pat}  ({reason})")
else:
    print("\n## All commands resolve to existing skill folders.")

# Cross-check: every existing skill folder should be referenced by at least one
# command (unless it's a phase folder or an internal scaffolding skill).
referenced_skills = {s for _, s in matches}
unreferenced = sorted(EXISTING_SKILLS - referenced_skills)
print(f"\n# Skill folders on disk: {len(EXISTING_SKILLS)}")
print(f"# Skill folders referenced by commands: {len(referenced_skills)}")
print(f"# Unreferenced (allowed: phases, scaffolding, agents, internals): {len(unreferenced)}")
for s in unreferenced:
    print(f"  - {s}")