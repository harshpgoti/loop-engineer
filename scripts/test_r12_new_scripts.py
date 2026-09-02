"""Tests for scripts/codehealth.py, scripts/iterative_retrieval.py, scripts/automation_audit.py, scripts/dashboard.py."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import codehealth
import iterative_retrieval
import automation_audit
import dashboard

REAL_ROOT = Path(__file__).resolve().parents[1]


class CodehealthTests(unittest.TestCase):
    def test_emits_valid_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "src").mkdir()
            (tmp_path / "src" / "foo.py").write_text("x = 1  # TODO\n", encoding="utf-8")
            (tmp_path / "src" / "bar.py").write_text("y = 2  # FIXME\n", encoding="utf-8")
            backup_argv = sys.argv
            try:
                sys.argv = ["codehealth.py", "--workspace", str(tmp_path)]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = codehealth.main()
                self.assertEqual(0, rc)
                data = json.loads(buf.getvalue())
            finally:
                sys.argv = backup_argv
            self.assertIn("lint_debt", data["signals"])
            self.assertGreaterEqual(data["signals"]["lint_debt"]["total"], 2)


class IterativeRetrievalTests(unittest.TestCase):
    def test_three_rounds_with_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            corpus = tmp_path / "corpus"
            corpus.mkdir()
            (corpus / "a.md").write_text(
                "The chain has skills, commands, roles, capabilities, and harnesses.",
                encoding="utf-8",
            )
            (corpus / "b.md").write_text(
                "Skills are organised into capabilities. Commands back skills.",
                encoding="utf-8",
            )
            (corpus / "c.md").write_text(
                "Roles declare model and hands_off_to. Agents.json is the manifest.",
                encoding="utf-8",
            )
            backup_argv = sys.argv
            try:
                sys.argv = [
                    "iterative_retrieval.py",
                    "--workspace", str(tmp_path),
                    "--query", "how are skills organised",
                    "--corpus", str(corpus),
                ]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = iterative_retrieval.main()
                self.assertEqual(0, rc)
                report = json.loads(buf.getvalue())
            finally:
                sys.argv = backup_argv
            self.assertEqual(3, len(report["rounds"]))
            self.assertIn("synthesis", report)
            self.assertIn("citations", report)
            self.assertGreaterEqual(len(report["citations"]), 1)


class AutomationAuditTests(unittest.TestCase):
    def test_walks_real_le_home(self) -> None:
        report = automation_audit._classify(
            automation_audit._walk_hooks(REAL_ROOT)
            + automation_audit._walk_harnesses(REAL_ROOT)
            + automation_audit._walk_scripts(REAL_ROOT)
            + automation_audit._walk_manifests(REAL_ROOT)
        )
        self.assertGreater(len(report["healthy"]) + len(report["stale"]), 0)

    def test_render_markdown_has_sections(self) -> None:
        report = automation_audit._classify([
            {"source": "scripts/foo.py", "type": "script", "name": "foo", "has_test": False},
            {"source": "harnesses/x.json", "type": "harness", "name": "x", "trust": "?"},
        ])
        output = automation_audit.render_markdown(report)
        self.assertIn("# Automation Audit", output)
        self.assertIn("Stale", output)


class DashboardTests(unittest.TestCase):
    def test_renders_simple_spec(self) -> None:
        spec = {"title": "Test Dashboard", "panels": [{"title": "Count", "type": "counter", "source": "echo 42"}]}
        panels = [
            dashboard._render_panel("Count", 42, "counter"),
        ]
        html = dashboard.render_html(spec, panels)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("Test Dashboard", html)
        self.assertIn("Count", html)
        self.assertIn(">42<", html)

    def test_no_data_panel_renders_gracefully(self) -> None:
        panel = dashboard._render_panel("Missing", None, "counter")
        self.assertIn("no data", panel)


if __name__ == "__main__":
    unittest.main()