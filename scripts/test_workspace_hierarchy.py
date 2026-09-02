"""Tests for the main-product / sub-product hierarchy.

Covers discovery, linking, parent resolution, drift checks, guarded cross-workspace
staged writes, and - most importantly - that a standalone workspace behaves exactly
as it did before this feature existed.

Stdlib unittest, no live network.

Run: python scripts/test_workspace_hierarchy.py
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import hierarchy_drift as drift
import pending_writes as pw
import workspace_tree as wt


MAIN_PLAN = """# Main Plan

- **Name:** Platform

## Deployment & Infrastructure

| Item | Choice |
|------|--------|
| Cloud provider | AWS |
| LLM provider | provider-a |
| Primary region(s) | TBD |
"""

PRODUCT_MAP = """# Product Map

| ID | Step file | Type | Title | Depends on | Ultraplan status |
|----|-----------|------|-------|------------|------------------|
| 01 | step_01 | service | auth svc | | outline |
| 02 | step_02 | sub-product | portal | 01 | outline |
| 03 | step_03 | module | billing | | outline |
"""


class TreeSandbox(unittest.TestCase):
    """A temp tree with a main product folder, isolated from the real LOOP home."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-hierarchy-test-"))
        self._prev = os.environ.get("LOOP_ENGINEER_HOME")
        os.environ["LOOP_ENGINEER_HOME"] = str(self.tmp / "home")
        self.main = self.tmp / "main"
        self.main_ws = self.seed(self.main)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LOOP_ENGINEER_HOME", None)
        else:
            os.environ["LOOP_ENGINEER_HOME"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)

    def seed(self, folder: Path, **files: str) -> Path:
        ws = folder / ".loop-engineer"
        (ws / "memories").mkdir(parents=True, exist_ok=True)
        (ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        for rel, body in files.items():
            path = ws / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return ws


class TestScanChildren(TreeSandbox):
    def test_finds_direct_children(self) -> None:
        self.seed(self.main / "auth-svc")
        self.seed(self.main / "portal")
        found = {p.name for p in wt.scan_children(self.main)}
        self.assertEqual(found, {"auth-svc", "portal"})

    def test_skips_build_dirs_and_hidden_dirs(self) -> None:
        self.seed(self.main / "node_modules" / "pkg")
        self.seed(self.main / ".cache" / "thing")
        self.seed(self.main / "dist" / "bundle")
        self.assertEqual(wt.scan_children(self.main), [])

    def test_does_not_descend_into_a_discovered_sub_product(self) -> None:
        """A sub-product's own children belong to it, not to the main product."""
        self.seed(self.main / "auth-svc")
        self.seed(self.main / "auth-svc" / "inner")
        found = {p.name for p in wt.scan_children(self.main)}
        self.assertEqual(found, {"auth-svc"})

    def test_honors_max_depth(self) -> None:
        self.seed(self.main / "a" / "b" / "c" / "deep")
        self.assertEqual(wt.scan_children(self.main, max_depth=3), [])
        self.assertEqual(len(wt.scan_children(self.main, max_depth=4)), 1)


class TestRoles(TreeSandbox):
    def test_no_children_no_parent_is_standalone(self) -> None:
        tree = wt.refresh(self.main_ws)
        self.assertEqual(tree["role"], wt.ROLE_STANDALONE)
        self.assertEqual(tree["children"], [])
        self.assertIsNone(tree["parent"])

    def test_children_promote_to_main(self) -> None:
        self.seed(self.main / "auth-svc")
        tree = wt.refresh(self.main_ws)
        self.assertEqual(tree["role"], wt.ROLE_MAIN)
        self.assertEqual([c["name"] for c in tree["children"]], ["auth-svc"])

    def test_child_resolves_parent_and_becomes_sub(self) -> None:
        child_ws = self.seed(self.main / "auth-svc")
        wt.refresh(self.main_ws)
        tree = wt.refresh(child_ws)
        self.assertEqual(tree["role"], wt.ROLE_SUB)
        self.assertEqual(tree["parent"]["name"], "main")

    def test_pinned_standalone_survives_a_scan(self) -> None:
        self.seed(self.main / "auth-svc")
        wt.set_role(self.main_ws, wt.ROLE_STANDALONE, pinned=True)
        tree = wt.refresh(self.main_ws)
        self.assertEqual(tree["role"], wt.ROLE_STANDALONE)
        self.assertEqual(tree["children"], [])

    def test_middle_node_keeps_both_links(self) -> None:
        mid_ws = self.seed(self.main / "auth-svc")
        self.seed(self.main / "auth-svc" / "token-api")
        wt.refresh(self.main_ws)
        tree = wt.refresh(mid_ws)
        self.assertEqual(tree["role"], wt.ROLE_MAIN)
        self.assertIsNotNone(tree["parent"])
        self.assertEqual([c["name"] for c in tree["children"]], ["token-api"])

    def test_refresh_is_idempotent(self) -> None:
        self.seed(self.main / "auth-svc")
        first = wt.refresh(self.main_ws)
        second = wt.refresh(self.main_ws)
        self.assertEqual(
            [c["path"] for c in first["children"]], [c["path"] for c in second["children"]]
        )

    def test_malformed_meta_does_not_raise(self) -> None:
        path = wt.meta_path(self.main_ws)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not json", encoding="utf-8")
        self.assertEqual(wt.read_meta(self.main_ws), {})
        self.assertEqual(wt.refresh(self.main_ws)["role"], wt.ROLE_STANDALONE)


class TestLinking(TreeSandbox):
    def test_link_outside_folder_round_trip(self) -> None:
        outside = self.tmp / "billing"
        self.seed(outside)
        entry = wt.link(self.main_ws, outside)
        self.assertEqual(entry["name"], "billing")
        self.assertEqual(entry["source"], "link")

        tree = wt.refresh(self.main_ws)
        self.assertIn("billing", [c["name"] for c in tree["children"]])
        self.assertEqual(wt.get_role(wt.data_dir_for(outside)), wt.ROLE_SUB)

        self.assertTrue(wt.unlink(self.main_ws, "billing"))
        tree = wt.refresh(self.main_ws)
        self.assertNotIn("billing", [c["name"] for c in tree["children"]])

    def test_link_requires_loop_data(self) -> None:
        plain = self.tmp / "not-a-workspace"
        plain.mkdir()
        with self.assertRaises(SystemExit):
            wt.link(self.main_ws, plain)

    def test_link_rejects_self(self) -> None:
        with self.assertRaises(SystemExit):
            wt.link(self.main_ws, self.main)

    def test_missing_linked_folder_is_flagged_not_dropped(self) -> None:
        outside = self.tmp / "billing"
        self.seed(outside)
        wt.link(self.main_ws, outside)
        shutil.rmtree(outside)
        children = wt.resolve_children(self.main_ws)
        self.assertEqual(len(children), 1)
        self.assertTrue(children[0]["missing"])

    def test_parent_that_does_not_list_child_is_rejected(self) -> None:
        """The link must never be one-way: an ancestor too deep to scan is not a parent."""
        deep_ws = self.seed(self.main / "a" / "b" / "c" / "deep")
        wt.refresh(self.main_ws)
        self.assertIsNone(wt.resolve_parent(deep_ws))

    def test_map_id_binds_by_folder_name(self) -> None:
        self.seed(self.main / "auth-svc")
        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(PRODUCT_MAP, encoding="utf-8")
        tree = wt.refresh(self.main_ws)
        self.assertEqual(tree["children"][0]["map_id"], "01")


class TestGlobalWorkspace(TreeSandbox):
    def test_global_data_home_has_no_hierarchy(self) -> None:
        from loop_home import global_data_home

        home = global_data_home()
        (home / "memories").mkdir(parents=True, exist_ok=True)
        (home / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        tree = wt.refresh(home)
        self.assertFalse(tree["enabled"])
        self.assertEqual(tree["role"], wt.ROLE_STANDALONE)


class TestPendingFileWrites(TreeSandbox):
    def test_rejects_traversal(self) -> None:
        for bad in ("../escape.md", "plan/../../x.md", "/abs/path.md"):
            with self.assertRaises(ValueError):
                pw.stage_file_write(
                    self.main_ws, relative_path=bad, action="append", content="x", reason="r"
                )

    def test_rejects_non_allowlisted_target(self) -> None:
        for bad in ("src/app.py", "state.db", "memories/MEMORY.md"):
            with self.assertRaises(ValueError):
                pw.stage_file_write(
                    self.main_ws, relative_path=bad, action="append", content="x", reason="r"
                )

    def test_allows_allowlisted_and_plan_paths(self) -> None:
        self.assertIsNotNone(
            pw.stage_file_write(self.main_ws, relative_path="DOUBTS.md", action="append", content="a", reason="r")
        )
        self.assertIsNotNone(
            pw.stage_file_write(self.main_ws, relative_path="plan/NOTES.md", action="append", content="b", reason="r")
        )

    def test_same_finding_stages_only_once(self) -> None:
        origin = {"finding_id": "decision-conflict:auth-svc:datastore"}
        first = pw.stage_file_write(
            self.main_ws, relative_path="DOUBTS.md", action="append", content="x", reason="r", origin=origin
        )
        second = pw.stage_file_write(
            self.main_ws, relative_path="DOUBTS.md", action="append", content="x", reason="r", origin=origin
        )
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(pw.list_pending(self.main_ws)), 1)

    def test_approve_appends_and_clears(self) -> None:
        (self.main_ws / "DOUBTS.md").write_text("# Doubts\n\n- existing\n", encoding="utf-8")
        pw.stage_file_write(
            self.main_ws, relative_path="DOUBTS.md", action="append", content="- new note", reason="r"
        )
        results = pw.approve_pending(self.main_ws, approve_all=True)
        self.assertEqual(len(results), 1)
        text = (self.main_ws / "DOUBTS.md").read_text(encoding="utf-8")
        self.assertIn("- existing", text)
        self.assertIn("- new note", text)
        self.assertEqual(pw.list_pending(self.main_ws), [])

    def test_approve_rechecks_the_guard(self) -> None:
        """A hand-edited pending file cannot widen the allowlist."""
        import json

        pw.pending_files_dir(self.main_ws).mkdir(parents=True, exist_ok=True)
        (pw.pending_files_dir(self.main_ws) / "evil.json").write_text(
            json.dumps(
                {
                    "id": "evil",
                    "relative_path": "../../escaped.md",
                    "action": "replace",
                    "content": "pwned",
                    "reason": "hand-edited",
                    "status": "pending",
                }
            ),
            encoding="utf-8",
        )
        results = pw.approve_pending(self.main_ws, approve_all=True)
        self.assertTrue(any("rejected" in r for r in results))
        self.assertFalse((self.tmp / "escaped.md").exists())
        self.assertFalse((self.main.parent / "escaped.md").exists())


class TestDoctorHierarchyHealth(TreeSandbox):
    def _check(self, workspace: Path) -> tuple[list[str], list[str], list[str]]:
        import doctor

        errors: list[str] = []
        warnings: list[str] = []
        passes: list[str] = []
        doctor.check_hierarchy_health(workspace, errors, warnings, passes)
        return errors, warnings, passes

    def test_standalone_reports_nothing(self) -> None:
        errors, warnings, passes = self._check(self.main_ws)
        self.assertEqual((errors, warnings, passes), ([], [], []))

    def test_two_way_link_is_healthy(self) -> None:
        outside = self.tmp / "billing"
        billing_ws = self.seed(outside)
        wt.link(self.main_ws, outside)
        wt.refresh(self.main_ws)
        wt.refresh(billing_ws)
        errors, _warnings, passes = self._check(billing_ws)
        self.assertEqual(errors, [])
        self.assertTrue(any("Hierarchy link healthy" in p for p in passes))

    def test_one_way_link_warns(self) -> None:
        """The parent forgot a linked sub-product that still points up at it."""
        outside = self.tmp / "billing"
        billing_ws = self.seed(outside)
        wt.link(self.main_ws, outside)
        wt.refresh(billing_ws)
        wt.unlink(self.main_ws, "billing")
        _errors, warnings, _passes = self._check(billing_ws)
        self.assertTrue(any("one-way" in w for w in warnings))

    def test_missing_child_folder_is_an_error(self) -> None:
        outside = self.tmp / "billing"
        self.seed(outside)
        wt.link(self.main_ws, outside)
        shutil.rmtree(outside)
        errors, _warnings, _passes = self._check(self.main_ws)
        self.assertTrue(any("missing" in e for e in errors))


class TestPlanPhase(TreeSandbox):
    def test_no_hierarchy_phase_without_errors(self) -> None:
        from plan_phase import compute_plan_phase

        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "main_plan.md").write_text(MAIN_PLAN, encoding="utf-8")
        self.assertNotEqual(compute_plan_phase(self.main_ws)["phase"], "hierarchy")


class TestMapParsing(TreeSandbox):
    """The map is read by column name, because real maps grow columns and tables."""

    def _map(self, body: str) -> list[dict]:
        from ultraplan_harness import parse_product_map

        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(body, encoding="utf-8")
        return parse_product_map(self.main_ws)

    def test_extra_column_does_not_shift_fields(self) -> None:
        """A `Founder rank` column between ID and Step file must change nothing."""
        rows = self._map(
            "# Product Map\n\n"
            "| ID | Founder rank | Step file | Type | Title | Scope | Depends on | Status |\n"
            "|----|---|---|---|---|---|---|---|\n"
            "| 01 | #1 | step_01 | sub-product | Denial Recovery Engine | engine loops | | Built |\n"
        )
        self.assertEqual(1, len(rows))
        self.assertEqual("sub-product", rows[0]["type"])
        self.assertEqual("Denial Recovery Engine", rows[0]["title"])
        self.assertEqual("", rows[0]["depends"])

    def test_two_tables_in_one_id_space(self) -> None:
        rows = self._map(
            "# Product Map\n\n## A. Programs\n\n"
            "| ID | Step file | Type | Title | Depends on | Status |\n"
            "|----|---|---|---|---|---|\n"
            "| 02 | step_02 | program | Revenue Activation | 01 | active |\n"
            "\n## B. Modules\n\n"
            "| ID | Founder rank | Step file | Type | Title | Depends on | Status |\n"
            "|----|---|---|---|---|---|---|\n"
            "| 01 | #1 | step_01 | sub-product | auth svc | | built |\n"
        )
        self.assertEqual({"01": "auth svc", "02": "Revenue Activation"}, {r["id"]: r["title"] for r in rows})

    def test_non_map_tables_are_skipped(self) -> None:
        """A path index also starts with `ID` - without a Title it is not a map."""
        rows = self._map(
            "# Product Map\n\n"
            "| ID | Step file | Type | Title | Depends on | Status |\n"
            "|----|---|---|---|---|---|\n"
            "| 01 | step_01 | sub-product | auth svc | | outline |\n"
            "\n## Canonical paths\n\n"
            "| ID | Index file | Ultraplan pack |\n|----|---|---|\n"
            "| 01 | `plan/step_01.md` | `plan/steps/01-auth/` |\n"
        )
        self.assertEqual(["01"], [r["id"] for r in rows])
        self.assertEqual("auth svc", rows[0]["title"])

    def test_header_less_table_keeps_legacy_column_order(self) -> None:
        rows = self._map("# Product Map\n\n| 01 | step_01 | service | auth svc | | outline |\n")
        self.assertEqual("auth svc", rows[0]["title"])


class TestMapBinding(TreeSandbox):
    def _bind(self, folder_name: str, map_body: str) -> str | None:
        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(map_body, encoding="utf-8")
        self.seed(self.main / folder_name)
        return wt.refresh(self.main_ws)["children"][0]["map_id"]

    MAP = (
        "# Product Map\n\n| ID | Step file | Type | Title | Depends on | Status |\n"
        "|----|---|---|---|---|---|\n"
        "| 01 | step_01 | sub-product | api gateway | | outline |\n"
        "| 02 | step_02 | sub-product | public api | | outline |\n"
    )

    def test_partial_name_never_binds(self) -> None:
        """`api` is a prefix of two rows - guessing one would be a silent mis-bind."""
        self.assertIsNone(self._bind("api", self.MAP))

    def test_exact_title_binds(self) -> None:
        self.assertEqual("02", self._bind("public-api", self.MAP))

    def test_workspace_column_binds_when_folder_name_differs(self) -> None:
        bound = self._bind(
            "gateway",
            "# Product Map\n\n| ID | Step file | Type | Title | Workspace | Status |\n"
            "|----|---|---|---|---|---|\n"
            "| 01 | step_01 | sub-product | api gateway | gateway | outline |\n",
        )
        self.assertEqual("01", bound)


class QualifiedDecisionBullets(unittest.TestCase):
    """An ADR that settles several things qualifies each bullet.

    `- **Decision - Cognito is authentication only.**` matched nothing, so the whole
    section yielded no value and never crossed into a sub-product. On the real main
    product that silently withheld "keep authorization wholly in Postgres" and the
    row-level-security requirement from two sub-products, which then built on SQLite.
    """

    ADR = (
        "## D-018: Account model" + chr(10) + chr(10)
        + "- **Decision - the model:** organization then facility then user." + chr(10)
        + "- **Decision - Cognito is authentication only.** Keep authorization in Postgres." + chr(10)
        + "- **Decision - tenant isolation gets a second layer.** Add row-level security." + chr(10)
        + "- **Rationale:** boilerplate that must never be harvested." + chr(10)
    )

    def entries(self):
        return drift.decision_entries(self.ADR)

    def test_every_qualified_bullet_becomes_its_own_decision(self) -> None:
        self.assertEqual(3, len(self.entries()))

    def test_the_datastore_call_survives_the_crossing(self) -> None:
        values = " ".join(value for _label, value in self.entries().values())
        self.assertIn("Postgres", values)
        self.assertIn("row-level security", values)

    def test_a_bare_decision_bullet_still_works(self) -> None:
        text = "## D-007: Datastore" + chr(10) + chr(10) + "- **Decision:** Postgres." + chr(10)
        entries = drift.decision_entries(text)
        self.assertEqual(1, len(entries))
        self.assertIn("Postgres", next(iter(entries.values()))[1])

    def test_adr_boilerplate_is_still_never_harvested(self) -> None:
        """The reason bare bullets are not harvested: every ADR repeats these."""
        labels = " ".join(label for label, _v in self.entries().values()).lower()
        self.assertNotIn("rationale", labels)


if __name__ == "__main__":
    unittest.main()


class PlatformPlanningLoop(unittest.TestCase):
    """ultraplan one step -> spec -> clarify -> checklist -> doubts -> tasks -> next step.

    Packing used to outrank an active feature, so on a multi-row platform the router
    pulled every session back to `ultraplan` until every pack existed: the spec just
    written sat untouched and `spec-clarify`, `resolve-doubts` and `task-compiler` were
    unreachable.
    """

    BODY = (
        "Substantive content describing the design, its constraints and the decisions "
        "taken, long enough to count as real work rather than a template heading.\n"
    )

    def setUp(self) -> None:
        import tempfile as _t
        self.root = Path(_t.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.ws = self.root / "P" / ".loop-engineer"
        (self.ws / "plan" / "steps").mkdir(parents=True)
        (self.ws / "memories").mkdir()
        (self.ws / ".loop").mkdir()
        (self.ws / "memories" / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
        (self.ws / "plan" / "main_plan.md").write_text("# Product\n\nreal plan\n", encoding="utf-8")
        (self.ws / "plan" / "PLAN_SCALE.md").write_text("scale: platform\n", encoding="utf-8")
        (self.ws / "plan" / "PRODUCT_MAP.md").write_text(
            "| ID | Type | Title | Depends on |\n|---|---|---|---|\n"
            "| 01 | module | Core |  |\n| 02 | module | Reports | 01 |\n", encoding="utf-8")
        self.feature = self.ws / "plan" / "features" / "001-core"

    def pack(self, step_id: str, title: str) -> None:
        from plan_paths import ULTRAPLAN_ARTIFACTS, step_ultraplan_dir
        folder = step_ultraplan_dir(self.ws, step_id, title)
        folder.mkdir(parents=True, exist_ok=True)
        for artifact in ULTRAPLAN_ARTIFACTS:
            (folder / f"{artifact}.md").write_text(f"# {artifact}\n\n{self.BODY}", encoding="utf-8")

    def activate_feature(self) -> None:
        self.feature.mkdir(parents=True, exist_ok=True)
        (self.feature / "spec.md").write_text("# Core\n\n## Open questions\n\n- what SLA?\n", encoding="utf-8")
        (self.ws / ".loop" / "active-feature.json").write_text(
            json.dumps({"id": "001", "title": "Core", "path": "plan/features/001-core"}), encoding="utf-8")

    def phase(self) -> str:
        import plan_phase
        return plan_phase.compute_plan_phase(self.ws)["phase"]

    def ready_checklist(self) -> None:
        (self.feature / "spec-checklist.md").write_text(
            "# Checklist\n\nVerdict: **Ready for feature-plan**\n", encoding="utf-8")

    def test_a_packed_step_with_an_open_spec_goes_to_spec_clarify(self) -> None:
        self.pack("01", "Core")
        self.activate_feature()
        self.assertEqual(self.phase(), "spec-clarify")

    def test_an_open_blocking_doubt_outranks_packing_the_next_row(self) -> None:
        self.pack("01", "Core")
        self.activate_feature()
        self.ready_checklist()
        (self.ws / "DOUBTS.md").write_text(
            "# Doubts\n\n## DQ-001: blocking\n- **Blocking:** yes\n", encoding="utf-8")
        self.assertEqual(self.phase(), "resolve-doubts")

    def test_a_finished_feature_returns_the_loop_to_the_next_pack(self) -> None:
        self.pack("01", "Core")
        self.activate_feature()
        self.ready_checklist()
        self.assertEqual(self.phase(), "ultraplan", "row 02 still needs its pack")

    def test_tasks_compile_once_every_row_is_packed(self) -> None:
        self.pack("01", "Core")
        self.pack("02", "Reports")
        self.activate_feature()
        self.ready_checklist()
        self.assertEqual(self.phase(), "task-compiler")

    def test_a_platform_with_no_feature_still_packs_first(self) -> None:
        self.assertEqual(self.phase(), "ultraplan")
