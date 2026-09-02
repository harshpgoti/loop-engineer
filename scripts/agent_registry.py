#!/usr/bin/env python3
"""Validate canonical agent roles and their skill/independence contracts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "manifests" / "agents.json").read_text(encoding="utf-8"))


def validate(root: Path = ROOT, data: dict[str, Any] | None = None) -> list[str]:
    data = data or load(root)
    roles = data.get("roles", [])
    ids = [item.get("id") for item in roles]
    errors = [f"duplicate agent role: {name}" for name, count in Counter(ids).items() if count > 1]
    known = set(ids)
    skills = {path.parent.name for path in (root / "skills").glob("*/SKILL.md")}
    valid_models = {"opus", "sonnet", "haiku"}
    safeguard_keywords = (
        "role, persona, or identity",
        "confidential data",
        "executable code",
        "unicode",
        "untrusted",
        "harmful",
    )
    for role in roles:
        for skill in role.get("skills", []):
            if skill not in skills:
                errors.append(f"{role.get('id')} references unknown skill: {skill}")
        for other in role.get("independent_from", []):
            if other not in known:
                errors.append(f"{role.get('id')} has unknown independence target: {other}")
            if other == role.get("id"):
                errors.append(f"{role.get('id')} cannot be independent from itself")
        for other in role.get("hands_off_to", []):
            if other not in known:
                errors.append(f"{role.get('id')} has unknown hands_off_to target: {other}")
            if other == role.get("id"):
                errors.append(f"{role.get('id')} cannot hand off to itself")
        model = role.get("model")
        if model is not None and model not in valid_models:
            errors.append(f"{role.get('id')} has unknown model tier: {model!r}")
        # E7: every role must declare a prompt_defense that either references
        # the safeguard skill or embeds >= 3 of the 6 baseline keywords.
        defense = role.get("prompt_defense") or ""
        defense_lower = defense.lower()
        references_safeguard = "skills/safeguard" in defense_lower or "safeguard/skill.md" in defense_lower
        kw_hits = sum(1 for kw in safeguard_keywords if kw in defense_lower)
        if not defense.strip():
            errors.append(f"{role.get('id')} missing prompt_defense field (E7)")
        elif role.get("class") == "assurance" and kw_hits < 3 and not references_safeguard:
            errors.append(
                f"{role.get('id')} assurance role prompt_defense is weak "
                f"({kw_hits}/6 baseline keywords; no safeguard reference)"
            )
        if role.get("class") == "assurance" and role.get("may_mutate"):
            errors.append(f"assurance role may not mutate reviewed work: {role.get('id')}")
        if role.get("class") == "assurance" and not role.get("independent_from"):
            errors.append(f"assurance role lacks independence boundary: {role.get('id')}")
    return sorted(errors)


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Agent registry OK: {len(load()['roles'])} governed roles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
