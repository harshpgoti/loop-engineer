"""Tests for import_scanner.py — content classification + routing + idempotence.

Run: python scripts/test_import_scanner.py
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import import_scanner as sc


class ScannerSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-scan-test-"))
        self.source = self.tmp / "source"
        self.workspace = self.tmp / "workspace"
        self.source.mkdir()
        self.workspace.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestClassify(unittest.TestCase):
    def _cat(self, name: str, text: str) -> str:
        return sc.classify(Path(name), text)[0]

    def test_user_by_filename(self) -> None:
        self.assertEqual(self._cat("my-profile.md", "Name: Harsh. Timezone: IST."), "user")

    def test_user_by_content(self) -> None:
        self.assertEqual(
            self._cat("stuff.md", "My name is Harsh. I prefer short answers. Communication style: direct."),
            "user",
        )

    def test_soul_by_cursorrules_style_content(self) -> None:
        self.assertEqual(
            self._cat("cursorrules.txt", "You are a senior engineer. Always respond tersely. Never invent APIs."),
            "soul",
        )

    def test_memory_by_content(self) -> None:
        self.assertEqual(
            self._cat("random.md", "Today we finished the auth flow. Next step: payments. Follow up on emails."),
            "memory",
        )

    def test_skill_by_frontmatter(self) -> None:
        cat, reason = sc.classify(Path("deploy.md"), "---\nname: deploy\ndescription: Deploy steps\n---\nrun x")
        self.assertEqual(cat, "skill")
        self.assertIn("frontmatter", reason)

    def test_skill_by_howto_shape(self) -> None:
        self.assertEqual(
            self._cat("db-backup-howto.md", "How to back up the DB.\nStep 1: dump.\nWhen to use: nightly."),
            "skill",
        )

    def test_plan_by_content(self) -> None:
        self.assertEqual(
            self._cat("vision.md", "Roadmap: MVP by June. Milestone 1: onboarding. Acceptance criteria below."),
            "plan",
        )

    def test_unknown_when_no_signals(self) -> None:
        self.assertEqual(self._cat("misc.md", "lorem ipsum dolor sit amet"), "unknown")


class TestSecretsAndBinary(ScannerSandbox):
    def test_env_file_never_copied(self) -> None:
        (self.source / ".env").write_text("OPENAI_API_KEY=sk-abcdefghijklmnop123456", encoding="utf-8")
        results = sc.run_scan_import(self.workspace, self.source)
        self.assertTrue(any("NOT copied" in r and ".env" in r for r in results))
        self.assertFalse(any(self.workspace.rglob(".env")))

    def test_secret_content_in_plain_file_blocked(self) -> None:
        (self.source / "notes.md").write_text("progress so far ok. api_key = sk-abcdefghijklmnop123456", encoding="utf-8")
        results = sc.run_scan_import(self.workspace, self.source)
        self.assertTrue(any("NOT copied" in r for r in results))

    def test_binary_skipped(self) -> None:
        (self.source / "logo.png").write_bytes(b"\x89PNG\x00\x00binary")
        results = sc.run_scan_import(self.workspace, self.source)
        self.assertTrue(any("binary" in r for r in results))


class TestRouting(ScannerSandbox):
    def test_memory_appended_with_marker(self) -> None:
        (self.source / "journal.md").write_text("Today we shipped login. Next step: signup.", encoding="utf-8")
        sc.run_scan_import(self.workspace, self.source)
        target = self.workspace / "memories" / "MEMORY.md"
        text = target.read_text(encoding="utf-8")
        self.assertIn("Imported from `journal.md`", text)
        self.assertIn("shipped login", text)

    def test_rerun_is_idempotent(self) -> None:
        (self.source / "journal.md").write_text("Today we shipped login. Next step: signup.", encoding="utf-8")
        sc.run_scan_import(self.workspace, self.source)
        results = sc.run_scan_import(self.workspace, self.source)
        self.assertTrue(any("already imported" in r for r in results))
        text = (self.workspace / "memories" / "MEMORY.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("Imported from `journal.md`"), 1)

    def test_skill_gets_frontmatter(self) -> None:
        (self.source / "restart-server-howto.md").write_text(
            "How to restart the server.\nStep 1: ssh in.\nStep 2: systemctl restart app.", encoding="utf-8"
        )
        sc.run_scan_import(self.workspace, self.source)
        dest = self.workspace / "skills" / "imported" / "restart-server-howto.md"
        text = dest.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname:"))
        self.assertIn("description:", text)

    def test_plan_staged_for_plan_command(self) -> None:
        (self.source / "roadmap.md").write_text("Roadmap: MVP milestone 1, sprint plan, acceptance criteria.", encoding="utf-8")
        results = sc.run_scan_import(self.workspace, self.source)
        self.assertTrue((self.workspace / "plan" / "imported" / "roadmap.md").exists())
        self.assertTrue(any("/plan-loop" in r for r in results))

    def test_unknown_staged_for_review(self) -> None:
        (self.source / "misc.md").write_text("lorem ipsum dolor sit amet", encoding="utf-8")
        sc.run_scan_import(self.workspace, self.source)
        self.assertTrue((self.workspace / ".loop" / "import-review" / "misc.md").exists())

    def test_dry_run_writes_nothing(self) -> None:
        (self.source / "journal.md").write_text("Today we shipped login. Next step: deploy.", encoding="utf-8")
        (self.source / "roadmap.md").write_text("Roadmap with milestone and mvp and sprint.", encoding="utf-8")
        results = sc.run_scan_import(self.workspace, self.source, dry_run=True)
        self.assertTrue(any(r.startswith("would append") for r in results))
        self.assertFalse((self.workspace / "memories").exists())
        self.assertFalse((self.workspace / "plan").exists())

    def test_exclude_known_skips_exact_name_files(self) -> None:
        (self.source / "MEMORY.md").write_text("What we did: everything. Progress: fine.", encoding="utf-8")
        (self.source / "journal.md").write_text("Today we shipped login. Next step: deploy.", encoding="utf-8")
        results = sc.run_scan_import(self.workspace, self.source, exclude_known=True)
        self.assertFalse(any("MEMORY.md ->" in r for r in results))
        self.assertTrue(any("journal.md" in r for r in results))

    def test_nested_folders_scanned(self) -> None:
        nested = self.source / "old-tool" / "data"
        nested.mkdir(parents=True)
        (nested / "user-preferences.md").write_text("I prefer dark mode. Timezone: IST.", encoding="utf-8")
        sc.run_scan_import(self.workspace, self.source)
        text = (self.workspace / "memories" / "USER.md").read_text(encoding="utf-8")
        self.assertIn("old-tool/data/user-preferences.md", text)


if __name__ == "__main__":
    unittest.main()
