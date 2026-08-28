"""Contract tests for declarative coding-harness adapters."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import harness_adapters


class HarnessAdapterRegistry(unittest.TestCase):
    def test_every_supported_harness_has_behavior_metadata(self) -> None:
        expected = {"universal", "claude", "codex", "cursor", "opencode", "gemini", "grok", "pi", "factory", "kiro", "slate", "hermes"}
        self.assertEqual(expected, set(harness_adapters.ADAPTERS))
        for adapter in harness_adapters.ADAPTERS.values():
            self.assertTrue(adapter["invocation"])
            self.assertTrue(adapter["trust"])
            self.assertTrue(adapter["hooks"])

    def test_behavior_specific_paths_are_derived_from_one_registry(self) -> None:
        self.assertEqual({"opencode", "pi"}, set(harness_adapters.path_table("command_paths")))
        self.assertEqual({"opencode"}, set(harness_adapters.path_table("permission_paths")))

    def test_codex_and_pi_record_different_invocation_contracts(self) -> None:
        self.assertIn("$skill-name", harness_adapters.ADAPTERS["codex"]["invocation"])
        self.assertIn("/skill:name", harness_adapters.ADAPTERS["pi"]["invocation"])

    def test_invalid_adapter_fails_before_installation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "broken.json").write_text(json.dumps({"name": "broken"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing"):
                harness_adapters.load_adapters(Path(tmp))


if __name__ == "__main__":
    unittest.main(verbosity=2)
