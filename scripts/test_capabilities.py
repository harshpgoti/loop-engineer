from __future__ import annotations

import copy
import unittest
from pathlib import Path

from capabilities import CapabilityRegistry


ROOT = Path(__file__).resolve().parents[1]


class CapabilityRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = CapabilityRegistry.load(ROOT)

    def test_repository_registry_is_valid_and_complete(self) -> None:
        self.assertEqual([], self.registry.validate())

    def test_every_public_command_and_skill_has_one_owner(self) -> None:
        commands = {path.stem for path in (ROOT / "commands").glob("*.md")}
        skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
        self.assertEqual(commands, set(self.registry.command_owners))
        self.assertEqual(skills, set(self.registry.skill_owners))

    def test_profiles_include_dependency_closure_and_respect_budget(self) -> None:
        for name in self.registry.profiles:
            plan = self.registry.plan(name)
            self.assertLessEqual(plan["context_cost"], plan["context_budget"])
            for capability in plan["capabilities"]:
                self.assertTrue(set(self.registry.capabilities[capability]["requires"]) <= set(plan["capabilities"]))

    def test_explain_resolves_command_skill_and_capability(self) -> None:
        self.assertEqual("delivery", self.registry.explain("develop-product")["id"])
        self.assertEqual("quality", self.registry.explain("tdd")["id"])
        self.assertEqual("security", self.registry.explain("security")["id"])

    def test_map_renders_every_registered_capability(self) -> None:
        rendered = self.registry.render_map()
        for capability in self.registry.capabilities:
            self.assertIn(f"| {capability} |", rendered)

    def test_duplicate_ownership_is_rejected(self) -> None:
        data = copy.deepcopy(self.registry.registry_data)
        data["capabilities"][1]["commands"].append(data["capabilities"][0]["commands"][0])
        broken = CapabilityRegistry(ROOT, data, self.registry.profile_data)
        self.assertTrue(any("multiple owners" in item for item in broken.validate()))

    def test_cycles_are_rejected(self) -> None:
        data = copy.deepcopy(self.registry.registry_data)
        data["capabilities"][0]["requires"] = [data["capabilities"][1]["id"]]
        data["capabilities"][1]["requires"] = [data["capabilities"][0]["id"]]
        broken = CapabilityRegistry(ROOT, data, self.registry.profile_data)
        self.assertTrue(any("dependency cycle" in item for item in broken.validate()))

    def test_unsupported_harness_is_rejected(self) -> None:
        data = copy.deepcopy(self.registry.registry_data)
        data["capabilities"][0]["harnesses"].append("unknown-harness")
        broken = CapabilityRegistry(ROOT, data, self.registry.profile_data)
        self.assertTrue(any("unsupported harnesses" in item for item in broken.validate()))

    def test_profile_over_budget_is_rejected(self) -> None:
        profiles = copy.deepcopy(self.registry.profile_data)
        profiles["profiles"][0]["context_budget"] = 0
        broken = CapabilityRegistry(ROOT, self.registry.registry_data, profiles)
        self.assertTrue(any("exceeds context budget" in item for item in broken.validate()))


if __name__ == "__main__":
    unittest.main()
