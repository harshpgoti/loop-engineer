"""Tests for scripts/living_docs_audit.py, scripts/dev.py, and scripts/chain_bench.py."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import living_docs_audit
import dev
import chain_bench

REAL_ROOT = Path(__file__).resolve().parents[1]


class LivingDocsAuditTests(unittest.TestCase):
    def test_clean_workspace_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "AGENTS.md").write_text("# AGENTS\n\n", encoding="utf-8")
            (tmp_path / "README.md").write_text("# README\n\n", encoding="utf-8")
            report = living_docs_audit.audit(tmp_path)
            # No outdated commands, no dead links, no stale tables.
            outdated = [f for f in report.findings if f.category == "outdated-command"]
            self.assertEqual([], outdated)

    def test_outdated_command_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "AGENTS.md").write_text(
                "# AGENTS\n\nRun /nonexistent-cmd today.\n",
                encoding="utf-8",
            )
            report = living_docs_audit.audit(tmp_path)
            outdated = [f for f in report.findings if f.category == "outdated-command"]
            self.assertEqual(1, len(outdated))
            self.assertIn("nonexistent-cmd", outdated[0].actual)

    def test_dead_link_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "AGENTS.md").write_text(
                "# AGENTS\n\n[missing](docs/missing.md)\n",
                encoding="utf-8",
            )
            report = living_docs_audit.audit(tmp_path)
            dead = [f for f in report.findings if f.category == "dead-link"]
            self.assertEqual(1, len(dead))
            self.assertIn("docs/missing.md", dead[0].actual)

    def test_word_slash_does_not_match_path_segment(self) -> None:
        # /cmd inside a file path (e.g. plan/main_plan.md) should NOT be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "AGENTS.md").write_text(
                "# AGENTS\n\nSee `plan/main_plan.md` for the structure.\n",
                encoding="utf-8",
            )
            report = living_docs_audit.audit(tmp_path)
            outdated = [f for f in report.findings if f.category == "outdated-command"]
            self.assertEqual([], outdated)

    def test_real_le_home_audit_runs(self) -> None:
        # Smoke test: the script runs against the LE home and produces a
        # valid report structure.
        report = living_docs_audit.audit(REAL_ROOT)
        self.assertGreaterEqual(report.docs_scanned, 1)
        # No exception; high+medium+low counts add up.
        self.assertEqual(len(report.findings), report.high_count + report.medium_count + report.low_count)


class DevCommandTests(unittest.TestCase):
    def test_no_config_emits_clear_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            backup_argv = sys.argv
            try:
                sys.argv = ["dev.py", "--workspace", str(tmp_path), "lint"]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = dev.main()
                self.assertEqual(1, rc)
                self.assertIn("lint.command", buf.getvalue())
            finally:
                sys.argv = backup_argv

    def test_commit_validates_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / ".loop").mkdir()
            (tmp_path / ".loop" / "dev_config.json").write_text(
                json.dumps({
                    "commit": {
                        "template": "<type>(<scope>): <subject>",
                        "types": ["feat", "fix"],
                        "max_subject_length": 72,
                    }
                }),
                encoding="utf-8",
            )
            backup_argv = sys.argv
            try:
                # Bad type
                sys.argv = ["dev.py", "--workspace", str(tmp_path), "commit",
                            "--message", "wip(scripts): thing"]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = dev.main()
                self.assertEqual(1, rc)
                self.assertIn("not in allowed types", buf.getvalue())

                # Good message but no git repo
                sys.argv = ["dev.py", "--workspace", str(tmp_path), "commit",
                            "--message", "feat(scripts): add /lint"]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = dev.main()
                # 0 or 1 depending on whether the workspace happens to be a git repo
                # (the validation passed; the git call is what fails next)
                # Validation passed (script reached git add -A); we cannot
                # actually commit in a temp dir, so the test passes if git add
                # was attempted.
                self.assertIn("$ git add -A", buf.getvalue())
            finally:
                sys.argv = backup_argv


class ChainBenchTests(unittest.TestCase):
    """Run chain_bench.benchmark in a real temp dir; assert the structure."""

    def test_bench_outputs_valid_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "skills").mkdir()
            (tmp_path / "skills" / "a" / "SKILL.md").parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / "skills" / "a" / "SKILL.md").write_text("# a\n", encoding="utf-8")
            (tmp_path / "commands").mkdir()
            (tmp_path / "commands" / "x.md").write_text("# /x\n", encoding="utf-8")
            (tmp_path / "manifests").mkdir()
            (tmp_path / "manifests" / "skill_policy.json").write_text(
                json.dumps({"assignments": {"a": "read-only"}}), encoding="utf-8"
            )
            (tmp_path / "manifests" / "capabilities.json").write_text(
                json.dumps({"capabilities": [{"id": "foundation", "commands": ["x"]}]}),
                encoding="utf-8",
            )
            (tmp_path / "manifests" / "agents.json").write_text(
                json.dumps({"roles": [{"id": "r1", "class": "planner"}]}),
                encoding="utf-8",
            )
            report = chain_bench.benchmark(tmp_path)
            self.assertEqual(1, report["skills"]["skills_total"])
            self.assertEqual(1, report["commands"]["commands_total"])
            self.assertEqual(1, report["roles"]["roles_total"])
            # JSON output is a valid JSON object
            text = json.dumps(report)
            self.assertIsInstance(json.loads(text), dict)


if __name__ == "__main__":
    unittest.main()