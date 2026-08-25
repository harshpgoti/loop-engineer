"""Folding a sub-product workspace into the main product, and the ways it must refuse."""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contracts as ct  # noqa: E402
import scope_absorb as ab  # noqa: E402
import scope_paths as sp  # noqa: E402
import scope_state as st  # noqa: E402
import session_store  # noqa: E402


MAP = """# Product Map

| ID | Step file | Type | Title | Depends on | Status |
|----|---|---|---|---|---|
| 01 | step_01 | sub-product | Auth Service | | ACTIVE |
| 02 | step_02 | sub-product | Portal | 01 | ACTIVE |
"""

CHILD_TASKS = """tasks:
  - id: TASK-001
    title: session endpoint
    gate: G-AUTH-01
    status: done
  - id: TASK-002
    title: tenant claims
    gate: G-AUTH-01
    status: todo
    blocked_by: [TASK-001]
  - id: TASK-003
    title: needs something gone
    status: todo
    blocked_by: [TASK-404]
"""

CHILD_GATES = """gates:
  G-AUTH-01:
    name: Auth usable
    status: blocked
"""

CHILD_DOUBTS = """# Doubts

## DQ-007: Which token lifetime?
Blocks TASK-002.
"""

MAIN_DECISIONS = """# Decisions

| Topic | Decision |
|---|---|
| Datastore | Postgres |
"""

CHILD_DECISIONS_OK = """# Decisions

| Topic | Decision |
|---|---|
| Token format | JWT with tenant claims |
"""

CHILD_DECISIONS_CONFLICT = """# Decisions

| Topic | Decision |
|---|---|
| Datastore | DynamoDB |
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.product = self.root / "Platform"
        self.main = self.product / ".loop-engineer"
        (self.main / "plan").mkdir(parents=True)
        (self.main / "plan" / "PRODUCT_MAP.md").write_text(MAP, encoding="utf-8")
        (self.main / "DECISIONS.md").write_text(MAIN_DECISIONS, encoding="utf-8")
        (self.main / "memories").mkdir()
        (self.main / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")

        self.child_folder = self.product / "auth-service"
        self.child = self.child_folder / ".loop-engineer"
        (self.child / "plan").mkdir(parents=True)
        (self.child / "plan" / "main_plan.md").write_text(
            "# Auth Service\n\nPlanned in full. TASK-002 is next.\n", encoding="utf-8"
        )
        (self.child / "plan" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
        (self.child / "plan" / "PARENT_CONTEXT.md").write_text("# generated\n", encoding="utf-8")
        (self.child / "plan" / "steps").mkdir()
        (self.child / "plan" / "steps" / "01-core.md").write_text("Step. See TASK-001.\n", encoding="utf-8")
        (self.child / "TASKS.yml").write_text(CHILD_TASKS, encoding="utf-8")
        (self.child / "GATES.yml").write_text(CHILD_GATES, encoding="utf-8")
        (self.child / "DOUBTS.md").write_text(CHILD_DOUBTS, encoding="utf-8")
        (self.child / "DECISIONS.md").write_text(CHILD_DECISIONS_OK, encoding="utf-8")
        (self.child / "memories").mkdir()
        (self.child / "memories" / "MEMORY.md").write_text("# Memory\n\nAuth decided on JWT.\n", encoding="utf-8")
        (self.child / ".loop").mkdir()
        (self.child / ".loop" / "workspace.json").write_text(
            json.dumps({"role": "sub", "parent": "..", "map_id": "01"}), encoding="utf-8"
        )
        (self.child / ".loop" / "parent-sync.json").write_text("{}", encoding="utf-8")
        session_store.log_session(
            self.child / "state.db", workspace=str(self.child), title="auth session", body="did work"
        )

    def absorb(self, **kwargs):
        plan = ab.plan_absorb(self.main, self.child_folder, **kwargs)
        self.assertTrue(plan.ok, plan.blockers)
        return plan, ab.apply_absorb(self.main, plan)


class Refusals(Sandbox):
    def test_a_folder_with_no_workspace_is_refused(self) -> None:
        plain = self.product / "docs-site"
        plain.mkdir()
        plan = ab.plan_absorb(self.main, plain)
        self.assertFalse(plan.ok)
        self.assertIn("holds no loop workspace", plan.blockers[0])

    def test_an_unbound_folder_is_refused_rather_than_guessed(self) -> None:
        other = self.product / "mystery"
        (other / ".loop-engineer" / "plan").mkdir(parents=True)
        (other / ".loop-engineer" / "memories").mkdir()
        plan = ab.plan_absorb(self.main, other)
        self.assertFalse(plan.ok)
        self.assertIn("--map-id", plan.blockers[0])

    def test_an_explicit_map_id_unblocks_an_unbound_folder(self) -> None:
        other = self.product / "mystery"
        (other / ".loop-engineer" / "plan").mkdir(parents=True)
        (other / ".loop-engineer" / "memories").mkdir()
        plan = ab.plan_absorb(self.main, other, map_id="02")
        self.assertTrue(plan.ok, plan.blockers)
        self.assertEqual(plan.map_id, "02")

    def test_an_existing_scope_is_refused_without_merge(self) -> None:
        sp.create_scope(self.main, "auth-service", name="Auth Service", map_id="01")
        plan = ab.plan_absorb(self.main, self.child_folder)
        self.assertFalse(plan.ok)
        self.assertIn("--merge", plan.blockers[0])

    def test_staged_writes_block_the_absorb(self) -> None:
        pending = self.child / ".loop" / "pending" / "memory"
        pending.mkdir(parents=True)
        (pending / "note.json").write_text("{}", encoding="utf-8")
        plan = ab.plan_absorb(self.main, self.child_folder)
        self.assertFalse(plan.ok)
        self.assertIn("staged write", plan.blockers[0])

    def test_a_main_product_with_children_is_refused(self) -> None:
        (self.child / ".loop" / "workspace.json").write_text(
            json.dumps({"role": "main", "children": [{"name": "x", "path": "x"}]}), encoding="utf-8"
        )
        plan = ab.plan_absorb(self.main, self.child_folder)
        self.assertFalse(plan.ok)
        self.assertIn("absorb its children first", plan.blockers[0])

    def test_a_decision_conflict_stops_and_asks(self) -> None:
        """The one thing that must never be auto-merged."""
        (self.child / "DECISIONS.md").write_text(CHILD_DECISIONS_CONFLICT, encoding="utf-8")
        plan = ab.plan_absorb(self.main, self.child_folder)
        self.assertTrue(plan.ok, "a conflict is not a blocker - it is a question")
        self.assertEqual(len(plan.decision_conflicts), 1)
        self.assertIn("Datastore", plan.decision_conflicts[0])
        with self.assertRaises(SystemExit) as caught:
            ab.apply_absorb(self.main, plan)
        self.assertIn("decided the same topic differently", str(caught.exception))

    def test_nothing_is_written_when_the_plan_refuses(self) -> None:
        (self.child / "DECISIONS.md").write_text(CHILD_DECISIONS_CONFLICT, encoding="utf-8")
        plan = ab.plan_absorb(self.main, self.child_folder)
        with self.assertRaises(SystemExit):
            ab.apply_absorb(self.main, plan)
        self.assertFalse(sp.scopes_dir(self.main).exists())
        self.assertTrue(self.child.is_dir(), "the child workspace must be untouched")


class Renaming(Sandbox):
    def test_ids_are_namespaced_to_the_scope(self) -> None:
        self.assertEqual(ab.task_rename("TASK-001", "auth"), "AUTH-TASK-001")
        self.assertEqual(ab.gate_rename("G-AUTH-01", "auth"), "G-AUTH-01")
        self.assertEqual(ab.gate_rename("G-CORE-01", "auth"), "G-AUTH-CORE-01")
        self.assertEqual(ab.doubt_rename("DQ-007", "auth"), "DQ-AUTH-007")

    def test_renaming_is_idempotent(self) -> None:
        """A second absorb must not turn AUTH-TASK-001 into AUTH-AUTH-TASK-001."""
        once = ab.task_rename("TASK-001", "auth")
        self.assertEqual(ab.task_rename(once, "auth"), once)
        self.assertEqual(ab.gate_rename(ab.gate_rename("G-CORE-01", "auth"), "auth"), "G-AUTH-CORE-01")


class Absorbing(Sandbox):
    def test_the_scope_is_created_and_bound_by_map_id(self) -> None:
        plan, report = self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        self.assertIsNotNone(scope)
        self.assertEqual(scope.map_id, "01")
        self.assertEqual(scope.code_dir, "auth-service")
        self.assertEqual(scope.name, "Auth Service")

    def test_tasks_move_with_their_ids_rewritten_everywhere(self) -> None:
        self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        tasks = scope.tasks_file.read_text(encoding="utf-8")
        self.assertIn("AUTH-SERVICE-TASK-001", tasks)
        self.assertNotIn("id: TASK-001", tasks)
        self.assertIn("blocked_by: [AUTH-SERVICE-TASK-001]", tasks)
        step = (scope.path / "steps" / "01-core.md").read_text(encoding="utf-8")
        self.assertIn("AUTH-SERVICE-TASK-001", step)

    def test_gate_references_inside_tasks_are_rewritten_too(self) -> None:
        self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        self.assertIn("G-AUTH-SERVICE-AUTH-01", scope.tasks_file.read_text(encoding="utf-8"))
        self.assertIn("G-AUTH-SERVICE-AUTH-01", scope.gates_file.read_text(encoding="utf-8"))

    def test_a_dangling_blocker_becomes_a_doubt_not_a_silent_drop(self) -> None:
        plan, report = self.absorb()
        self.assertEqual(len(report["doubts"]), 1)
        doubts = (sp.find_scope(self.main, "auth-service").doubts_file).read_text(encoding="utf-8")
        self.assertIn("TASK-404", doubts)

    def test_the_child_plan_becomes_the_scope_prd(self) -> None:
        self.absorb()
        prd = (sp.find_scope(self.main, "auth-service").path / "prd.md").read_text(encoding="utf-8")
        self.assertIn("## From sub-product plan", prd)
        self.assertIn("Planned in full", prd)

    def test_authored_plan_files_come_across(self) -> None:
        self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        self.assertTrue((scope.path / "architecture.md").is_file())

    def test_generated_hierarchy_files_are_dropped(self) -> None:
        plan, report = self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        self.assertFalse((scope.path / "PARENT_CONTEXT.md").exists())
        self.assertIn("plan/PARENT_CONTEXT.md", report["dropped"])

    def test_decisions_merge_into_the_shared_file_tagged_by_scope(self) -> None:
        self.absorb()
        text = (self.main / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("Datastore", text)
        self.assertIn("Token format", text)
        self.assertIn("absorbed:auth-service", text)

    def test_memory_becomes_a_per_scope_file(self) -> None:
        self.absorb()
        path = self.main / "memories" / "scopes" / "auth-service.md"
        self.assertTrue(path.is_file())
        self.assertIn("JWT", path.read_text(encoding="utf-8"))
        self.assertEqual((self.main / "memories" / "MEMORY.md").read_text(encoding="utf-8"), "# Memory\n")

    def test_sessions_fold_in_carrying_their_scope(self) -> None:
        plan, report = self.absorb()
        self.assertEqual(report["sessions"], 1)
        conn = sqlite3.connect(self.main / "state.db")
        rows = conn.execute("SELECT title, scope FROM sessions").fetchall()
        conn.close()
        self.assertEqual(rows, [("auth session", "auth-service")])

    def test_the_map_row_points_at_the_scope(self) -> None:
        self.absorb()
        text = (self.main / "plan" / "PRODUCT_MAP.md").read_text(encoding="utf-8")
        self.assertIn("Scope", text)
        self.assertIn("`plan/products/auth-service`", text)

    def test_the_child_workspace_is_archived_not_deleted(self) -> None:
        """Kept as a backup of what was absorbed - nothing reads it, but losing it
        would mean the absorb had no undo of any kind."""
        plan, report = self.absorb()
        self.assertFalse(self.child.exists(), "the live path must stop resolving")
        archived = list(self.child_folder.glob(".loop-engineer.absorbed-*"))
        self.assertEqual(len(archived), 1)
        self.assertTrue((archived[0] / "TASKS.yml").is_file())

    def test_resolution_no_longer_finds_the_dead_workspace(self) -> None:
        """The single worst failure this migration could leave behind."""
        self.absorb()
        import workspace_resolver as wr

        self.assertFalse(wr.has_local_loop_data(self.child_folder))

    def test_a_pointer_file_is_written_so_cd_still_works(self) -> None:
        self.absorb()
        self.assertEqual(
            (self.child_folder / sp.POINTER_FILE).read_text(encoding="utf-8").strip(), "auth-service"
        )

    def test_the_absorbed_tasks_load_through_the_union_loader(self) -> None:
        self.absorb()
        ids = {t["id"]: t["scope"] for t in st.load_tasks(self.main)}
        self.assertEqual(ids.get("AUTH-SERVICE-TASK-002"), "auth-service")


class Integrations(Sandbox):
    def test_the_provider_scope_records_what_it_now_provides(self) -> None:
        """Otherwise every absorb emits a `contract-undeclared` warning about bookkeeping."""
        (self.child / "plan" / "INTEGRATIONS.yml").write_text(
            "integrations:\n  - counterparty: Portal\n", encoding="utf-8"
        )
        sp.create_scope(self.main, "portal", name="Portal", map_id="02")
        self.absorb()
        provider = sp.find_scope(self.main, "portal")
        self.assertEqual(provider.provides, ["portal.auth-service-v1"])
        self.assertNotIn("contract-undeclared", [f.kind for f in ct.check(self.main, tasks=[])])

    def test_declared_integrations_become_draft_contracts(self) -> None:
        (self.child / "plan" / "INTEGRATIONS.yml").write_text(
            "integrations:\n  - counterparty: Portal\n    status: planned\n", encoding="utf-8"
        )
        sp.create_scope(self.main, "portal", name="Portal", map_id="02")
        self.absorb()
        ids = [c.id for c in ct.list_contracts(self.main)]
        self.assertEqual(ids, ["portal.auth-service-v1"])
        self.assertEqual(ct.list_contracts(self.main)[0].status, ct.DRAFT)

    def test_an_integration_naming_no_scope_stays_loud(self) -> None:
        """An unsatisfiable dependency must surface, not vanish into a draft."""
        (self.child / "plan" / "INTEGRATIONS.yml").write_text(
            "integrations:\n  - counterparty: Search\n", encoding="utf-8"
        )
        self.absorb()
        kinds = [f.kind for f in ct.check(self.main, tasks=[])]
        self.assertIn("contract-unprovided", kinds)


class Ordering(Sandbox):
    def _second_child(self) -> Path:
        folder = self.product / "portal"
        ws = folder / ".loop-engineer"
        (ws / "plan").mkdir(parents=True)
        (ws / "plan" / "main_plan.md").write_text("# Portal\n", encoding="utf-8")
        (ws / "memories").mkdir()
        (ws / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
        return folder

    def test_dependencies_are_absorbed_before_their_dependents(self) -> None:
        portal = self._second_child()
        ordered = ab.order_folders(self.main, [portal, self.child_folder])
        self.assertEqual([f.name for f in ordered], ["auth-service", "portal"])

    def test_discover_finds_the_sub_product_workspaces(self) -> None:
        self._second_child()
        found = {f.name for f in ab.discover(self.main)}
        self.assertEqual(found, {"auth-service", "portal"})


class Idempotence(Sandbox):
    def test_absorbing_twice_does_not_double_prefix_or_duplicate_decisions(self) -> None:
        self.absorb()
        plan2 = ab.plan_absorb(self.main, self.child_folder)
        self.assertFalse(plan2.ok, "the archived workspace must not be absorbed again")
        text = (self.main / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("absorbed:auth-service"), 1)


if __name__ == "__main__":
    unittest.main()
