from __future__ import annotations

import copy
import unittest
from pathlib import Path

from agent_registry import load, validate


ROOT = Path(__file__).resolve().parents[1]


class AgentRegistryTests(unittest.TestCase):
    def test_registry_is_valid(self) -> None:
        self.assertEqual([], validate(ROOT))

    def test_assurance_role_cannot_mutate(self) -> None:
        data = copy.deepcopy(load(ROOT))
        role = next(item for item in data["roles"] if item["class"] == "assurance")
        role["may_mutate"] = True
        self.assertTrue(any("may not mutate" in item for item in validate(ROOT, data)))

    def test_all_assurance_roles_are_independent_from_builders(self) -> None:
        for role in load(ROOT)["roles"]:
            if role["class"] == "assurance":
                self.assertTrue(role["independent_from"])

    def test_agent_evaluator_is_independent_from_agent_operator(self) -> None:
        role = next(item for item in load(ROOT)["roles"] if item["id"] == "agent-evaluator")
        self.assertIn("agent-operator", role["independent_from"])

    def test_hands_off_to_targets_must_exist(self) -> None:
        data = copy.deepcopy(load(ROOT))
        role = next(item for item in data["roles"] if item.get("hands_off_to"))
        role["hands_off_to"] = ["nonexistent-role-id"]
        errors = validate(ROOT, data)
        self.assertTrue(any("unknown hands_off_to target" in item for item in errors))

    def test_hands_off_to_cannot_target_self(self) -> None:
        data = copy.deepcopy(load(ROOT))
        role = next(item for item in data["roles"] if item.get("hands_off_to"))
        role["hands_off_to"] = [role["id"]]
        errors = validate(ROOT, data)
        self.assertTrue(any("cannot hand off to itself" in item for item in errors))

    def test_model_tier_must_be_known(self) -> None:
        data = copy.deepcopy(load(ROOT))
        role = data["roles"][0]
        role["model"] = "gpt-99"
        errors = validate(ROOT, data)
        self.assertTrue(any("unknown model tier" in item for item in errors))

    def test_model_tier_is_optional(self) -> None:
        data = copy.deepcopy(load(ROOT))
        for role in data["roles"]:
            role.pop("model", None)
        self.assertEqual([], validate(ROOT, data))

    def test_e7_prompt_defense_required(self) -> None:
        data = copy.deepcopy(load(ROOT))
        for role in data["roles"]:
            role.pop("prompt_defense", None)
        errors = validate(ROOT, data)
        self.assertTrue(any("missing prompt_defense" in item for item in errors))

    def test_e7_assurance_role_with_weak_defense_fails(self) -> None:
        data = copy.deepcopy(load(ROOT))
        for role in data["roles"]:
            if role["class"] == "assurance":
                # Keep the field but make it weak (no safeguard reference, no keywords)
                role["prompt_defense"] = "see other doc"
        errors = validate(ROOT, data)
        self.assertTrue(any("assurance role prompt_defense is weak" in item for item in errors))

    def test_e7_safeguard_reference_is_accepted(self) -> None:
        data = copy.deepcopy(load(ROOT))
        for role in data["roles"]:
            if role["class"] == "assurance":
                # Replace the embedded preamble with a reference to safeguard
                role["prompt_defense"] = (
                    "References the canonical Prompt Defense Baseline at "
                    "skills/safeguard/SKILL.md. The 6-bullet preamble is applied."
                )
        self.assertEqual([], validate(ROOT, data))


if __name__ == "__main__":
    unittest.main()
