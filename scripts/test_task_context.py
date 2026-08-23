"""A build session must read the slice for its task, not the whole workspace."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_phase  # noqa: E402
import task_context as tc  # noqa: E402
from memory_paths import session_bootstrap_paths  # noqa: E402

TASKS = """version: 1
project: Test

tasks:
  - id: TASK-001
    title: Scaffold the repo
    phase: step2
    gate: G-PLATFORM-01
    status: completed
    priority: P0

  - id: TASK-002
    title: Build the token issuer
    phase: step2
    gate: G-MODULE-01
    status: in_progress
    priority: P0
    blocked_by: [TASK-001]
    acceptance:
      - issues signed tokens
      - rejects expired input

  - id: TASK-003
    title: Ship the UI
    phase: step2
    gate: G-UI-01
    status: blocked
    priority: P1
    blocked_by: [TASK-002]
"""

GATES = """# Gates

```yaml
gates:
  G-PLATFORM-01:
    name: Platform core
    status: passed

  G-MODULE-01:
    name: First product step
    criteria:
      - first step implemented
      - relevant tests pass
    status: blocked

  # ---- later gates ----
  G-UI-01:
    name: Product UI
    status: blocked
```
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-taskctx-"))
        self.ws = self.tmp / "product" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(TASKS, encoding="utf-8")
        (self.ws / "GATES.yml").write_text(GATES, encoding="utf-8")
        (self.ws / "DOUBTS.md").write_text(
            "# Doubts\n\n### DQ-001: Token lifetime\n- **Status:** open\n"
            "- **Question:** How long should a token live?\n",
            encoding="utf-8",
        )
        (self.ws / "plan" / "main_plan.md").write_text("# Plan\n\n- **Name:** Test\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class Slicing(Sandbox):
    def test_picks_the_in_progress_task(self) -> None:
        tasks = tc.parse_tasks(self.ws)
        self.assertEqual(3, len(tasks))
        self.assertEqual("TASK-002", tc.active_task(tasks)["id"])

    def test_falls_back_to_the_first_unblocked_task(self) -> None:
        (self.ws / "TASKS.yml").write_text(TASKS.replace("status: in_progress", "status: pending"), encoding="utf-8")
        self.assertEqual("TASK-002", tc.active_task(tc.parse_tasks(self.ws))["id"])

    def test_a_task_with_unmet_dependencies_is_not_selected(self) -> None:
        body = TASKS.replace("status: in_progress", "status: pending").replace("status: completed", "status: pending")
        (self.ws / "TASKS.yml").write_text(body, encoding="utf-8")
        self.assertEqual("TASK-001", tc.active_task(tc.parse_tasks(self.ws))["id"])

    def test_context_holds_the_task_its_dependency_and_its_gate(self) -> None:
        text = tc.render(self.ws)
        self.assertIn("TASK-002", text)
        self.assertIn("TASK-001", text)
        self.assertIn("G-MODULE-01", text)
        self.assertIn("rejects expired input", text)

    def test_context_excludes_other_tasks_and_gates(self) -> None:
        """The whole point: 37 irrelevant tasks are attention, not just tokens."""
        text = tc.render(self.ws)
        self.assertNotIn("TASK-003", text)
        self.assertNotIn("Ship the UI", text)
        self.assertNotIn("G-UI-01", text)

    def test_gate_extraction_stops_at_the_next_gate(self) -> None:
        block = tc.gate_block(self.ws, "G-MODULE-01")
        self.assertIn("relevant tests pass", block)
        self.assertNotIn("G-UI-01", block)
        self.assertNotIn("later gates", block)

    def test_blocking_doubts_are_carried_in(self) -> None:
        self.assertIn("DQ-001", tc.render(self.ws))

    def test_no_tasks_file_is_not_an_error(self) -> None:
        (self.ws / "TASKS.yml").unlink()
        self.assertIsNone(tc.write_context(self.ws))

    def test_slice_size_does_not_grow_with_the_backlog(self) -> None:
        """The property that matters: O(1) in task count, where the file is O(n).

        A fixed header means the slice only wins on a real backlog - on the real
        workspace this replaced 43,308 chars with 3,911.
        """
        small = len(tc.render(self.ws))

        extra = "".join(
            f"\n  - id: TASK-1{i:02d}\n    title: Later work {i}\n    phase: step2\n"
            f"    gate: G-UI-01\n    status: blocked\n    priority: P2\n"
            f"    blocked_by: [TASK-003]\n    acceptance:\n      - {'y' * 120}\n"
            for i in range(40)
        )
        (self.ws / "TASKS.yml").write_text(TASKS + extra, encoding="utf-8")

        grown_file = len((self.ws / "TASKS.yml").read_text(encoding="utf-8"))
        grown_slice = len(tc.render(self.ws))

        self.assertGreater(grown_file, 8000, "the backlog really did grow")
        self.assertLess(grown_slice - small, 200, "the slice must stay flat")
        self.assertLess(grown_slice, grown_file // 2)


class ReadOrder(Sandbox):
    def test_build_session_swaps_the_full_files_for_the_slice(self) -> None:
        tc.write_context(self.ws)
        names = {p.name for p in session_bootstrap_paths(self.ws, "/develop-product")}
        self.assertIn("BUILD_CONTEXT.md", names)
        for dropped in ("TASKS.yml", "GATES.yml", "DOUBTS.md"):
            self.assertNotIn(dropped, names)

    def test_planning_session_still_reads_the_full_files(self) -> None:
        """Planning edits them - it must not be handed a read-only slice."""
        tc.write_context(self.ws)
        names = {p.name for p in session_bootstrap_paths(self.ws, "/plan-loop")}
        self.assertIn("TASKS.yml", names)
        self.assertIn("GATES.yml", names)
        self.assertNotIn("BUILD_CONTEXT.md", names)

    def test_no_slice_means_no_swap(self) -> None:
        names = {p.name for p in session_bootstrap_paths(self.ws, "/develop-product")}
        self.assertIn("TASKS.yml", names)


class Phases(Sandbox):
    def _phase(self) -> str:
        return build_phase.compute_build_phase(self.ws)["phase"]

    def test_no_source_tree_routes_to_scaffold(self) -> None:
        self.assertEqual("scaffold", self._phase())

    def test_active_task_routes_to_implement(self) -> None:
        (self.ws.parent / "src").mkdir(parents=True, exist_ok=True)
        self.assertEqual("implement", self._phase())

    def test_qa_task_routes_to_test(self) -> None:
        (self.ws.parent / "src").mkdir(parents=True, exist_ok=True)
        (self.ws / "TASKS.yml").write_text(TASKS.replace("phase: step2\n    gate: G-MODULE-01", "phase: qa\n    gate: G-QA-01"), encoding="utf-8")
        self.assertEqual("test", self._phase())

    def test_each_phase_names_a_file_that_exists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for phase, rel in build_phase.PHASE_FILES.items():
            self.assertTrue((root / rel).is_file(), f"{phase} -> {rel} is missing")

    def test_each_phase_loads_only_its_own_skills(self) -> None:
        root = Path(__file__).resolve().parents[1]
        for phase, skills in build_phase.PHASE_SKILLS.items():
            self.assertTrue(skills, f"{phase} names no skills")
            for skill in skills:
                self.assertTrue((root / skill).is_file(), f"{phase} -> {skill} is missing")
        self.assertNotIn("skills/security-compliance/SKILL.md", build_phase.PHASE_SKILLS["implement"])


class CompactBound(Sandbox):
    def test_oversized_compact_is_trimmed_on_a_section_boundary(self) -> None:
        import compact_context as cc

        body = "# Compact\n\nintro\n" + "".join(f"\n## Section {i}\n\n{'x' * 900}\n" for i in range(20))
        trimmed = cc.enforce_limit(body, limit=4000)
        self.assertLessEqual(len(trimmed), 4600, "must be near the limit")
        self.assertIn("## Section 0", trimmed)
        self.assertIn("trimmed", trimmed)

    def test_small_compact_is_untouched(self) -> None:
        import compact_context as cc

        body = "# Compact\n\n## One\n\nshort\n"
        self.assertEqual(body, cc.enforce_limit(body))


if __name__ == "__main__":
    unittest.main(verbosity=2)
