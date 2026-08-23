"""Tests for the main-product / sub-product hierarchy.

Covers discovery, linking, parent resolution, drift checks, guarded cross-workspace
staged writes, and - most importantly - that a standalone workspace behaves exactly
as it did before this feature existed.

Stdlib unittest, no live network.

Run: python scripts/test_workspace_hierarchy.py
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import hierarchy_drift as drift
import hierarchy_sync
import pending_writes as pw
import workspace_tree as wt


MAIN_PLAN = """# Main Plan

- **Name:** Platform

## Deployment & Infrastructure

| Item | Choice |
|------|--------|
| Cloud provider | AWS |
| LLM provider | Anthropic |
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


class TestDriftChecks(TreeSandbox):
    def setUp(self) -> None:
        super().setUp()
        self.main_ws = self.seed(
            self.main,
            **{
                "plan/main_plan.md": MAIN_PLAN,
                "plan/PRODUCT_MAP.md": PRODUCT_MAP,
                "DECISIONS.md": "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | DynamoDB |\n",
            },
        )

    def _children(self) -> list[dict]:
        return wt.refresh(self.main_ws)["children"]

    def _kinds(self, findings: list[dict]) -> set[str]:
        return {f["kind"] for f in findings}

    def test_aligned_sub_product_has_no_findings(self) -> None:
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n\n- **Name:** Auth\n\n## Deployment & Infrastructure\n\n"
                "| Item | Choice |\n|---|---|\n| Cloud provider | AWS |\n",
                "DECISIONS.md": "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | DynamoDB |\n",
            },
        )
        findings = drift.check_children(self.main_ws, self._children())
        self.assertNotIn("decision-conflict", self._kinds(findings))
        self.assertNotIn("deployment-conflict", self._kinds(findings))

    def test_deployment_conflict(self) -> None:
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n\n## Deployment & Infrastructure\n\n"
                "| Item | Choice |\n|---|---|\n| Cloud provider | GCP |\n"
            },
        )
        findings = drift.check_children(self.main_ws, self._children())
        conflict = next(f for f in findings if f["kind"] == "deployment-conflict")
        self.assertEqual(conflict["level"], drift.LEVEL_ERROR)
        self.assertIn("AWS", conflict["detail"])
        self.assertIn("GCP", conflict["detail"])

    def test_decision_conflict(self) -> None:
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Auth\n",
                "DECISIONS.md": "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | Postgres |\n",
            },
        )
        self.assertIn("decision-conflict", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_placeholder_values_never_conflict(self) -> None:
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n\n## Deployment & Infrastructure\n\n"
                "| Item | Choice |\n|---|---|\n| Primary region(s) | us-east-1 |\n"
            },
        )
        findings = drift.check_children(self.main_ws, self._children())
        self.assertNotIn("deployment-conflict", self._kinds(findings))

    def test_pending_decisions_section_is_ignored(self) -> None:
        (self.main_ws / "DECISIONS.md").write_text(
            "# Decisions\n\n## Pending decisions\n\n| Topic | Options | Blocker |\n|---|---|---|\n"
            "| Datastore | a vs b | User |\n",
            encoding="utf-8",
        )
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Auth\n",
                "DECISIONS.md": "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | Postgres |\n",
            },
        )
        self.assertNotIn("decision-conflict", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_unmapped_sub_product(self) -> None:
        self.seed(self.main / "surprise", **{"plan/main_plan.md": "# Plan\n- **Name:** Surprise\n"})
        findings = drift.check_children(self.main_ws, self._children())
        self.assertIn("unmapped-sub", self._kinds(findings))

    def test_unbuilt_map_row(self) -> None:
        """Only a row that declares delegation can be missing a workspace.

        `billing` is typed `module` - planned and built inside this workspace - so
        it is not unbuilt, it is simply not delegated.
        """
        self.seed(self.main / "auth-svc", **{"plan/main_plan.md": "# Plan\n- **Name:** Auth\n"})
        findings = drift.check_children(self.main_ws, self._children())
        unbuilt = [f for f in findings if f["kind"] == "unbuilt-row"]
        self.assertEqual({f["sub"] for f in unbuilt}, {"portal"})

    def _map(self, *rows: str) -> None:
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(
            "# Product Map\n\n\n\n| ID | Step file | Type | Title | Depends on | Status |\n"
            "|----|---|---|---|---|---|\n" + "".join(rows),
            encoding="utf-8",
        )

    def _unbuilt(self) -> list[str]:
        findings = drift.check_children(self.main_ws, self._children())
        return [f["sub"] for f in findings if f["kind"] == "unbuilt-row"]

    def _auth(self) -> None:
        self.seed(self.main / "auth-svc", **{"plan/main_plan.md": "# Plan\n- **Name:** Auth\n"})

    ROW_AUTH = "| 01 | step_01 | sub-product | auth svc | | outline |\n"

    def test_a_deferred_row_is_not_yet_a_missing_workspace(self) -> None:
        """Typing a row `sub-product` says where the work will live, not that it starts now.

        A real map had 12 of 14 delegated rows `Deferred`; warning about each one every
        session buried the single row that had actually gone active.
        """
        self._map(self.ROW_AUTH, "| 02 | step_02 | sub-product | portal | | Deferred - lowest priority |\n")
        self._auth()
        self.assertEqual([], self._unbuilt())

    def test_the_same_row_reports_the_session_it_goes_active(self) -> None:
        self._map(self.ROW_AUTH, "| 02 | step_02 | sub-product | portal | | **ACTIVE (track C)** |\n")
        self._auth()
        self.assertEqual(["portal"], self._unbuilt())

    def test_planned_still_counts_as_dormant(self) -> None:
        self._map(self.ROW_AUTH, "| 02 | step_02 | sub-product | portal | | PLANNED - ranked ahead of row 10 |\n")
        self._auth()
        self.assertEqual([], self._unbuilt())

    def test_a_row_with_no_status_still_reports(self) -> None:
        """Unknown is not the same as dormant - the cautious default is to say something."""
        self._map(self.ROW_AUTH, "| 02 | step_02 | sub-product | portal | | |\n")
        self._auth()
        self.assertEqual(["portal"], self._unbuilt())

    def test_a_dormant_row_that_has_a_workspace_is_never_reported(self) -> None:
        self._map("| 01 | step_01 | sub-product | auth svc | | Deferred |\n")
        self._auth()
        self.assertEqual([], self._unbuilt())

    def test_module_and_program_rows_are_never_unbuilt(self) -> None:
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(
            "# Product Map\n\n| ID | Step file | Type | Title | Depends on | Status |\n"
            "|----|---|---|---|---|---|\n"
            "| 01 | step_01 | sub-product | auth svc | | outline |\n"
            "| 02 | step_02 | program | Revenue Activation | | active |\n"
            "| 03 | step_03 | module | billing | | outline |\n",
            encoding="utf-8",
        )
        self.seed(self.main / "auth-svc", **{"plan/main_plan.md": "# Plan\n- **Name:** Auth\n"})
        findings = drift.check_children(self.main_ws, self._children())
        self.assertEqual([], [f for f in findings if f["kind"] == "unbuilt-row"])

    def test_decisions_past_40k_are_still_parsed(self) -> None:
        """A real DECISIONS.md hit 63,074 chars and 23 of 41 keys fell past the cut.

        The parent watermark then saw them vanish and told the sub-product 16
        decisions had been removed while they were still sitting in the file.
        """
        padding = "\n".join(f"<!-- filler line {i} to push the table past the old cap -->" for i in range(1200))
        (self.main_ws / "DECISIONS.md").write_text(
            "# Decision Log\n\n## Context\n\n" + padding
            + "\n\n## Inherited decisions\n\n| Decision | Status |\n|---|---|\n| Datastore | Postgres |\n",
            encoding="utf-8",
        )
        self.assertGreater(len((self.main_ws / "DECISIONS.md").read_text(encoding="utf-8")), 40_000)
        self.assertIn("datastore", drift.decisions_labels(self.main_ws))

    def test_body_tables_are_not_harvested_as_decisions(self) -> None:
        """An ICP segmentation grid inside one decision turned into four decisions."""
        (self.main_ws / "DECISIONS.md").write_text(
            "# Decision Log\n\n## D-M-009: Who we sell to\n"
            "- **Decision:** Volume clinics first.\n\n"
            "| Segment | Volume |\n|---|---|\n| Dental | 3-4 dentists |\n| Dermatology | 2-3 providers |\n\n"
            "## Inherited decisions\n\n| Decision | Status |\n|---|---|\n| Datastore | Postgres |\n",
            encoding="utf-8",
        )
        labels = drift.decisions_labels(self.main_ws)
        self.assertIn("datastore", labels, "the declared decision table must be read")
        self.assertNotIn("dental", labels)
        self.assertNotIn("dermatology", labels)

    def test_adr_formatted_logs_do_not_collide_on_boilerplate(self) -> None:
        """Two ADR logs share field names, not decisions - that is not a conflict."""
        adr = (
            "# Decision Log\n\n## {id}: {topic}\n"
            "- **Date:** {date}\n"
            "- **Decision:** {decision}\n"
            "- **Rationale:** because of {date}\n"
            "- **Consequences:** downstream work\n"
        )
        (self.main_ws / "DECISIONS.md").write_text(
            adr.format(id="D-M-001", topic="Pricing model", date="2026-08-10", decision="Flat fee only"),
            encoding="utf-8",
        )
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Auth\n",
                "DECISIONS.md": adr.format(
                    id="D-001", topic="Token lifetime", date="2026-07-01", decision="15 minutes"
                ),
            },
        )
        self.assertNotIn("decision-conflict", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_same_adr_topic_decided_differently_is_a_conflict(self) -> None:
        """The ID prefix differs per workspace, so the topic alone is the key."""
        adr = "# Decision Log\n\n## {id}: Datastore\n- **Date:** {date}\n- **Decision:** {decision}\n"
        (self.main_ws / "DECISIONS.md").write_text(
            adr.format(id="D-M-004", date="2026-08-10", decision="Postgres"), encoding="utf-8"
        )
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Auth\n",
                "DECISIONS.md": adr.format(id="D-002", date="2026-07-01", decision="DynamoDB"),
            },
        )
        findings = [f for f in drift.check_children(self.main_ws, self._children()) if f["kind"] == "decision-conflict"]
        self.assertEqual(1, len(findings))
        self.assertIn("Postgres", findings[0]["detail"])
        self.assertIn("DynamoDB", findings[0]["detail"])

    def test_uninitialized_sub_product(self) -> None:
        self.seed(self.main / "auth-svc", **{"plan/main_plan.md": "# Plan\n\nStatus: **UNINITIALIZED**\n"})
        self.assertIn("uninitialized-sub", self._kinds(drift.check_children(self.main_ws, self._children())))

    LEDGER = "integrations:\n  - counterparty: {ref}\n    status: {status}\n    contract: {detail}\n"

    def test_dependency_gap_when_nothing_is_declared(self) -> None:
        self.seed(
            self.main / "portal",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Portal\n",
                "plan/INTEGRATIONS.yml": "integrations:\n",
            },
        )
        findings = drift.check_children(self.main_ws, self._children())
        gap = next(f for f in findings if f["kind"] == "dependency-gap")
        self.assertIn("auth svc", gap["detail"])

    def test_dependency_satisfied_when_the_ledger_declares_it(self) -> None:
        self.seed(
            self.main / "portal",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Portal\n",
                "plan/INTEGRATIONS.yml": self.LEDGER.format(ref="01", status="planned", detail="REST /token v1"),
            },
        )
        self.assertNotIn("dependency-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_prose_alone_no_longer_satisfies_a_dependency(self) -> None:
        """Naming a module in passing is not the same as planning the integration."""
        self.seed(
            self.main / "portal",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Portal\n\nCalls the auth svc for tokens.\n",
                "plan/INTEGRATIONS.yml": "integrations:\n",
            },
        )
        self.assertIn("dependency-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_a_declined_dependency_is_recorded_not_reported_as_a_gap(self) -> None:
        """"We deliberately do not integrate with X" is an answer, not a failure."""
        self.seed(
            self.main / "portal",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Portal\n",
                "plan/INTEGRATIONS.yml": self.LEDGER.format(
                    ref="auth svc", status="declined", detail="Tokens come from the edge proxy (D-009)."
                ),
            },
        )
        kinds = self._kinds(drift.check_children(self.main_ws, self._children()))
        self.assertIn("dependency-declined", kinds)
        self.assertNotIn("dependency-gap", kinds)

    def test_parent_context_alone_does_not_satisfy_a_dependency(self) -> None:
        """The harness writes this file; reading it back was self-validation."""
        self.seed(
            self.main / "portal",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Portal\n",
                "plan/PARENT_CONTEXT.md": "# Parent Context\n\n- **Depends on** 01 - auth svc\n",
                "plan/INTEGRATIONS.yml": "integrations:\n",
            },
        )
        self.assertIn("dependency-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_placeholder_depends_produces_no_finding(self) -> None:
        """`—` used to pass via slugify returning the literal word `module`."""
        (self.main_ws / "plan" / "PRODUCT_MAP.md").write_text(
            PRODUCT_MAP.replace("| 02 | step_02 | sub-product | portal | 01 |", "| 02 | step_02 | sub-product | portal | — |"),
            encoding="utf-8",
        )
        self.seed(self.main / "portal", **{"plan/main_plan.md": "# Plan\n- **Name:** Portal\n"})
        kinds = self._kinds(drift.check_children(self.main_ws, self._children()))
        self.assertNotIn("dependency-gap", kinds)
        self.assertNotIn("unverifiable-dependency", kinds)

    def test_no_integration_surface_is_unverifiable_not_a_pass(self) -> None:
        self.seed(self.main / "portal", **{"plan/main_plan.md": "# Plan\n- **Name:** Portal\n"})
        findings = drift.check_children(self.main_ws, self._children())
        item = next(f for f in findings if f["kind"] == "unverifiable-dependency")
        self.assertEqual(drift.LEVEL_INFO, item["level"])
        self.assertIn("INTEGRATIONS.yml", item["note"])

    def _parent_spec(self, body: str) -> None:
        folder = self.main_ws / "plan" / "steps" / "01-auth-svc"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "integrations.md").write_text(body, encoding="utf-8")

    def test_contract_gap_from_the_declared_table(self) -> None:
        self._parent_spec(
            "# Integrations\n\n## Internal platform APIs\n\n"
            "| Step / service | Contract | Version |\n|---|---|---|\n"
            "| 02 | token introspection | v1 |\n"
        )
        self.seed(
            self.main / "auth-svc",
            **{"plan/main_plan.md": "# Plan\n- **Name:** Auth\n", "plan/INTEGRATIONS.yml": "integrations:\n"},
        )
        self.assertIn("contract-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_prose_in_the_parent_spec_declares_nothing(self) -> None:
        """The old check inferred counterparties by substring - two stacked guesses."""
        self._parent_spec("# Integrations\n\nExposes token introspection to the portal.\n")
        self.seed(
            self.main / "auth-svc",
            **{"plan/main_plan.md": "# Plan\n- **Name:** Auth\n", "plan/INTEGRATIONS.yml": "integrations:\n"},
        )
        self.assertNotIn("contract-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_contract_satisfied_when_the_child_declares_it(self) -> None:
        self._parent_spec(
            "# Integrations\n\n## Internal platform APIs\n\n"
            "| Step / service | Contract | Version |\n|---|---|---|\n"
            "| 02 | token introspection | v1 |\n"
        )
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n- **Name:** Auth\n",
                "plan/INTEGRATIONS.yml": self.LEDGER.format(ref="02", status="planned", detail="introspection v1"),
            },
        )
        self.assertNotIn("contract-gap", self._kinds(drift.check_children(self.main_ws, self._children())))

    def test_missing_link_is_an_error(self) -> None:
        outside = self.tmp / "billing"
        self.seed(outside, **{"plan/main_plan.md": "# Plan\n- **Name:** Billing\n"})
        wt.link(self.main_ws, outside)
        shutil.rmtree(outside)
        findings = drift.check_children(self.main_ws, self._children())
        missing = next(f for f in findings if f["kind"] == "missing-link")
        self.assertEqual(missing["level"], drift.LEVEL_ERROR)

    def test_finding_ids_are_stable(self) -> None:
        self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n\n## Deployment & Infrastructure\n\n"
                "| Item | Choice |\n|---|---|\n| Cloud provider | GCP |\n"
            },
        )
        first = {f["id"] for f in drift.check_children(self.main_ws, self._children())}
        second = {f["id"] for f in drift.check_children(self.main_ws, self._children())}
        self.assertEqual(first, second)


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


class TestHierarchySync(TreeSandbox):
    def setUp(self) -> None:
        super().setUp()
        self.main_ws = self.seed(
            self.main,
            **{
                "plan/main_plan.md": MAIN_PLAN,
                "plan/PRODUCT_MAP.md": PRODUCT_MAP,
                "DECISIONS.md": "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | DynamoDB |\n",
            },
        )
        self.child_ws = self.seed(
            self.main / "auth-svc",
            **{
                "plan/main_plan.md": "# Plan\n\n- **Name:** Auth\n\n## Deployment & Infrastructure\n\n"
                "| Item | Choice |\n|---|---|\n| Cloud provider | GCP |\n",
                "DOUBTS.md": "# Doubts\n",
            },
        )

    def test_reports_here_and_the_sub_product_sees_it_there(self) -> None:
        """Nothing is copied across: the sub-product derives its own view."""
        import parent_inbox

        result = hierarchy_sync.run(self.main_ws)
        self.assertEqual(result["role"], wt.ROLE_MAIN)
        self.assertTrue((self.main_ws / "plan" / "SUBPRODUCTS.md").exists())
        self.assertGreaterEqual(result["counts"]["error"], 1)

        self.assertEqual([], pw.list_pending(self.child_ws), "findings are derived, never queued")
        self.assertNotIn("GCP", (self.child_ws / "DOUBTS.md").read_text(encoding="utf-8"))

        box = parent_inbox.inbox(self.child_ws)
        self.assertTrue(box["ask"], "the sub-product must see the conflict from its own side")
        self.assertEqual("deployment-conflict", box["ask"][0]["kind"])

    def test_resolved_finding_stops_appearing(self) -> None:
        import finding_log
        import parent_inbox

        hierarchy_sync.run(self.main_ws)
        box = parent_inbox.inbox(self.child_ws)
        finding_log.resolve(self.child_ws, box["ask"][0], finding_log.DECLINED, note="platform is wrong")
        self.assertEqual(0, parent_inbox.inbox(self.child_ws)["total"])

    def test_changed_upstream_value_reopens_a_resolved_finding(self) -> None:
        """A 'no' about AWS must not silently suppress a later switch to Azure."""
        import finding_log
        import parent_inbox

        hierarchy_sync.run(self.main_ws)
        box = parent_inbox.inbox(self.child_ws)
        finding_log.resolve(self.child_ws, box["ask"][0], finding_log.DECLINED)
        self.assertEqual(0, parent_inbox.inbox(self.child_ws)["total"])

        (self.main_ws / "plan" / "main_plan.md").write_text(
            MAIN_PLAN.replace("| Cloud provider | AWS |", "| Cloud provider | Azure |"), encoding="utf-8"
        )
        self.assertEqual(1, parent_inbox.inbox(self.child_ws)["total"])

    def test_every_finding_carries_a_recommended_answer(self) -> None:
        import parent_inbox

        hierarchy_sync.run(self.main_ws)
        for item in parent_inbox.inbox(self.child_ws)["ask"]:
            question = parent_inbox.question(item)
            self.assertIn(question["recommended"], question["options"])
            self.assertTrue(question["why"].strip())

    def test_sub_gets_parent_context(self) -> None:
        hierarchy_sync.run(self.main_ws)
        result = hierarchy_sync.run(self.child_ws)
        self.assertEqual(result["role"], wt.ROLE_SUB)
        text = (self.child_ws / "plan" / "PARENT_CONTEXT.md").read_text(encoding="utf-8")
        self.assertIn("Cloud provider", text)
        self.assertIn("AWS", text)
        self.assertIn("Datastore", text)

    def test_readiness_reports_blockers(self) -> None:
        info = hierarchy_sync.readiness(self.main_ws)
        self.assertEqual(info["children"], 1)
        self.assertTrue(any("deployment-conflict" in b for b in info["blockers"]))

    def test_stale_reports_are_removed_after_unlink(self) -> None:
        """A stale report would keep feeding a session constraints that no longer apply."""
        hierarchy_sync.run(self.main_ws)
        hierarchy_sync.run(self.child_ws)
        self.assertTrue((self.main_ws / "plan" / "SUBPRODUCTS.md").exists())
        self.assertTrue((self.child_ws / "plan" / "PARENT_CONTEXT.md").exists())

        wt.set_role(self.child_ws, wt.ROLE_STANDALONE, pinned=True)
        wt.set_role(self.main_ws, wt.ROLE_STANDALONE, pinned=True)
        hierarchy_sync.run(self.main_ws)
        hierarchy_sync.run(self.child_ws)
        self.assertFalse((self.main_ws / "plan" / "SUBPRODUCTS.md").exists())
        self.assertFalse((self.child_ws / "plan" / "PARENT_CONTEXT.md").exists())

    def test_manifest_block_mentions_reports(self) -> None:
        result = hierarchy_sync.run(self.main_ws)
        block = "\n".join(hierarchy_sync.manifest_block(self.main_ws, result))
        self.assertIn("plan/SUBPRODUCTS.md", block)


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


class TestBackwardCompatibility(TreeSandbox):
    """A standalone workspace must behave exactly as it did before this feature."""

    def test_no_reports_written(self) -> None:
        result = hierarchy_sync.run(self.main_ws)
        self.assertEqual(result["role"], wt.ROLE_STANDALONE)
        self.assertIsNone(result["subproducts_file"])
        self.assertIsNone(result["parent_context_file"])
        self.assertFalse((self.main_ws / "plan" / "SUBPRODUCTS.md").exists())
        self.assertFalse((self.main_ws / "plan" / "PARENT_CONTEXT.md").exists())

    def test_no_manifest_block(self) -> None:
        result = hierarchy_sync.run(self.main_ws)
        self.assertEqual(hierarchy_sync.manifest_block(self.main_ws, result), [])

    def test_bootstrap_paths_unchanged(self) -> None:
        from memory_paths import session_bootstrap_paths

        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "main_plan.md").write_text("# Plan\n", encoding="utf-8")
        before = session_bootstrap_paths(self.main_ws)
        hierarchy_sync.run(self.main_ws)
        self.assertEqual(before, session_bootstrap_paths(self.main_ws))

    def test_session_start_survives_a_broken_hierarchy(self) -> None:
        """A hierarchy failure must never break session start."""
        import session_lifecycle

        original = hierarchy_sync.refresh
        hierarchy_sync.refresh = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            result = session_lifecycle._hierarchy(self.main_ws)
        finally:
            hierarchy_sync.refresh = original
        self.assertFalse(result["enabled"])
        self.assertIn("error", result)


class TestPlanPhase(TreeSandbox):
    def test_hierarchy_phase_selected_when_errors_exist(self) -> None:
        from plan_phase import compute_plan_phase

        (self.main_ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.main_ws / "plan" / "main_plan.md").write_text(MAIN_PLAN, encoding="utf-8")
        (self.main_ws / "plan" / "SUBPRODUCTS.md").write_text(
            "| Level | Sub-product | Kind | Detail |\n|---|---|---|---|\n"
            "| error | `auth-svc` | decision-conflict | datastore differs |\n",
            encoding="utf-8",
        )
        result = compute_plan_phase(self.main_ws)
        self.assertEqual(result["phase"], "hierarchy")
        self.assertIn("hierarchy", result["pipeline"])

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
