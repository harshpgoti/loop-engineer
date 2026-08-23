"""A product's vocabulary is only real if something checks it."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import glossary  # noqa: E402

CONTEXT = """# Product Context

## Repo Map

- backend/

## Language

**Denial**
A claim the payer adjudicated and refused to pay.
_Avoid_: rejection, decline

**Underpayment**
A claim paid at less than the contracted rate.
_Avoid_: shortfall

## Conventions

- Match the surrounding code.
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.ws, True)
        (self.ws / "plan").mkdir()
        (self.ws / "CONTEXT.md").write_text(CONTEXT, encoding="utf-8")

    def plan(self, name: str, body: str) -> None:
        (self.ws / "plan" / name).write_text(body, encoding="utf-8")


class Parsing(Sandbox):
    def test_terms_are_read_from_the_language_section_only(self) -> None:
        names = [t.name for t in glossary.terms(self.ws)]
        self.assertEqual(["Denial", "Underpayment"], names)

    def test_a_term_carries_its_definition_and_its_displaced_words(self) -> None:
        denial = glossary.terms(self.ws)[0]
        self.assertIn("refused to pay", denial.definition)
        self.assertEqual(["rejection", "decline"], denial.avoid)

    def test_a_workspace_with_no_context_file_is_not_an_error(self) -> None:
        (self.ws / "CONTEXT.md").unlink()
        self.assertEqual([], glossary.terms(self.ws))

    def test_a_term_with_no_definition_is_reported(self) -> None:
        (self.ws / "CONTEXT.md").write_text(
            "## Language\n\n**Denial**\n\n## Conventions\n", encoding="utf-8"
        )
        self.assertIn("named with no definition", glossary.terms(self.ws)[0].issues)

    def test_a_term_that_displaces_itself_is_reported(self) -> None:
        (self.ws / "CONTEXT.md").write_text(
            "## Language\n\n**Denial**\nA refusal to pay.\n_Avoid_: Denial\n", encoding="utf-8"
        )
        self.assertTrue(any("both" in i for i in glossary.terms(self.ws)[0].issues))


class DriftDetection(Sandbox):
    def test_a_displaced_word_in_the_plan_is_counted(self) -> None:
        self.plan("step_01.md", "The rejection queue holds every rejection.\n")
        found = {d.word: d.count for d in glossary.drift(self.ws)}
        self.assertEqual(1, found["rejection"])

    def test_it_matches_inflections_but_not_unrelated_words(self) -> None:
        self.plan("step_01.md", "declined claims\ndeclines\ndeclination of gravity\n")
        found = {d.word: d.count for d in glossary.drift(self.ws)}
        self.assertEqual(2, found["decline"])

    def test_it_names_the_canonical_term_to_use_instead(self) -> None:
        self.plan("step_01.md", "a shortfall\n")
        self.assertEqual("Underpayment", glossary.drift(self.ws)[0].canonical)

    def test_the_canonical_word_itself_is_never_a_hit(self) -> None:
        self.plan("step_01.md", "Denial and Denial and Denial.\n")
        self.assertEqual([], glossary.drift(self.ws))

    def test_context_md_is_excluded_so_the_avoid_list_is_not_its_own_finding(self) -> None:
        self.assertEqual([], glossary.drift(self.ws))

    def test_findings_are_ordered_by_how_entrenched_the_word_is(self) -> None:
        self.plan("a.md", "rejection\nrejection\nrejection\n")
        self.plan("b.md", "shortfall\n")
        self.assertEqual(["rejection", "shortfall"], [d.word for d in glossary.drift(self.ws)])

    def test_every_hit_is_counted_even_when_only_a_few_are_shown(self) -> None:
        self.plan("a.md", "rejection\n" * 20)
        entry = glossary.drift(self.ws, limit=3)[0]
        self.assertEqual(20, entry.count)
        self.assertEqual(3, entry.shown)

    def test_a_hit_carries_where_it_is(self) -> None:
        self.plan("step_01.md", "line one\nthe rejection lives here\n")
        path, number, text = glossary.drift(self.ws)[0].hits[0]
        self.assertEqual("plan/step_01.md", path)
        self.assertEqual(2, number)
        self.assertIn("rejection", text)


class Manifest(Sandbox):
    def test_a_clean_plan_says_nothing(self) -> None:
        self.assertEqual([], glossary.manifest_block(self.ws))

    def test_drift_is_surfaced_without_anyone_running_a_command(self) -> None:
        self.plan("step_01.md", "rejection\n")
        block = "\n".join(glossary.manifest_block(self.ws))
        self.assertIn("Language", block)
        self.assertIn("rejection", block)

    def test_a_bare_workspace_is_not_nagged(self) -> None:
        """A prompt that fires every session on an empty product is noise."""
        (self.ws / "CONTEXT.md").write_text("# Product Context\n", encoding="utf-8")
        self.assertEqual([], glossary.manifest_block(self.ws))

    def test_a_real_plan_with_no_glossary_is_prompted_once_it_has_prose(self) -> None:
        (self.ws / "CONTEXT.md").write_text("# Product Context\n", encoding="utf-8")
        for name in ("main_plan.md", "step_01.md", "step_02.md"):
            self.plan(name, "content\n")
        self.assertIn("no `## Language` section", "\n".join(glossary.manifest_block(self.ws)))


class Reporting(Sandbox):
    def test_it_reports_and_never_rewrites(self) -> None:
        self.plan("step_01.md", "rejection\n")
        before = (self.ws / "plan" / "step_01.md").read_text(encoding="utf-8")
        glossary.describe(self.ws)
        self.assertEqual(before, (self.ws / "plan" / "step_01.md").read_text(encoding="utf-8"))

    def test_an_empty_glossary_gets_a_worked_example_not_a_scolding(self) -> None:
        (self.ws / "CONTEXT.md").write_text("# Product Context\n", encoding="utf-8")
        text = glossary.describe(self.ws)
        self.assertIn("## Language", text)
        self.assertIn("_Avoid_", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
