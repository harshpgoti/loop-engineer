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


if __name__ == "__main__":
    unittest.main()
