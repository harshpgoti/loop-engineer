"""Tests for migrate_import.run_import(), including the combined
`/setup-loop-engine --source` flow (freshly-seeded placeholders should be
superseded by imported content; genuinely pre-existing content should not be,
unless --overwrite is passed).

Run: python scripts/test_migrate_import.py
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from memory_paths import ensure_memory_layout
from migrate_import import run_import


class TestMigrateImport(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-migrate-import-test-"))
        self.source = self.tmp / "source"
        self.workspace = self.tmp / "workspace"
        self.source.mkdir()
        self.workspace.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_source_memory(self, content: str = "# imported memory from other tool") -> None:
        (self.source / "MEMORY.md").write_text(content, encoding="utf-8")
        (self.source / "USER.md").write_text("# imported user profile", encoding="utf-8")

    def test_missing_source_raises(self) -> None:
        with self.assertRaises(SystemExit):
            run_import(self.workspace, str(self.tmp / "does-not-exist"))

    def test_combined_setup_flow_supersedes_fresh_placeholder(self) -> None:
        """Simulates /setup-loop-engine --source: caller's own ensure_memory_layout()
        ran first (fresh workspace), then run_import() gets that same actions dict."""
        self._write_source_memory()
        memory_actions = ensure_memory_layout(self.workspace)
        self.assertTrue(memory_actions["MEMORY.md"].startswith("created"))

        run_import(self.workspace, str(self.source), memory_actions=memory_actions)

        self.assertEqual(
            (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8"),
            "# imported memory from other tool",
        )
        self.assertEqual(
            (self.workspace / "memories" / "USER.md").read_text(encoding="utf-8"),
            "# imported user profile",
        )

    def test_standalone_import_respects_existing_without_overwrite(self) -> None:
        """Standalone /migrate-import against an already-set-up workspace (separate
        prior process) must NOT clobber real content without --overwrite."""
        ensure_memory_layout(self.workspace)  # simulates an earlier, separate setup run
        original = (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8")

        self._write_source_memory("# a different memory, should not clobber")
        run_import(self.workspace, str(self.source))  # memory_actions=None -> recomputed as "exists"

        self.assertEqual(
            (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8"), original
        )

    def test_standalone_import_overwrite_flag_actually_overwrites(self) -> None:
        ensure_memory_layout(self.workspace)
        self._write_source_memory("# overwritten content")
        run_import(self.workspace, str(self.source), overwrite=True)

        self.assertEqual(
            (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8"),
            "# overwritten content",
        )

    def test_dry_run_does_not_write(self) -> None:
        memory_actions = ensure_memory_layout(self.workspace)
        self._write_source_memory()
        run_import(self.workspace, str(self.source), memory_actions=memory_actions, dry_run=True)

        # ensure_memory_layout's own placeholder should remain untouched
        content = (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8")
        self.assertNotEqual(content, "# imported memory from other tool")

    def test_skills_are_imported(self) -> None:
        skills_dir = self.source / "skills"
        skills_dir.mkdir()
        (skills_dir / "cool-skill.md").write_text("---\nname: cool-skill\n---\ndo a thing", encoding="utf-8")
        memory_actions = ensure_memory_layout(self.workspace)

        run_import(self.workspace, str(self.source), memory_actions=memory_actions)

        imported = self.workspace / "skills" / "imported" / "cool-skill.md"
        self.assertTrue(imported.exists())
        self.assertIn("cool-skill", imported.read_text(encoding="utf-8"))

    def test_source_without_soul_keeps_default_soul(self) -> None:
        """A source tool that doesn't have SOUL.md must not blank out the default."""
        self._write_source_memory()
        memory_actions = ensure_memory_layout(self.workspace)

        run_import(self.workspace, str(self.source), memory_actions=memory_actions)

        soul = (self.workspace / "memories" / "SOUL.md").read_text(encoding="utf-8")
        self.assertTrue(len(soul) > 0)


if __name__ == "__main__":
    unittest.main()
