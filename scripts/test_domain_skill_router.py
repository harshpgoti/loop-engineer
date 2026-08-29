from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from domain_skill_router import run_router, select
from session_lifecycle import render_manifest


class DomainSkillRouterTests(unittest.TestCase):
    def test_selects_each_domain_from_task_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            picks = dict(select(workspace, "database migration, model training drift, SLO backup runbook"))
            self.assertEqual({"data-engineering", "ml-engineering", "operations"}, set(picks))

    def test_avoids_substring_false_positive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], select(Path(tmp), "restoredbx is unrelated"))

    def test_write_records_selection_and_authority_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            run_router(workspace, extra="warehouse lineage", write=True)
            report = (workspace / "plan" / "AUTO_DOMAIN_SKILLS.md").read_text(encoding="utf-8")
            self.assertIn("data-engineering", report)
            self.assertIn("does not grant external-action authority", report)

    def test_session_manifest_exposes_selected_domain_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rendered = render_manifest(
                Path(tmp), command="/develop-product", tool="test", hits=0,
                auto_skills=[], auto_agent_skills=[], auto_domain_skills=["ml-engineering"]
            )
            self.assertIn("## Auto domain skills", rendered)
            self.assertIn("plan/AUTO_DOMAIN_SKILLS.md", rendered)


if __name__ == "__main__":
    unittest.main()
