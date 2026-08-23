"""Carving a map row out of the main product, and the ways it must refuse."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import subproduct_new as sp  # noqa: E402

MAP = """# Product Map

| ID | Step file | Type | Title | Depends on | Status |
|----|---|---|---|---|---|
| 01 | step_01 | sub-product | Auth Service | | **ACTIVE** - gated on `G-AUTH-01` |
| 02 | step_02 | module | Billing | | ACTIVE |
| 03 | step_03 | sub-product | Portal | | Deferred - later |
| 04 | step_04 | sub-product | | | ACTIVE |
"""

TASKS = """tasks:
  - id: TASK-001
    title: build auth
    gate: G-AUTH-01
    status: todo
  - id: TASK-002
    title: shared platform work
    gate: G-PLATFORM-01
    status: todo
  - id: TASK-003
    title: more auth
    gate: G-AUTH-01
    status: todo
"""

STEP_PLAN = """# Auth Service

Everything already planned for auth.
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.main = self.root / "Platform" / ".loop-engineer"
        (self.main / "plan").mkdir(parents=True)
        (self.main / "plan" / "PRODUCT_MAP.md").write_text(MAP, encoding="utf-8")
        (self.main / "plan" / "step_01_auth-service.md").write_text(STEP_PLAN, encoding="utf-8")
        (self.main / "TASKS.yml").write_text(TASKS, encoding="utf-8")
        (self.main / "memories").mkdir()
        (self.main / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")


class Refusals(Sandbox):
    def test_a_module_row_is_refused(self) -> None:
        """A module is built inside the main product; retyping it is a plan decision."""
        plan = sp.plan_row(self.main, "02")
        self.assertFalse(plan.ok)
        self.assertIn("not `sub-product`", plan.blockers[0])

    def test_a_row_that_does_not_exist_is_refused(self) -> None:
        self.assertIn("no row 99", sp.plan_row(self.main, "99").blockers[0])

    def test_a_row_with_no_title_is_refused(self) -> None:
        """The title is the folder name, and the folder name is what map_id binds on.

        The map parser drops a titleless row before this sees it, so the refusal reads
        "no row 04". Either way it is refused and never carved out under a blank name.
        """
        plan = sp.plan_row(self.main, "04")
        self.assertFalse(plan.ok)
        self.assertNotIn("04", {r["row"] for r in sp.carveable(self.main)})

    def test_a_single_digit_row_still_matches(self) -> None:
        self.assertEqual("01", sp.plan_row(self.main, "1").row_id)


class FolderNaming(Sandbox):
    def test_the_folder_comes_from_the_row_title(self) -> None:
        self.assertEqual("Auth Service", sp.plan_row(self.main, "01").folder.name)

    def test_the_workspace_is_always_the_nested_layout(self) -> None:
        """data_dir_for falls back to the folder itself when .loop-engineer is absent."""
        plan = sp.plan_row(self.main, "01")
        self.assertEqual(".loop-engineer", plan.workspace.name)
        self.assertEqual("Auth Service", plan.workspace.parent.name)


class TaskAttribution(Sandbox):
    def test_the_gate_comes_from_what_the_row_declares(self) -> None:
        self.assertEqual(["G-AUTH-01"], sp.declared_gates(self.main, "01"))

    def test_only_tasks_carrying_that_gate_are_reported(self) -> None:
        """Shared platform work must never be attributed to one row."""
        found = sp.task_candidates(self.main, "01", "Auth Service")
        self.assertEqual(["TASK-001", "TASK-003"], found)
        self.assertNotIn("TASK-002", found)

    def test_a_row_declaring_no_gate_reports_nothing(self) -> None:
        """Under-reporting an advisory list beats guessing at which tasks to move."""
        self.assertEqual([], sp.declared_gates(self.main, "03"))
        self.assertEqual([], sp.task_candidates(self.main, "03", "Portal"))


class Listing(Sandbox):
    def test_a_deferred_row_is_marked_later_not_ready(self) -> None:
        rows = {r["row"]: r for r in sp.carveable(self.main)}
        self.assertTrue(rows["03"]["dormant"])
        self.assertFalse(rows["01"]["dormant"])

    def test_module_rows_are_not_listed_at_all(self) -> None:
        self.assertNotIn("02", {r["row"] for r in sp.carveable(self.main)})


class Creating(Sandbox):
    def test_dry_run_writes_nothing(self) -> None:
        sp.create(self.main, "01", dry_run=True)
        self.assertFalse((self.root / "Platform" / "Auth Service").exists())

    def test_the_new_workspace_inherits_the_rows_plan(self) -> None:
        result = sp.create(self.main, "01")
        self.assertTrue(result["created"], result["blockers"])
        text = (Path(result["workspace"]) / "plan" / "main_plan.md").read_text(encoding="utf-8")
        self.assertIn("Everything already planned for auth.", text)
        self.assertIn("map row 01", text)

    def test_it_is_linked_by_map_id(self) -> None:
        result = sp.create(self.main, "01")
        meta = json.loads(
            (Path(result["workspace"]) / ".loop" / "workspace.json").read_text(encoding="utf-8")
        )
        self.assertEqual("sub", meta["role"])
        self.assertEqual("01", str(meta["map_id"]))

    def test_the_seeded_plan_does_not_point_at_a_missing_file(self) -> None:
        """The handover header names plan/PARENT_CONTEXT.md - it has to exist."""
        result = sp.create(self.main, "01")
        self.assertTrue((Path(result["workspace"]) / "plan" / "PARENT_CONTEXT.md").is_file())

    def test_creating_twice_refuses_rather_than_overwrites(self) -> None:
        sp.create(self.main, "01")
        again = sp.create(self.main, "01")
        self.assertFalse(again["created"])
        self.assertTrue(again["blockers"])

    def test_the_main_products_tasks_are_left_alone(self) -> None:
        before = (self.main / "TASKS.yml").read_text(encoding="utf-8")
        result = sp.create(self.main, "01")
        self.assertEqual(["TASK-001", "TASK-003"], result["tasks"])
        self.assertEqual(before, (self.main / "TASKS.yml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
