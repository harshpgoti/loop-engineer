"""Tests for round 14: the 11 new roles and skills have valid structure.

Each new skill must:
- have a valid frontmatter (name, description)
- Inherit docs/SKILL_CONTRACT.md
- have at least one E-pattern section (Approval Criteria, Stop Conditions,
  Pre-Report Gate, Common False Positives, or Prompt Defense Baseline)
- not be empty

Each new role must:
- have a class and may_mutate
- have a model in the known set
- have a non-empty prompt_defense
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NEW_SKILLS = [
    "code-simplifier", "comment-analyzer", "performance-optimizer",
    "refactor-cleaner", "type-design-analyzer", "harness-optimizer",
    "pr-test-analyzer", "conversation-analyzer", "network-architect",
    "network-troubleshooter", "network-config-reviewer",
]
NEW_ROLES = [
    "code-simplifier", "comment-analyzer", "performance-optimizer",
    "refactor-cleaner", "type-design-analyzer", "harness-optimizer",
    "pr-test-analyzer", "conversation-analyzer", "network-architect",
    "network-troubleshooter", "network-config-reviewer",
]
E_PATTERN_HEADINGS = (
    "Pre-Report Gate",
    "Common False Positives",
    "Stop Conditions",
    "Approval Criteria",
    "Prompt Defense Baseline",
    "E3",
    "E5",
    "E7",
)


class R14SkillStructureTests(unittest.TestCase):
    def test_each_new_skill_has_frontmatter_and_inherits(self) -> None:
        for name in NEW_SKILLS:
            p = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(p.is_file(), f"missing skill file: {p}")
            text = p.read_text(encoding="utf-8")
            self.assertTrue(
                text.startswith("---"),
                f"{name}: must start with YAML frontmatter",
            )
            self.assertIn("name:", text[:200], f"{name}: frontmatter missing name")
            self.assertIn("description:", text[:500], f"{name}: frontmatter missing description")
            self.assertIn(
                "Inherits `docs/SKILL_CONTRACT.md`",
                text,
                f"{name}: must inherit the SKILL_CONTRACT",
            )
            self.assertGreater(
                len(text.splitlines()), 30,
                f"{name}: skill body is too short (likely a stub)",
            )

    def test_each_new_skill_has_at_least_one_e_pattern(self) -> None:
        for name in NEW_SKILLS:
            p = ROOT / "skills" / name / "SKILL.md"
            text = p.read_text(encoding="utf-8")
            has_e_pattern = any(
                re.search(rf"^##\s*{re.escape(heading)}", text, re.MULTILINE)
                for heading in E_PATTERN_HEADINGS
            )
            self.assertTrue(
                has_e_pattern,
                f"{name}: no E-pattern heading found (need one of {E_PATTERN_HEADINGS})",
            )

    def test_each_new_skill_has_command_file(self) -> None:
        for name in NEW_SKILLS:
            cmd = ROOT / "commands" / f"{name}.md"
            self.assertTrue(cmd.is_file(), f"missing command file: {cmd}")


class R14RoleStructureTests(unittest.TestCase):
    def setUp(self) -> None:
        import json
        self.agents = json.loads((ROOT / "manifests" / "agents.json").read_text(encoding="utf-8"))

    def test_each_new_role_exists_with_class_and_model(self) -> None:
        by_id = {r["id"]: r for r in self.agents["roles"]}
        for name in NEW_ROLES:
            self.assertIn(name, by_id, f"role {name!r} not in agents.json")
            role = by_id[name]
            self.assertIn(role["class"], {"planner", "executor", "assurance", "controller"})
            self.assertIn(role.get("model"), {"opus", "sonnet", "haiku"})

    def test_each_new_role_has_prompt_defense(self) -> None:
        by_id = {r["id"]: r for r in self.agents["roles"]}
        for name in NEW_ROLES:
            role = by_id[name]
            self.assertIn("prompt_defense", role, f"{name}: missing prompt_defense")
            self.assertGreater(len(role["prompt_defense"]), 20, f"{name}: prompt_defense too short")

    def test_assurance_roles_have_independent_from(self) -> None:
        by_id = {r["id"]: r for r in self.agents["roles"]}
        for name in NEW_ROLES:
            role = by_id[name]
            if role["class"] == "assurance":
                self.assertTrue(
                    role.get("independent_from"),
                    f"assurance role {name} must have independent_from",
                )

    def test_each_new_role_has_hands_off_to(self) -> None:
        by_id = {r["id"]: r for r in self.agents["roles"]}
        for name in NEW_ROLES:
            role = by_id[name]
            self.assertTrue(
                role.get("hands_off_to"),
                f"role {name}: missing hands_off_to",
            )


if __name__ == "__main__":
    unittest.main()