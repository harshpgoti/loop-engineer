"""Fog is meant to clear. These tests are about what happens when it does not."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doubts  # noqa: E402
import fog  # noqa: E402

PLAN = """# Main Plan

## Product

A thing.

## Not yet specified

- How tenants share a model cache once there is more than one tenant.
- Whether the appeal templates need a per-payer variant.

## Out of scope

- A native mobile client.

## Step Plan Index

- step_01
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.ws, True)
        (self.ws / "plan").mkdir()
        (self.ws / "plan" / "main_plan.md").write_text(PLAN, encoding="utf-8")

    @property
    def today(self) -> date:
        return date(2026, 8, 22)

    def later(self, days: int) -> date:
        return self.today + timedelta(days=days)


class Parsing(Sandbox):
    def test_fog_and_scope_are_read_from_their_own_sections(self) -> None:
        self.assertEqual(2, len(fog.fog(self.ws)))
        self.assertEqual(1, len(fog.out_of_scope(self.ws)))

    def test_bullets_outside_those_sections_are_ignored(self) -> None:
        self.assertNotIn("step_01", [p.text for p in fog.parse(self.ws)])

    def test_a_plan_with_neither_section_is_not_an_error(self) -> None:
        (self.ws / "plan" / "main_plan.md").write_text("# Main Plan\n", encoding="utf-8")
        self.assertEqual([], fog.parse(self.ws))

    def test_a_numbered_heading_still_matches(self) -> None:
        """Real plans number their sections."""
        (self.ws / "plan" / "main_plan.md").write_text(
            "# Main Plan\n\n## 11. Not yet specified\n\n- Something.\n", encoding="utf-8"
        )
        self.assertEqual(1, len(fog.fog(self.ws)))


class Ageing(Sandbox):
    def test_the_clock_starts_when_the_patch_first_appears(self) -> None:
        fog.record(self.ws, today=self.today)
        self.assertEqual(self.today.isoformat(), fog.fog(self.ws)[0].first_seen)

    def test_looking_again_does_not_reset_it(self) -> None:
        """A patch must not be only as old as the last person who looked at it."""
        fog.record(self.ws, today=self.today)
        fog.record(self.ws, today=self.later(40))
        self.assertEqual(40, fog.fog(self.ws)[0].age_days(self.later(40)))

    def test_fog_that_has_not_cleared_is_reported(self) -> None:
        fog.record(self.ws, today=self.today)
        self.assertEqual([], fog.stale(self.ws, today=self.later(10)))
        self.assertEqual(2, len(fog.stale(self.ws, today=self.later(fog.STALE_DAYS))))

    def test_out_of_scope_work_never_goes_stale(self) -> None:
        """It is not meant to clear - it is a scope call, not an unknown."""
        fog.record(self.ws, today=self.today)
        stale = fog.stale(self.ws, today=self.later(400))
        self.assertNotIn("A native mobile client.", [p.text for p in stale])

    def test_rewriting_a_patch_restarts_its_clock(self) -> None:
        fog.record(self.ws, today=self.today)
        path = self.ws / "plan" / "main_plan.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace("per-payer variant", "per-payer and per-state variant"),
            encoding="utf-8",
        )
        fog.record(self.ws, today=self.later(40))
        ages = sorted(p.age_days(self.later(40)) for p in fog.fog(self.ws))
        self.assertEqual([0, 40], ages)

    def test_cleared_fog_leaves_no_residue(self) -> None:
        fog.record(self.ws, today=self.today)
        path = self.ws / "plan" / "main_plan.md"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "- How tenants share a model cache once there is more than one tenant.\n", ""
            ),
            encoding="utf-8",
        )
        fog.record(self.ws, today=self.later(1))
        ledger = (self.ws / ".loop" / "fog.json").read_text(encoding="utf-8")
        self.assertNotIn("model cache", ledger)


class Promotion(Sandbox):
    def test_a_patch_becomes_a_stated_question(self) -> None:
        doubt_id = fog.promote(self.ws, 1)
        self.assertIsNotNone(doubt_id)
        recorded = doubts.parse(self.ws)
        self.assertEqual(1, len(recorded))
        self.assertIn("model cache", recorded[0].question)

    def test_the_question_keeps_the_author_s_own_wording(self) -> None:
        """A machine paraphrase loses whatever nuance made it worth writing down."""
        original = fog.fog(self.ws)[0].text
        fog.promote(self.ws, 1)
        self.assertEqual(original, doubts.parse(self.ws)[0].question)

    def test_promoting_clears_it_from_the_plan(self) -> None:
        fog.promote(self.ws, 1)
        remaining = [p.text for p in fog.fog(self.ws)]
        self.assertEqual(1, len(remaining))
        self.assertNotIn("model cache", remaining[0])

    def test_the_rest_of_the_plan_survives(self) -> None:
        fog.promote(self.ws, 1)
        text = (self.ws / "plan" / "main_plan.md").read_text(encoding="utf-8")
        self.assertIn("## Out of scope", text)
        self.assertIn("A native mobile client.", text)
        self.assertIn("## Step Plan Index", text)

    def test_an_index_that_names_nothing_is_reported_not_guessed(self) -> None:
        self.assertIsNone(fog.promote(self.ws, 99))
        self.assertEqual(2, len(fog.fog(self.ws)))


class Manifest(Sandbox):
    def test_fresh_fog_is_counted_but_not_chased(self) -> None:
        block = "\n".join(fog.manifest_block(self.ws, today=self.today))
        self.assertIn("2 patch(es)", block)
        self.assertNotIn("unchanged for", block)

    def test_fog_that_will_not_clear_is_chased(self) -> None:
        fog.record(self.ws, today=self.today)
        block = "\n".join(fog.manifest_block(self.ws, today=self.later(fog.STALE_DAYS)))
        self.assertIn("unchanged", block)
        self.assertIn("loop fog promote", block)

    def test_a_plan_with_no_fog_says_nothing(self) -> None:
        (self.ws / "plan" / "main_plan.md").write_text("# Main Plan\n", encoding="utf-8")
        self.assertEqual([], fog.manifest_block(self.ws, today=self.today))

    def test_out_of_scope_alone_says_nothing(self) -> None:
        (self.ws / "plan" / "main_plan.md").write_text(
            "# Main Plan\n\n## Out of scope\n\n- A native mobile client.\n", encoding="utf-8"
        )
        self.assertEqual([], fog.manifest_block(self.ws, today=self.today))


if __name__ == "__main__":
    unittest.main(verbosity=2)
