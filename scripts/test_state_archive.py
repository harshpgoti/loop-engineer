"""Compaction must shrink the file without the plan forgetting anything.

Every test here is an anti-rework invariant: if one of these breaks, a later session
re-compiles a finished task or re-asks an answered question.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doubts  # noqa: E402
import state_archive as sa  # noqa: E402
import task_context as tc  # noqa: E402


def _tasks(count: int) -> str:
    body = ["version: 1", "project: Test", "", "tasks:"]
    for i in range(1, count + 1):
        status = "completed" if i < count else "in_progress"
        body.append(
            f"""
  - id: TASK-{i:03d}
    title: Task number {i} with a reasonably long descriptive title
    phase: step2
    gate: G-MODULE-{i:02d}
    status: {status}
    priority: P0
    blocked_by: [TASK-{i - 1:03d}]
    acceptance:
      - {'a' * 200}
      - {'b' * 200}"""
        )
    return "\n".join(body) + "\n"


DOUBTS_BODY = """# Doubts

## Open Doubts

### DQ-001: Still open
- **Status:** open
- **Question:** What now?

### DQ-002: Answered properly
- **Status:** resolved
- **Question:** Which datastore?
- **Why it matters:** {pad}
- **Resolution (2026-08-01):** Postgres, for the JSONB support.

### DQ-003: Answered properly too
- **Status:** resolved
- **Question:** Which region?
- **Why it matters:** {pad}
- **Resolution (2026-08-02):** us-east-1.

### DQ-004: Also answered
- **Status:** resolved
- **Question:** Which runtime?
- **Why it matters:** {pad}
- **Resolution (2026-08-03):** Python 3.12.

### DQ-005: Closed with no answer recorded
- **Status:** resolved
- **Question:** What was decided here?
- **Why it matters:** {pad}

### DQ-DEP-008: Cloud provider
- **Status:** resolved
- **Question:** Which cloud?
- **Why it matters:** {pad}
- **Resolution (2026-08-04):** AWS.
""".format(pad="p" * 400)


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-archive-"))
        self.ws = self.tmp / "product" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(_tasks(20), encoding="utf-8")
        (self.ws / "DOUBTS.md").write_text(DOUBTS_BODY, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class TasksKeepTheirLedger(Sandbox):
    def test_it_actually_shrinks(self) -> None:
        before = len((self.ws / "TASKS.yml").read_text(encoding="utf-8"))
        sa.compact_tasks(self.ws)
        self.assertLess(len((self.ws / "TASKS.yml").read_text(encoding="utf-8")), before * 0.7)

    def test_no_task_disappears(self) -> None:
        """The invariant that prevents re-compiling finished work."""
        before = {t["id"] for t in tc.parse_tasks(self.ws)}
        sa.compact_tasks(self.ws)
        self.assertEqual(before, {t["id"] for t in tc.parse_tasks(self.ws)})

    def test_titles_and_status_survive(self) -> None:
        sa.compact_tasks(self.ws)
        done = [t for t in tc.parse_tasks(self.ws) if t.get("status") == "completed"]
        self.assertTrue(done)
        for task in done:
            self.assertTrue(task.get("title"), f"{task['id']} lost its title")

    def test_dependencies_still_resolve(self) -> None:
        """`blocked_by: [TASK-019]` must still find TASK-019."""
        sa.compact_tasks(self.ws)
        tasks = tc.parse_tasks(self.ws)
        active = tc.active_task(tasks)
        self.assertIsNotNone(active)
        self.assertEqual(["TASK-019"], [d["id"] for d in tc.dependencies(tasks, active)])

    def test_progress_count_is_unchanged(self) -> None:
        before = sum(1 for t in tc.parse_tasks(self.ws) if t.get("status") == "completed")
        sa.compact_tasks(self.ws)
        after = sum(1 for t in tc.parse_tasks(self.ws) if t.get("status") == "completed")
        self.assertEqual(before, after)

    def test_the_live_task_is_untouched(self) -> None:
        sa.compact_tasks(self.ws)
        text = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        self.assertIn("TASK-020", text)
        self.assertIn("a" * 200, text, "the active task keeps its acceptance criteria")

    def test_full_detail_is_in_the_archive(self) -> None:
        sa.compact_tasks(self.ws)
        archive = (self.ws / sa.TASKS_ARCHIVE).read_text(encoding="utf-8")
        self.assertIn("TASK-001", archive)
        self.assertIn("a" * 200, archive, "acceptance criteria are preserved, not deleted")

    def test_recent_completions_stay_in_full(self) -> None:
        sa.compact_tasks(self.ws)
        text = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        self.assertIn("TASK-019", text)
        self.assertNotIn("TASK-019", (self.ws / sa.TASKS_ARCHIVE).read_text(encoding="utf-8"))

    def test_running_twice_changes_nothing(self) -> None:
        """budget=0 forces a second pass, which is where the reserved-recent bug hid."""
        sa.compact_tasks(self.ws, budget=0)
        once = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        sa.compact_tasks(self.ws, budget=0)
        self.assertEqual(once, (self.ws / "TASKS.yml").read_text(encoding="utf-8"))
        self.assertIn("TASK-019", once, "the reserved recent task must survive both passes")

    def test_small_file_is_left_alone(self) -> None:
        (self.ws / "TASKS.yml").write_text(_tasks(2), encoding="utf-8")
        before = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        result = sa.compact_tasks(self.ws)
        self.assertIn("under budget", result["skipped"])
        self.assertEqual(before, (self.ws / "TASKS.yml").read_text(encoding="utf-8"))


class DoubtsKeepTheirAnswers(Sandbox):
    def test_no_doubt_disappears(self) -> None:
        before = {d.id for d in doubts.parse(self.ws)}
        sa.compact_doubts(self.ws, budget=0)
        self.assertEqual(before, {d.id for d in doubts.parse(self.ws)})

    def test_counts_are_unchanged(self) -> None:
        before = doubts.counts(self.ws)
        sa.compact_doubts(self.ws, budget=0)
        self.assertEqual(before, doubts.counts(self.ws))

    def test_the_answer_stays_inline(self) -> None:
        """`reuse, don't re-ask` reads this without opening the archive."""
        sa.compact_doubts(self.ws, budget=0, keep=0)
        text = (self.ws / "DOUBTS.md").read_text(encoding="utf-8")
        self.assertIn("Postgres, for the JSONB support.", text)

    def test_a_doubt_with_no_recorded_answer_is_left_in_full(self) -> None:
        """Compacting it would strip the question and leave nothing behind."""
        result = sa.compact_doubts(self.ws, budget=0, keep=0)
        self.assertIn("DQ-005", result["unanswered"])
        self.assertNotIn("DQ-005", result["compacted"])
        self.assertIn("What was decided here?", (self.ws / "DOUBTS.md").read_text(encoding="utf-8"))

    def test_deployment_ids_survive_so_they_are_not_re_asked(self) -> None:
        """deployment_plan dedupes on `doubt_id in doubts_text` - losing the id re-asks."""
        sa.compact_doubts(self.ws, budget=0, keep=0)
        self.assertIn("DQ-DEP-008", (self.ws / "DOUBTS.md").read_text(encoding="utf-8"))

    def test_open_doubts_are_untouched(self) -> None:
        sa.compact_doubts(self.ws, budget=0, keep=0)
        self.assertIn("What now?", (self.ws / "DOUBTS.md").read_text(encoding="utf-8"))

    def test_rationale_is_archived_not_lost(self) -> None:
        sa.compact_doubts(self.ws, budget=0, keep=0)
        archive = (self.ws / sa.DOUBTS_ARCHIVE).read_text(encoding="utf-8")
        self.assertIn("Which datastore?", archive)
        self.assertIn("p" * 400, archive)

    def test_running_twice_changes_nothing(self) -> None:
        sa.compact_doubts(self.ws, budget=0, keep=0)
        once = (self.ws / "DOUBTS.md").read_text(encoding="utf-8")
        sa.compact_doubts(self.ws, budget=0, keep=0)
        self.assertEqual(once, (self.ws / "DOUBTS.md").read_text(encoding="utf-8"))


EVIDENCE = """# Evidence Log

### E-001: Competitors target enterprise
- **Type:** verified_fact
- **Claim:** {pad}
- **Source:** https://example.com/a
- **Confidence:** high

### E-002: Bundling is the kill-shot risk
- **Type:** verified_fact
- **Claim:** {pad}
- **Source:** https://example.com/b
- **Confidence:** high

### E-003: Still being argued about
- **Type:** assumption
- **Claim:** {pad}
- **Source:** https://example.com/c
- **Confidence:** low

### E-004: Also settled
- **Type:** verified_fact
- **Claim:** {pad}
- **Confidence:** medium

### E-005: Settled too
- **Type:** verified_fact
- **Claim:** {pad}
- **Confidence:** medium
""".format(pad="c" * 700)

DECISIONS = """# Decision Log

### D-001: Flat fee pricing
- **Date:** 2026-08-01
- **Decision:** Flat per-claim fee only.
- **Supersedes:** DQ-002
- **Rationale:** {pad}
- **Consequences:** {pad}

### D-002: Postgres
- **Date:** 2026-08-02
- **Decision:** Postgres with JSONB.
- **Rationale:** {pad}

### D-003: Region
- **Date:** 2026-08-03
- **Decision:** us-east-1.
- **Rationale:** {pad}

### D-004: Runtime
- **Date:** 2026-08-04
- **Decision:** Python 3.12.
- **Rationale:** {pad}
""".format(pad="r" * 700)


class EvidenceAndDecisions(Sandbox):
    def setUp(self) -> None:
        super().setUp()
        (self.ws / "EVIDENCE_LOG.md").write_text(EVIDENCE, encoding="utf-8")
        (self.ws / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
        # E-003 is cited by an open doubt, so it is live.
        (self.ws / "DOUBTS.md").write_text(
            DOUBTS_BODY + "\n### DQ-100: Pricing risk\n- **Status:** open\n"
            "- **Question:** Does E-003 still hold?\n",
            encoding="utf-8",
        )

    def test_evidence_cited_by_an_open_doubt_is_kept_in_full(self) -> None:
        """The user's rule: evidence still being argued about stays."""
        result = sa.compact_evidence(self.ws, budget=0, keep=0)
        self.assertIn("E-003", result["live"])
        self.assertNotIn("E-003", result["compacted"])
        self.assertIn("c" * 700, (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8"))

    def test_settled_evidence_is_compacted(self) -> None:
        result = sa.compact_evidence(self.ws, budget=0, keep=0)
        self.assertIn("E-001", result["compacted"])
        self.assertLess(result["after"], result["before"] * 0.6)

    def test_every_evidence_id_still_resolves(self) -> None:
        """A decision citing E-001 must still find it."""
        sa.compact_evidence(self.ws, budget=0, keep=0)
        text = (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8")
        for eid in ("E-001", "E-002", "E-003", "E-004", "E-005"):
            self.assertIn(eid, text)

    def test_the_headline_finding_survives_compaction(self) -> None:
        sa.compact_evidence(self.ws, budget=0, keep=0)
        text = (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8")
        self.assertIn("Competitors target enterprise", text)

    def test_sourcing_is_archived_not_deleted(self) -> None:
        sa.compact_evidence(self.ws, budget=0, keep=0)
        archive = (self.ws / sa.EVIDENCE_ARCHIVE).read_text(encoding="utf-8")
        self.assertIn("https://example.com/a", archive)
        self.assertIn("c" * 700, archive)

    def test_decision_text_and_supersedes_survive(self) -> None:
        """`hierarchy_drift` keys on these; `doubts.supersessions` reads Supersedes."""
        import doubts as doubts_mod
        import hierarchy_drift as drift

        before_topics = set(drift.decisions_labels(self.ws))
        before_sup = doubts_mod.supersessions(self.ws)
        sa.compact_decisions(self.ws, budget=0, keep=0)
        self.assertEqual(before_topics, set(drift.decisions_labels(self.ws)))
        self.assertEqual(before_sup, doubts_mod.supersessions(self.ws))

    def test_decision_rationale_moves_to_the_archive(self) -> None:
        sa.compact_decisions(self.ws, budget=0, keep=0)
        self.assertNotIn("r" * 700, (self.ws / "DECISIONS.md").read_text(encoding="utf-8"))
        self.assertIn("r" * 700, (self.ws / sa.DECISIONS_ARCHIVE).read_text(encoding="utf-8"))

    def test_both_are_idempotent(self) -> None:
        for fn in (sa.compact_evidence, sa.compact_decisions):
            fn(self.ws, budget=0, keep=0)
        once = (
            (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8"),
            (self.ws / "DECISIONS.md").read_text(encoding="utf-8"),
        )
        for fn in (sa.compact_evidence, sa.compact_decisions):
            fn(self.ws, budget=0, keep=0)
        self.assertEqual(
            once,
            (
                (self.ws / "EVIDENCE_LOG.md").read_text(encoding="utf-8"),
                (self.ws / "DECISIONS.md").read_text(encoding="utf-8"),
            ),
        )


class Retrieval(Sandbox):
    def test_archived_detail_is_searchable(self) -> None:
        sa.compact_doubts(self.ws, budget=0, keep=0)
        hits = sa.search_archive(self.ws, "datastore")
        self.assertTrue(hits)
        self.assertIn("DQ-002", "\n".join(hits))

    def test_search_misses_are_reported_as_misses(self) -> None:
        sa.compact_doubts(self.ws, budget=0, keep=0)
        self.assertEqual([], sa.search_archive(self.ws, "kubernetes"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
