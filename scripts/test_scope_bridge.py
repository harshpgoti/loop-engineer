"""Absorbing a sub-product, and what must not follow it into the platform.

Every case here was found by absorbing a real three-sub-product platform, not by reading
the code - which is why each test names the symptom it prevents. The federated bridge
these once guarded is gone (`docs/SCOPES.md`); what remains is what absorb still has to
get right.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hierarchy_drift as drift  # noqa: E402
import scope_absorb as ab  # noqa: E402
import scope_paths as sp  # noqa: E402
import session_store  # noqa: E402
from workspace_tree import describe_tree, read_meta, resolve_children  # noqa: E402


MAP = """# Product Map

| ID | Step file | Type | Title | Depends on | Status |
|----|---|---|---|---|---|
| 01 | step_01 | sub-product | Auth Service | | ACTIVE |
| 02 | step_02 | sub-product | Portal | 01 | ACTIVE |
"""

MAIN_DECISIONS = """# Decisions

| Topic | Decision |
|---|---|
| Datastore | Postgres |
"""

CHILD_DECISIONS = """# Decisions

| Topic | Decision |
|---|---|
| Token format | JWT with tenant claims |
"""


class Platform(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.product = self.root / "Platform"
        self.main = self.product / ".loop-engineer"
        (self.main / "plan").mkdir(parents=True)
        (self.main / "plan" / "PRODUCT_MAP.md").write_text(MAP, encoding="utf-8")
        (self.main / "plan" / "main_plan.md").write_text("# Platform\n", encoding="utf-8")
        (self.main / "DECISIONS.md").write_text(MAIN_DECISIONS, encoding="utf-8")
        (self.main / "EVIDENCE_LOG.md").write_text("# Evidence\n", encoding="utf-8")
        (self.main / "memories").mkdir()
        (self.main / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")

        self.child_folder = self.product / "auth-service"
        self.child = self.child_folder / ".loop-engineer"
        (self.child / "plan").mkdir(parents=True)
        (self.child / "plan" / "main_plan.md").write_text("# Auth\n", encoding="utf-8")
        (self.child / "memories").mkdir()
        (self.child / "memories" / "MEMORY.md").write_text("# Memory\n\nauth notes.\n", encoding="utf-8")
        (self.child / "TASKS.yml").write_text("tasks:\n  - id: TASK-001\n    title: x\n    status: todo\n", encoding="utf-8")
        (self.child / "DECISIONS.md").write_text(CHILD_DECISIONS, encoding="utf-8")
        (self.child / "EVIDENCE_LOG.md").write_text("# Evidence\n\n- claim (source)\n", encoding="utf-8")
        session_store.log_session(self.child / "state.db", workspace=str(self.child), title="auth work", body="did")

    def absorb(self):
        plan = ab.plan_absorb(self.main, self.child_folder)
        self.assertTrue(plan.ok, plan.blockers)
        return ab.apply_absorb(self.main, plan)


class MapRows(Platform):
    def _unbuilt(self) -> list[str]:
        findings = drift.check_children(self.main, resolve_children(self.main))
        return [str(f.get("id")) for f in findings if f.get("kind") == "unbuilt-row"]

    def test_an_absorbed_row_is_not_reported_unbuilt(self) -> None:
        """It is being built - here. Reporting it unbuilt would never stop."""
        self.absorb()
        self.assertEqual([i for i in self._unbuilt() if "row-01" in i], [])

    def test_a_row_with_neither_scope_nor_workspace_is_still_reported(self) -> None:
        self.absorb()
        self.assertEqual(self._unbuilt(), ["unbuilt-row:portal:row-02"])

    def test_the_absorbed_child_is_unlinked_so_it_is_not_reported_missing(self) -> None:
        """Three permanent `missing-link` errors on the real platform, every session."""
        from workspace_tree import link

        link(self.main, self.child_folder)
        self.assertTrue(read_meta(self.main).get("children"))
        self.absorb()
        names = [c.get("name") for c in read_meta(self.main).get("children") or []]
        self.assertNotIn("auth-service", names)
        kinds = [f.get("kind") for f in drift.check_children(self.main, resolve_children(self.main))]
        self.assertNotIn("missing-link", kinds)


class TreeOutput(Platform):
    def test_a_unified_workspace_does_not_report_itself_as_having_no_sub_products(self) -> None:
        self.absorb()
        text = describe_tree(self.main)
        self.assertIn("scopes: 1", text)
        self.assertIn("auth-service", text)
        self.assertNotIn("standalone - no parent or sub-product workspaces detected", text)

    def test_a_federated_workspace_output_is_unchanged(self) -> None:
        text = describe_tree(self.main)
        self.assertIn("sub-products: 1", text)
        self.assertNotIn("scopes:", text)


class ScopeDecisionsAreNotPlatformPolicy(Platform):
    """Absorbing one sub-product must not publish its decisions to the others.

    Measured on a real platform: absorbing one sub-product took drift from 10 findings
    to 31 - thirty `parent-added`, fifteen per remaining sub-product, announcing another
    product's form-drafting and repo-layout decisions as new platform policy.
    """

    def _second_child(self) -> Path:
        folder = self.product / "portal"
        ws = folder / ".loop-engineer"
        (ws / "plan").mkdir(parents=True)
        (ws / "plan" / "main_plan.md").write_text("# Portal\n", encoding="utf-8")
        (ws / "memories").mkdir()
        (ws / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
        (ws / "DECISIONS.md").write_text("# Decisions\n\n| Topic | Decision |\n|---|---|\n| Router | Next.js |\n", encoding="utf-8")
        return folder

    def test_absorbed_decisions_stay_out_of_the_platform_surface(self) -> None:
        self._second_child()
        self.absorb()
        surface = drift.decisions_labels(self.main)
        self.assertIn("datastore", {k.lower() for k in surface}, "the platform's own must stay")
        self.assertNotIn("token format", {k.lower() for k in surface}, "the scope's must not")

    def test_the_heading_alone_is_enough_when_the_marker_is_compacted_away(self) -> None:
        """`loop archive` rebuilds DECISIONS.md entries and drops bare HTML comments."""
        self._second_child()
        self.absorb()
        path = self.main / "DECISIONS.md"
        path.write_text(path.read_text(encoding="utf-8").replace("<!-- absorbed:auth-service -->", ""), encoding="utf-8")
        surface = drift.decisions_labels(self.main)
        self.assertNotIn("token format", {k.lower() for k in surface})

    def test_recorded_keys_cover_the_case_where_both_are_gone(self) -> None:
        self._second_child()
        self.absorb()
        scope = sp.find_scope(self.main, "auth-service")
        self.assertIn("token-format", scope.decision_keys)
        path = self.main / "DECISIONS.md"
        text = path.read_text(encoding="utf-8")
        text = text.replace("<!-- absorbed:auth-service -->", "")
        text = text.replace("## Decisions from sub-product `auth-service` (absorbed", "## Notes (")
        path.write_text(text, encoding="utf-8")
        surface = drift.decisions_labels(self.main)
        self.assertNotIn("token format", {k.lower() for k in surface})
        self.assertIn("datastore", {k.lower() for k in surface})

    def test_a_platform_topic_repeated_by_a_scope_is_not_dropped(self) -> None:
        """Excluding by key alone would delete a real platform decision."""
        (self.child / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | Postgres |\n", encoding="utf-8"
        )
        self.absorb()
        self.assertIn("datastore", {k.lower() for k in drift.decisions_labels(self.main)})

    def test_absorbing_a_second_sub_product_does_not_conflict_with_the_first(self) -> None:
        """Two sub-products deciding their own separate business is not a conflict."""
        portal = self._second_child()
        self.absorb()
        (portal / ".loop-engineer" / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Token format | Opaque tokens |\n", encoding="utf-8"
        )
        plan = ab.plan_absorb(self.main, portal, map_id="02")
        self.assertEqual(plan.decision_conflicts, [], "the first scope's decisions are not the platform's")
