"""Tests for scripts/command_audit.py."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout

import command_audit

REAL_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


class CommandAuditTests(unittest.TestCase):
    def test_real_chain_passes_audit(self) -> None:
        backup = sys.argv
        try:
            sys.argv = ["command_audit.py", "--root", str(REAL_ROOT), "--json"]
            buf = io.StringIO()
            with redirect_stdout(buf):
                import contextlib
                with contextlib.redirect_stdout(buf):
                    rc = command_audit.main()
            data = json.loads(buf.getvalue())
        finally:
            sys.argv = backup
        self.assertEqual(0, rc)
        self.assertEqual([], data["findings"])
        self.assertEqual(REAL_ROOT.name, data["root"].split("/")[-1] if "/" in data["root"] else data["root"].split("\\")[-1])

    def test_command_missing_section_is_flagged(self) -> None:
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "commands").mkdir()
            (tmp_path / "commands" / "stub.md").write_text(
                "# /stub\n\n## How To Interpret\n\nRun me.\n\n## Required Reads\n\n1. AGENTS.md\n\n",
                encoding="utf-8",
            )
            (tmp_path / "commands" / "full.md").write_text(
                "# /full\n\n"
                "## How To Interpret\n\nRun me.\n\n"
                "## Required Reads\n\n1. AGENTS.md\n\n"
                "## Loop\n\n1. Step one.\n\n"
                "## Output\n\n1. Done.\n\n",
                encoding="utf-8",
            )
            backup = sys.argv
            try:
                sys.argv = ["command_audit.py", "--root", str(tmp_path), "--json"]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = command_audit.main()
                data = json.loads(buf.getvalue())
            finally:
                sys.argv = backup
            self.assertEqual(1, rc)
            findings_by_cmd = {f["command"]: f for f in data["findings"]}
            self.assertIn("stub", findings_by_cmd)
            self.assertNotIn("full", findings_by_cmd)
            self.assertIn("Loop", findings_by_cmd["stub"]["missing"])
            self.assertIn("Output", findings_by_cmd["stub"]["missing"])

    def test_legacy_aliases_accepted(self) -> None:
        # A command that uses ## Purpose (instead of ## How To Interpret) and
        # ## Process (instead of ## Loop) should pass the audit.
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "commands").mkdir()
            (tmp_path / "commands" / "legacy.md").write_text(
                "# /legacy\n\n"
                "## Purpose\n\nLegacy form.\n\n"
                "## Required Reads\n\n1. AGENTS.md\n\n"
                "## Process\n\nLegacy form.\n\n"
                "## Output\n\nLegacy form.\n\n",
                encoding="utf-8",
            )
            backup = sys.argv
            try:
                sys.argv = ["command_audit.py", "--root", str(tmp_path), "--json"]
                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = command_audit.main()
                data = json.loads(buf.getvalue())
            finally:
                sys.argv = backup
            self.assertEqual(0, rc)
            self.assertEqual([], data["findings"])


if __name__ == "__main__":
    unittest.main()