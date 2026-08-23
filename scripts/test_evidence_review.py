"""Evidence decays on wall-clock time, not on file changes. Two separate mechanisms."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evidence_review as er  # noqa: E402

LOG = """# Evidence Log

### E-001: A regulation
- **Type:** regulatory
- **Claim:** CMS mandates the transaction.
- **Date checked:** 2026-01-10 - **Confidence:** high

### E-002: A market observation
- **Type:** verified_fact
- **Claim:** Competitor pricing sits here.
- **Date checked:** 2026-01-10 - **Confidence:** medium

### E-003: A guess
- **Type:** assumption
- **Claim:** Clinics probably want this.
- **Date checked:** 2026-01-10 - **Confidence:** low

### E-004: Already dismissed
- **Type:** rejected
- **Claim:** We looked and it was wrong.
- **Date checked:** 2026-01-10 - **Confidence:** high

### E-005: No date at all
- **Type:** verified_fact
- **Claim:** Recorded without a check date.
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Path(tempfile.mkdtemp(prefix="loop-evidence-"))
        (self.ws / "EVIDENCE_LOG.md").write_text(LOG, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.ws, ignore_errors=True)

    def entry(self, eid: str) -> dict:
        return next(e for e in er.parse(self.ws) if e["id"] == eid)


class Parsing(Sandbox):
    def test_every_entry_is_found(self) -> None:
        self.assertEqual(
            ["E-001", "E-002", "E-003", "E-004", "E-005"], [e["id"] for e in er.parse(self.ws)]
        )

    def test_type_and_confidence_are_read_from_one_line(self) -> None:
        """Real entries put `Date checked` and `Confidence` on the same line."""
        entry = self.entry("E-002")
        self.assertEqual("verified_fact", entry["type"])
        self.assertEqual("medium", entry["confidence"])
        self.assertEqual("2026-01-10", entry["checked"])

    def test_a_missing_file_is_not_an_error(self) -> None:
        (self.ws / "EVIDENCE_LOG.md").unlink()
        self.assertEqual([], er.parse(self.ws))


class Windows(Sandbox):
    def test_stronger_evidence_lasts_longer(self) -> None:
        self.assertGreater(er.window_days(self.entry("E-001")), er.window_days(self.entry("E-002")))
        self.assertGreater(er.window_days(self.entry("E-002")), er.window_days(self.entry("E-003")))

    def test_confidence_shortens_the_window(self) -> None:
        high = {"type": "verified_fact", "confidence": "high"}
        medium = {"type": "verified_fact", "confidence": "medium"}
        self.assertEqual(180, er.window_days(high))
        self.assertEqual(90, er.window_days(medium))

    def test_no_window_is_shorter_than_two_weeks(self) -> None:
        self.assertGreaterEqual(er.window_days({"type": "assumption", "confidence": "low"}), 14)


class Expiry(Sandbox):
    def test_nothing_is_due_the_day_it_was_checked(self) -> None:
        self.assertEqual([], er.review_due(self.ws, today="2026-01-10"))

    def test_a_weak_claim_expires_before_a_strong_one(self) -> None:
        """assumption/low = 30d * 0.25 -> 14d floor; regulatory/high = 365d."""
        due = {e["id"] for e in er.review_due(self.ws, today="2026-02-01")}
        self.assertIn("E-003", due)
        self.assertNotIn("E-001", due)
        self.assertNotIn("E-002", due)

    def test_everything_perishable_expires_eventually(self) -> None:
        due = {e["id"] for e in er.review_due(self.ws, today="2027-06-01")}
        self.assertEqual({"E-001", "E-002", "E-003"}, due)

    def test_a_rejected_claim_is_never_re_checked(self) -> None:
        self.assertNotIn("E-004", {e["id"] for e in er.review_due(self.ws, today="2030-01-01")})

    def test_an_undated_entry_is_reported_not_expired(self) -> None:
        """No honest way to decay it, so it is surfaced rather than guessed at."""
        self.assertNotIn("E-005", {e["id"] for e in er.review_due(self.ws, today="2030-01-01")})
        self.assertIn("E-005", {e["id"] for e in er.undated(self.ws)})

    def test_an_explicit_review_after_overrides_the_computed_window(self) -> None:
        (self.ws / "EVIDENCE_LOG.md").write_text(
            LOG.replace(
                "### E-001: A regulation\n- **Type:** regulatory",
                "### E-001: A regulation\n- **Review after:** 2026-02-01\n- **Type:** regulatory",
            ),
            encoding="utf-8",
        )
        self.assertIn("E-001", {e["id"] for e in er.review_due(self.ws, today="2026-03-01")})

    def test_re_checking_resets_the_clock(self) -> None:
        self.assertIn("E-002", {e["id"] for e in er.review_due(self.ws, today="2026-06-01")})
        (self.ws / "EVIDENCE_LOG.md").write_text(
            LOG.replace(
                "- **Claim:** Competitor pricing sits here.\n- **Date checked:** 2026-01-10",
                "- **Claim:** Competitor pricing sits here.\n- **Date checked:** 2026-05-20",
            ),
            encoding="utf-8",
        )
        self.assertNotIn("E-002", {e["id"] for e in er.review_due(self.ws, today="2026-06-01")})


class SeparateFromContentFreshness(Sandbox):
    def test_editing_the_file_does_not_reset_decay(self) -> None:
        """The mechanical and epistemic axes must not be confused for each other.

        Content hashing answers "did the file change"; nothing there answers "is this
        claim still true". Rewording a claim is not re-checking it.
        """
        before = {e["id"] for e in er.review_due(self.ws, today="2026-06-01")}
        text = (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8")
        (self.ws / "EVIDENCE_LOG.md").write_text(text.replace("sits here", "sits right here"), encoding="utf-8")
        self.assertEqual(before, {e["id"] for e in er.review_due(self.ws, today="2026-06-01")})

    def test_expiry_never_deletes_anything(self) -> None:
        before = (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8")
        er.review_due(self.ws, today="2030-01-01")
        er.describe(self.ws, today="2030-01-01")
        self.assertEqual(before, (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8"))

    def test_the_report_says_uncertain_not_wrong(self) -> None:
        text = er.describe(self.ws, today="2027-06-01")
        self.assertIn("uncertain, not disproved", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
