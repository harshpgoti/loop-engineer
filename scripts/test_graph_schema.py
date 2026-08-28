"""The model's invariants, each tested against the shape that violates it."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graph_index as gi  # noqa: E402
import graph_schema as gs  # noqa: E402

TASKS = """version: 1
tasks:
  - id: TASK-001
    title: First
    gate: G-ONE
    status: completed

  - id: TASK-002
    title: Second, resting on D-002 (the live decision)
    gate: G-ONE
    status: in_progress
    blocked_by: [TASK-001]
"""

# The same work, but pointed at D-001 - which D-002 superseded.
TASKS_ON_SUPERSEDED = TASKS.replace("resting on D-002 (the live decision)", "resting on D-001")

GATES = """# Gates

```yaml
gates:
  G-ONE:
    name: The gate
    status: blocked
```
"""

DOUBTS = "# Doubts\n\n### DQ-001: Open one\n- **Status:** open\n- **Question:** Given E-001?\n"

DECISIONS = """# Decision Log

### D-001: Original call
- **Date:** 2026-08-01
- **Decision:** Do it this way, per E-001.

### D-002: Replacement
- **Date:** 2026-08-10
- **Supersedes:** D-001
- **Decision:** No, this way instead, per E-001.
"""

EVIDENCE = "# Evidence Log\n\n### E-001: A fact\n- **Claim:** Something measured.\n"


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-schema-"))
        self.ws = self.tmp / "product" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        self.write(TASKS=TASKS, GATES=GATES)
        (self.ws / "DOUBTS.md").write_text(DOUBTS, encoding="utf-8")
        (self.ws / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
        (self.ws / "EVIDENCE_LOG.md").write_text(EVIDENCE, encoding="utf-8")
        (self.ws / "plan" / "main_plan.md").write_text("# Plan\n\n- **Name:** Test\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, **files: str) -> None:
        for name, body in files.items():
            (self.ws / f"{name}.yml").write_text(body, encoding="utf-8")

    def rules(self, level: str | None = None) -> set[str]:
        findings = gs.validate(self.ws)
        return {f["rule"] for f in findings if level is None or f["level"] == level}


class CleanWorkspace(Sandbox):
    def test_a_consistent_workspace_has_no_errors(self) -> None:
        self.assertEqual(set(), self.rules(gs.ERROR))

    def test_real_shapes_are_allowed(self) -> None:
        """A rule nobody can satisfy trains people to ignore the checker."""
        self.assertNotIn("edge-type", self.rules())

    def test_a_scoped_decision_amendment_is_a_known_non_superseding_edge(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            DECISIONS
            + "\n### D-003: Narrow exception\n- **Supersedes:** amends D-001 for row 12 only.\n",
            encoding="utf-8",
        )
        self.assertNotIn("unknown-edge", self.rules())
        self.assertNotIn("cites-superseded", self.rules())


class Supersession(Sandbox):
    def test_open_work_may_not_rest_on_a_superseded_decision(self) -> None:
        """The highest-value invariant in the ADR literature."""
        self.write(TASKS=TASKS_ON_SUPERSEDED, GATES=GATES)
        self.assertIn("cites-superseded", self.rules(gs.ERROR))

    def test_finished_work_may_cite_what_was_true_at_the_time(self) -> None:
        self.write(TASKS=TASKS_ON_SUPERSEDED.replace("status: in_progress", "status: completed"), GATES=GATES)
        self.assertNotIn("cites-superseded", self.rules())

    def test_pointing_at_the_live_decision_is_clean(self) -> None:
        self.assertNotIn("cites-superseded", self.rules())

    def test_a_supersession_cycle_is_an_error(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            DECISIONS + "\n### D-003: Circular\n- **Supersedes:** D-002\n- **Decision:** Back again.\n"
            "\n### D-004: Closes the loop\n- **Supersedes:** D-003\n- **Decision:** x.\n",
            encoding="utf-8",
        )
        text = (self.ws / "DECISIONS.md").read_text(encoding="utf-8")
        (self.ws / "DECISIONS.md").write_text(
            text.replace("### D-002: Replacement\n- **Date:** 2026-08-10\n- **Supersedes:** D-001",
                         "### D-002: Replacement\n- **Date:** 2026-08-10\n- **Supersedes:** D-001, D-004"),
            encoding="utf-8",
        )
        self.assertIn("supersession-cycle", self.rules(gs.ERROR))

    def test_two_live_decisions_superseding_the_same_one_is_an_error(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            DECISIONS + "\n### D-003: Also replaces it\n- **Supersedes:** D-001\n- **Decision:** A third way.\n",
            encoding="utf-8",
        )
        self.assertIn("supersession-fork", self.rules(gs.ERROR))


class References(Sandbox):
    def test_a_task_targeting_a_missing_gate_is_an_error(self) -> None:
        self.write(TASKS=TASKS.replace("gate: G-ONE", "gate: G-NOPE"), GATES=GATES)
        self.assertIn("missing-gate", self.rules(gs.ERROR))

    def test_a_reference_to_nothing_is_a_warning(self) -> None:
        (self.ws / "DOUBTS.md").write_text(
            DOUBTS + "\n### DQ-002: Broken\n- **Status:** open\n- **Question:** See E-999.\n", encoding="utf-8"
        )
        self.assertIn("dangling-reference", self.rules(gs.WARN))

    def test_an_impossible_edge_shape_is_reported(self) -> None:
        original = dict(gs.ALLOWED["blocked_by"])
        try:
            gs.ALLOWED["blocked_by"] = {(gi.GATE, gi.GATE)}
            self.assertIn("edge-type", self.rules(gs.WARN))
        finally:
            gs.ALLOWED["blocked_by"] = original


class Advisory(Sandbox):
    def test_a_decision_without_evidence_is_information_not_a_defect(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            "# Decision Log\n\n### D-009: A judgement call\n- **Decision:** Founder's choice.\n", encoding="utf-8"
        )
        findings = [f for f in gs.validate(self.ws) if f["rule"] == "unsupported-decision"]
        self.assertTrue(findings)
        self.assertEqual(gs.INFO, findings[0]["level"])

    def test_every_finding_names_a_fix_or_is_advisory(self) -> None:
        (self.ws / "DOUBTS.md").write_text(
            DOUBTS + "\n### DQ-002: Broken\n- **Status:** open\n- **Question:** See E-999.\n", encoding="utf-8"
        )
        for item in gs.validate(self.ws):
            if item["level"] in (gs.ERROR, gs.WARN):
                self.assertTrue(item["fix"], f"{item['rule']} has no suggested fix")

    def test_validation_never_raises_on_a_broken_workspace(self) -> None:
        (self.ws / "DECISIONS.md").write_text("### not a heading at all\n{{{", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text("!!! not yaml", encoding="utf-8")
        gs.validate(self.ws)  # must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
