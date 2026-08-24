"""Regression tests for executable helpers shipped by the frontend-animation skill."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = ROOT / "skills" / "frontend-animation"


class FrontendAnimationScriptTests(unittest.TestCase):
    def run_script(
        self, relative_path: str, *args: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SKILL_ROOT / relative_path), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_every_skill_python_script_compiles(self) -> None:
        failures: list[str] = []
        for path in sorted((ROOT / "skills").rglob("*.py")):
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except (SyntaxError, UnicodeError) as exc:
                failures.append(f"{path.relative_to(ROOT)}: {exc}")

        self.assertEqual([], failures)

    def test_component_generator_emits_jsx_event_handler(self) -> None:
        result = self.run_script(
            "scripts/component_generator.py",
            "--type",
            "interactive",
            "--name",
            "Button",
            "--events",
            "onClick,onPointerOver",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('onClick={(e) => console.log("click", e)}', result.stdout)
        self.assertIn(
            'onPointerOver={(e) => console.log("pointerover", e)}', result.stdout
        )

    def test_motion_validator_is_safe_on_windows_console_encoding(self) -> None:
        child_env = os.environ.copy()
        child_env["PYTHONIOENCODING"] = "cp1252"
        result = self.run_script(
            "scripts/validate_motion_config.py",
            str(SKILL_ROOT / "examples" / "example-config.json"),
            env=child_env,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Configuration valid", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
