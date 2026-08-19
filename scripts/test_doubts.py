"""One parser for DOUBTS.md, and it must survive what real files actually contain."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doubts  # noqa: E402

CLEAN = """# Doubts

## Open Doubts

### DQ-001: Product initialization
- **Status:** open
- **Question:** What product should this build?
- **Why it matters:** Everything depends on it.
- **Default if unavailable:** Do not invent a product.

### DQ-002: Pricing model
- **Status:** open (commercial - does not block the build)
- **Question:** Flat fee or per-seat?
- **Default if unavailable:** Flat fee.

## Resolved Doubts

### DQ-003: Datastore
- **Status:** resolved
- **Resolution (2026-08-01):** Postgres.
"""

# Every deviation below was taken from a real workspace.
MESSY = """# Doubts

## Open Doubts

### DQ-015: Lane order - **RESOLVED 2026-08-06**
- **Resolution:** Both lanes ship sequentially.

### DQ-010: MCP spec version
- **Status:** open (Step-02 build start)
- **Question:** Which spec version?
- **Resolved 2026-07-12:** D-015 pins mcp==1.27.2.

## Resolved Doubts

### DQ-012: Model availability
- **Status:** open (verify at build)
- **Question:** Is the model available in this region?
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Path(tempfile.mkdtemp(prefix="loop-doubts-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.ws, ignore_errors=True)

    def seed(self, body: str) -> None:
        (self.ws / "DOUBTS.md").write_text(body, encoding="utf-8")


class Parsing(Sandbox):
    def test_counts_the_whole_file(self) -> None:
        self.seed(CLEAN)
        counts = doubts.counts(self.ws)
        self.assertEqual(3, counts["total"])
        self.assertEqual(2, counts["open"])
        self.assertEqual(1, counts["resolved"])

    def test_status_qualifier_does_not_break_the_status(self) -> None:
        """`open (commercial - does not block the build)` is still `open`."""
        self.seed(CLEAN)
        pricing = next(d for d in doubts.parse(self.ws) if d.id == "DQ-002")
        self.assertEqual(doubts.OPEN, pricing.status)

    def test_non_blocking_doubt_does_not_block(self) -> None:
        """The bug this fixes: one commercial question pinned the whole phase router."""
        self.seed(CLEAN)
        blocking = doubts.blocking_doubts(self.ws)
        self.assertEqual(["DQ-001"], [d.id for d in blocking])

    def test_resolved_file_has_no_blocking_doubts(self) -> None:
        self.seed(CLEAN.replace("- **Status:** open\n", "- **Status:** resolved\n"))
        self.assertFalse(doubts.has_blocking(self.ws))

    def test_the_word_open_in_a_heading_is_not_a_doubt(self) -> None:
        """`prod_gap` used to raise a launch blocker off the `## Open Doubts` heading."""
        self.seed("# Doubts\n\n## Open Doubts\n\nNone yet.\n")
        self.assertEqual(0, doubts.counts(self.ws)["open"])
        self.assertFalse(doubts.has_blocking(self.ws))

    def test_missing_file_is_not_an_error(self) -> None:
        self.assertEqual([], doubts.parse(self.ws))
        self.assertFalse(doubts.has_blocking(self.ws))


class RealWorldMess(Sandbox):
    def test_heading_resolved_without_a_status_field(self) -> None:
        self.seed(MESSY)
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-015")
        self.assertEqual(doubts.RESOLVED, entry.status)
        self.assertTrue(entry.issues)

    def test_status_field_wins_over_a_resolution_body(self) -> None:
        """Ambiguity is reported, never silently guessed."""
        self.seed(MESSY)
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-010")
        self.assertEqual(doubts.OPEN, entry.status)
        self.assertTrue(any("resolution" in issue for issue in entry.issues))

    def test_open_entry_filed_under_resolved_is_flagged(self) -> None:
        self.seed(MESSY)
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-012")
        self.assertEqual(doubts.OPEN, entry.status)
        self.assertTrue(any("Resolved" in issue for issue in entry.issues))


class Writing(Sandbox):
    def test_resolve_rewrites_status_and_records_the_answer(self) -> None:
        self.seed(CLEAN)
        self.assertTrue(doubts.resolve(self.ws, "DQ-001", "Denial recovery engine", decision_ref="D-014"))
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-001")
        self.assertEqual(doubts.RESOLVED, entry.status)
        text = (self.ws / "DOUBTS.md").read_text(encoding="utf-8")
        self.assertIn("Denial recovery engine", text)
        self.assertIn("D-014", text)

    def test_resolve_reduces_the_open_count(self) -> None:
        self.seed(CLEAN)
        before = doubts.counts(self.ws)["open"]
        doubts.resolve(self.ws, "DQ-001", "answered")
        self.assertEqual(before - 1, doubts.counts(self.ws)["open"])

    def test_defer_is_recorded_with_a_reason(self) -> None:
        self.seed(CLEAN)
        doubts.defer(self.ws, "DQ-002", "decide after the first pilot")
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-002")
        self.assertEqual(doubts.DEFERRED, entry.status)
        self.assertIn("first pilot", (self.ws / "DOUBTS.md").read_text(encoding="utf-8"))

    def test_unknown_id_is_reported_not_guessed(self) -> None:
        self.seed(CLEAN)
        self.assertFalse(doubts.resolve(self.ws, "DQ-999", "x"))

    def test_add_is_idempotent_on_the_question(self) -> None:
        self.seed(CLEAN)
        first = doubts.add(self.ws, title="Region", question="Which region?", default="us-east-1")
        again = doubts.add(self.ws, title="Region", question="Which region?", default="us-east-1")
        self.assertIsNotNone(first)
        self.assertIsNone(again, "the same question must not stack up every session")

    def test_added_doubt_round_trips(self) -> None:
        self.seed(CLEAN)
        new_id = doubts.add(self.ws, title="Region", question="Which region?", blocking=False)
        entry = next(d for d in doubts.parse(self.ws) if d.id == new_id)
        self.assertEqual(doubts.OPEN, entry.status)
        self.assertFalse(entry.blocking)


class Supersession(Sandbox):
    """A decision can retire a question instead of answering it."""

    DECISION = (
        "# Decision Log\n\n## D-014: Pricing is flat fee only\n"
        "- **Date:** 2026-08-10\n"
        "- **Supersedes:** DQ-002\n"
        "- **Decision:** No percentage pricing, in any market.\n"
    )

    def test_local_decision_retires_a_doubt(self) -> None:
        self.seed(CLEAN)
        self.assertIn("DQ-002", [d.id for d in doubts.open_doubts(self.ws)])
        (self.ws / "DECISIONS.md").write_text(self.DECISION, encoding="utf-8")

        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-002")
        self.assertEqual(doubts.RESOLVED, entry.status)
        self.assertIn("D-014", entry.superseded_by)
        self.assertFalse(entry.blocking)

    def test_superseded_doubt_is_never_asked(self) -> None:
        self.seed(CLEAN)
        (self.ws / "DECISIONS.md").write_text(
            self.DECISION.replace("DQ-002", "DQ-001"), encoding="utf-8"
        )
        self.assertEqual([], [d.id for d in doubts.blocking_doubts(self.ws)])
        self.assertFalse(doubts.has_blocking(self.ws))

    def test_withdrawing_the_decision_reopens_the_doubt(self) -> None:
        """Derived, not written - so it is reversible."""
        self.seed(CLEAN)
        decisions = self.ws / "DECISIONS.md"
        decisions.write_text(self.DECISION, encoding="utf-8")
        self.assertEqual(doubts.RESOLVED, next(d for d in doubts.parse(self.ws) if d.id == "DQ-002").status)

        decisions.write_text(self.DECISION.replace("- **Supersedes:** DQ-002\n", ""), encoding="utf-8")
        self.assertEqual(doubts.OPEN, next(d for d in doubts.parse(self.ws) if d.id == "DQ-002").status)

    def test_ids_are_found_inside_prose(self) -> None:
        """Real entries write a sentence, not a bare list."""
        self.seed(CLEAN)
        (self.ws / "DECISIONS.md").write_text(
            "# Decision Log\n\n## D-M-003: Flat fee only\n"
            "- **Supersedes:** the founder plan's 20-30% GTM; sub-product `DQ-001` and "
            "`DQ-002` are **superseded, not answered**.\n",
            encoding="utf-8",
        )
        retired = doubts.supersessions(self.ws)
        self.assertEqual({"DQ-001", "DQ-002"}, set(retired))

    def test_a_supersedes_line_needs_a_decision_heading(self) -> None:
        self.seed(CLEAN)
        (self.ws / "DECISIONS.md").write_text("# Decisions\n\n- **Supersedes:** DQ-001\n", encoding="utf-8")
        self.assertEqual({}, doubts.supersessions(self.ws))

    def test_an_already_resolved_doubt_is_left_alone(self) -> None:
        self.seed(CLEAN)
        (self.ws / "DECISIONS.md").write_text(
            self.DECISION.replace("DQ-002", "DQ-003"), encoding="utf-8"
        )
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-003")
        self.assertEqual("", entry.superseded_by, "its real resolution must not be overwritten")


class SupersessionAcrossWorkspaces(unittest.TestCase):
    """The headline case: the master plan kills a question inside a sub-product."""

    def setUp(self) -> None:
        import json

        self.tmp = Path(tempfile.mkdtemp(prefix="loop-supersede-"))
        self.main = self.tmp / "platform" / ".loop-engineer"
        self.sub = self.tmp / "platform" / "engine" / ".loop-engineer"
        for ws in (self.main, self.sub):
            (ws / ".loop").mkdir(parents=True, exist_ok=True)
            (ws / "memories").mkdir(parents=True, exist_ok=True)
            (ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")

        (self.sub / "DOUBTS.md").write_text(
            "# Doubts\n\n### DQ-007: Contingency fee percentage\n"
            "- **Status:** open\n"
            "- **Question:** 20%, 25%, or 30% of recovered revenue?\n"
            "- **Default if unavailable:** 25%.\n",
            encoding="utf-8",
        )
        (self.sub / ".loop" / "workspace.json").write_text(
            json.dumps({"role": "sub", "parent": ".."}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_parent_decision_retires_a_sub_product_doubt(self) -> None:
        self.assertTrue(doubts.has_blocking(self.sub))

        (self.main / "DECISIONS.md").write_text(
            "# Decision Log\n\n## D-M-003: Pricing is flat fee only\n"
            "- **Supersedes:** sub-product `DQ-007` is superseded, not answered.\n"
            "- **Decision:** No percentage of recovered revenue, in any market.\n",
            encoding="utf-8",
        )

        entry = next(d for d in doubts.parse(self.sub) if d.id == "DQ-007")
        self.assertEqual(doubts.RESOLVED, entry.status)
        self.assertIn("D-M-003", entry.superseded_by)
        self.assertIn("parent product", entry.superseded_by)
        self.assertFalse(doubts.has_blocking(self.sub), "a retired question must not block the build")

    def test_a_sub_product_cannot_retire_its_parents_doubts(self) -> None:
        """One direction only - a child must never close a question upstream."""
        (self.main / "DOUBTS.md").write_text(
            "# Doubts\n\n### DQ-M-001: Launch markets\n- **Status:** open\n"
            "- **Question:** US, Ontario, or both?\n",
            encoding="utf-8",
        )
        (self.sub / "DECISIONS.md").write_text(
            "# Decision Log\n\n## D-001: Ontario only\n- **Supersedes:** DQ-M-001\n",
            encoding="utf-8",
        )
        entry = next(d for d in doubts.parse(self.main) if d.id == "DQ-M-001")
        self.assertEqual(doubts.OPEN, entry.status)
        self.assertEqual("", entry.superseded_by)


class Suggestions(Sandbox):
    def test_default_if_unavailable_is_the_recommendation(self) -> None:
        self.seed(CLEAN)
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-001")
        recommended, source = entry.suggestion()
        self.assertEqual("Do not invent a product.", recommended)
        self.assertIn("Default if unavailable", source)

    def test_question_shape_is_complete(self) -> None:
        self.seed(CLEAN)
        entry = next(d for d in doubts.parse(self.ws) if d.id == "DQ-001")
        q = doubts.question(entry)
        self.assertEqual("DQ-001", q["id"])
        self.assertTrue(q["question"])
        self.assertTrue(q["recommended"])
        self.assertTrue(q["options"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
