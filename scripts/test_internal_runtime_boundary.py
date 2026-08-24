"""The shell runner is an internal compatibility bridge, not the user interface."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "loop_cli.py"


class InternalRuntimeBoundary(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_presents_slash_commands_as_the_public_interface(self) -> None:
        result = self.run_cli("--help")

        self.assertEqual(0, result.returncode)
        self.assertIn("Internal deterministic runtime", result.stdout)
        self.assertIn("/plan-loop", result.stdout)
        self.assertIn("coding agent", result.stdout)

    def test_free_form_plan_cli_is_compatibility_only(self) -> None:
        with tempfile.TemporaryDirectory(prefix="loop-internal-runtime-") as tmp:
            workspace = Path(tmp) / ".loop-engineer"
            workspace.mkdir(parents=True)
            result = self.run_cli(
                "--workspace",
                str(workspace),
                "plan-loop",
                "A small appointment reminder product",
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("compatibility-only", result.stderr)
            self.assertIn("/plan-loop", result.stderr)
            self.assertTrue((workspace / "plan" / "PLAN_BOOTSTRAP.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
