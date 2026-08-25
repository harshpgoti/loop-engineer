"""Blocking doubts stop both chains and get asked, rather than being built on top of.

The manifest is the file every command reads first, and it never mentioned doubts - so a
workspace could carry open blocking questions through planning and into a build without
anyone being asked. The build router had no doubt check at all.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_phase  # noqa: E402
import plan_phase  # noqa: E402
import session_lifecycle as sl  # noqa: E402

TWO_BLOCKING = """# Doubts

## DQ-001: Which auth provider?
- **Blocking:** yes
- **Default if unavailable:** Cognito

## DQ-002: Retention window?
- **Blocking:** yes
- **Default if unavailable:** 90 days
"""

ANSWERED_AND_DEFERRED = """# Doubts

## DQ-001: Which auth provider?
- **Blocking:** yes
- **Status:** resolved
- **Answer:** Cognito

## DQ-002: Retention window?
- **Blocking:** yes
- **Status:** deferred
- **Reason:** waiting on legal
"""

CHAINED = """# Doubts

## DQ-003: Datastore?
- **Blocking:** yes
- **Default if unavailable:** Postgres

## DQ-004: Sharding?
- **Blocking:** yes
- **Depends on:** DQ-003
"""


class Workspace(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.product = self.root / "P"
        self.ws = self.product / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)
        (self.ws / "memories").mkdir()
        (self.ws / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
        (self.ws / "plan" / "main_plan.md").write_text("# Product\n\na real plan\n", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(
            "tasks:\n  - id: T-1\n    title: build it\n    status: todo\n", encoding="utf-8")
        (self.product / "src").mkdir()
        (self.product / "package.json").write_text("{}", encoding="utf-8")

    def doubts(self, text: str) -> None:
        (self.ws / "DOUBTS.md").write_text(text, encoding="utf-8")

    def build(self) -> str:
        return build_phase.compute_build_phase(self.ws)["phase"]

    def plan(self) -> str:
        return plan_phase.compute_plan_phase(self.ws)["phase"]


class BuildChain(Workspace):
    def test_blocking_doubts_stop_the_build_before_a_task_is_picked(self) -> None:
        self.doubts(TWO_BLOCKING)
        result = build_phase.compute_build_phase(self.ws)
        self.assertEqual(result["phase"], "clarify")
        self.assertIn("DQ-001", result["reason"])
        self.assertIn("ask before building", result["reason"])

    def test_the_clarify_phase_loads_the_doubt_resolution_file(self) -> None:
        self.doubts(TWO_BLOCKING)
        result = build_phase.compute_build_phase(self.ws)
        self.assertTrue((Path(__file__).resolve().parent.parent / result["file"]).exists())
        self.assertIn("resolve-doubts", result["file"])

    def test_answered_and_deferred_doubts_let_the_build_continue(self) -> None:
        """Deferring is the documented way to proceed without an answer."""
        self.doubts(ANSWERED_AND_DEFERRED)
        self.assertEqual(self.build(), "implement")

    def test_a_doubt_waiting_on_another_is_not_asked_twice(self) -> None:
        self.doubts(CHAINED)
        result = build_phase.compute_build_phase(self.ws)
        self.assertIn("DQ-003", result["reason"])
        self.assertNotIn("DQ-004", result["reason"])

    def test_a_non_blocking_doubt_does_not_stop_the_build(self) -> None:
        self.doubts("# Doubts\n\n## DQ-005: Naming?\n- **Blocking:** no - does not block\n")
        self.assertEqual(self.build(), "implement")

    def test_no_doubts_file_is_not_a_gate(self) -> None:
        self.assertEqual(self.build(), "implement")


class PlanChain(Workspace):
    def test_blocking_doubts_stop_planning_without_needing_an_active_feature(self) -> None:
        self.doubts(TWO_BLOCKING)
        self.assertEqual(self.plan(), "resolve-doubts")

    def test_deferred_doubts_do_not_pin_the_plan_phase(self) -> None:
        self.doubts(ANSWERED_AND_DEFERRED)
        self.assertEqual(self.plan(), "council")


class Manifest(Workspace):
    def test_the_block_every_command_reads_names_the_answerable_doubts(self) -> None:
        self.doubts(TWO_BLOCKING)
        text = "\n".join(sl.attention_block(self.ws))
        self.assertIn("blocking doubt(s) can be answered now", text)
        self.assertIn("DQ-001", text)
        self.assertIn("loop doubts ask", text)

    def test_doubts_waiting_on_an_answer_are_reported_separately(self) -> None:
        self.doubts(CHAINED)
        text = "\n".join(sl.attention_block(self.ws))
        self.assertIn("wait on an earlier answer", text)

    def test_nothing_open_means_no_doubt_line(self) -> None:
        self.doubts(ANSWERED_AND_DEFERRED)
        text = "\n".join(sl.attention_block(self.ws))
        self.assertNotIn("blocking doubt(s) can be answered now", text)


if __name__ == "__main__":
    unittest.main()
