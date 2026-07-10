"""Tests for agent_scaffold.py (stdlib unittest, no deps).

Run: python scripts/test_agent_scaffold.py
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import agent_scaffold


class TestScaffold(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-agent-scaffold-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_creates_all_expected_files(self) -> None:
        results = agent_scaffold.scaffold(self.tmp)
        statuses = dict(results)
        for rel in agent_scaffold.SCAFFOLD_FILES:
            self.assertEqual(statuses[rel], "written")
            self.assertTrue((self.tmp / rel).exists(), f"missing {rel}")

    def test_rendered_templates_are_not_placeholder_fallback(self) -> None:
        agent_scaffold.scaffold(self.tmp)
        arch = (self.tmp / "agent/AGENT_ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("Agent Architecture", arch)
        skill = (self.tmp / "agent/skills/_template/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: <skill-name>", skill)

    def test_second_run_skips_without_force(self) -> None:
        agent_scaffold.scaffold(self.tmp)
        (self.tmp / "agent/AGENT_ARCHITECTURE.md").write_text("custom content", encoding="utf-8")
        results = agent_scaffold.scaffold(self.tmp)
        statuses = dict(results)
        self.assertEqual(statuses["agent/AGENT_ARCHITECTURE.md"], "skipped (exists)")
        # user's edit must survive
        self.assertEqual(
            (self.tmp / "agent/AGENT_ARCHITECTURE.md").read_text(encoding="utf-8"), "custom content"
        )

    def test_force_overwrites(self) -> None:
        agent_scaffold.scaffold(self.tmp)
        (self.tmp / "agent/AGENT_ARCHITECTURE.md").write_text("custom content", encoding="utf-8")
        results = agent_scaffold.scaffold(self.tmp, force=True)
        statuses = dict(results)
        self.assertEqual(statuses["agent/AGENT_ARCHITECTURE.md"], "written")
        self.assertNotEqual(
            (self.tmp / "agent/AGENT_ARCHITECTURE.md").read_text(encoding="utf-8"), "custom content"
        )


if __name__ == "__main__":
    unittest.main()
