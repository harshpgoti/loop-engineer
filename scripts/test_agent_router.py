from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_router import run_router, select


class AgentRouterTests(unittest.TestCase):
    def test_development_separates_builder_and_assurance_roles(self) -> None:
        roles = select("/develop-product", "", [])
        self.assertIn("builder", roles)
        self.assertIn("code-reviewer", roles)
        self.assertIn("security-reviewer", roles)

    def test_domain_signals_add_domain_reviewers(self) -> None:
        roles = select("/develop-product", "", ["data-engineering", "ml-engineering", "operations"])
        self.assertTrue({"data-reviewer", "ml-reviewer", "operations-reviewer"} <= set(roles))

    def test_diagnosis_uses_repairer_not_general_builder(self) -> None:
        roles = select("/diagnose-loop", "regression", [])
        self.assertIn("build-repairer", roles)
        self.assertNotIn("builder", roles)

    def test_write_records_authority_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_router(Path(tmp), command="/plan-loop", write=True)
            text = (Path(tmp) / "plan" / "AUTO_AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("product-manager", text)
            self.assertIn("grants no authority", text)


if __name__ == "__main__":
    unittest.main()
