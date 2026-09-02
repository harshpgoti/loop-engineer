from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from import_agent_development_skills import LEGACY_BRAND, SKILLS, import_skills


class ImportAgentDevelopmentSkillsTests(unittest.TestCase):
    def test_imports_complete_trees_and_adds_local_contract(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as destination_tmp:
            source = Path(source_tmp)
            for name in SKILLS:
                folder = source / name
                folder.mkdir()
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n# {LEGACY_BRAND} on Claude Code\n",
                    encoding="utf-8",
                )
                (folder / "reference.md").write_text(
                    f"{LEGACY_BRAND} and CLAUDE.md", encoding="utf-8"
                )
            written = import_skills(source, Path(destination_tmp))
            self.assertEqual(len(SKILLS) * 2, len(written))
            for name in SKILLS:
                text = (Path(destination_tmp) / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("Inherits `docs/SKILL_CONTRACT.md`", text)
                self.assertNotIn(LEGACY_BRAND, text)
                self.assertTrue((Path(destination_tmp) / name / "reference.md").is_file())

    def test_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as source_tmp, tempfile.TemporaryDirectory() as destination_tmp:
            source = Path(source_tmp)
            for name in SKILLS:
                folder = source / name
                folder.mkdir()
                (folder / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: test\n---\n", encoding="utf-8"
                )
            existing = Path(destination_tmp) / SKILLS[0]
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                import_skills(source, Path(destination_tmp))


if __name__ == "__main__":
    unittest.main()
