"""Tests for plan-reconcile: reform fanout, plan-surface drift, dead-plan retirement."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from plan_reconcile import (  # noqa: E402
    check,
    fanout,
    retire,
    superseded_map,
)


def make_workspace() -> Path:
    tmp = Path(tempfile.mkdtemp()) / ".loop-engineer"
    (tmp / "plan" / "products" / "auth").mkdir(parents=True)
    (tmp / "DECISIONS.md").write_text(
        "# Decisions\n\n"
        "## D-001: Ship a shared auth library\n\n"
        "- **Date:** 2026-01-01\n"
        "- **Decision:** Every product imports the shared auth library.\n\n"
        "## D-002: Auth is a centralized service, not a library\n\n"
        "- **Date:** 2026-02-01\n"
        "- **Status:** n/a\n"
        "- **Decision:** Auth is a centralized service. Reverses the library approach.\n"
        "- **Supersedes:** D-001\n",
        encoding="utf-8",
    )
    (tmp / "plan" / "main_plan.md").write_text(
        "# Plan\n\nAll products import the shared auth library (D-001).\n", encoding="utf-8"
    )
    (tmp / "plan" / "PRODUCT_MAP.md").write_text(
        "# Map\n\n| ID | a | Step file | b | Title | Scope | Depends on | Status |\n"
        "| 01 | x | step_01 | y | Auth | `plan/products/auth` | - | Built |\n",
        encoding="utf-8",
    )
    (tmp / "plan" / "ULTRAPLAN_STATUS.md").write_text(
        "# Ultraplan Status\n\n| Step | Title | Ultraplan | Missing artifacts |\n"
        "| step_01 | Auth | partial | architecture.md, data-model.md |\n",
        encoding="utf-8",
    )
    (tmp / "plan" / "products" / "auth" / "prd.md").write_text(
        "# PRD\n\nBuilt on the shared auth library (D-001).\n", encoding="utf-8"
    )
    (tmp / "TASKS.yml").write_text(
        "tasks:\n  - id: TASK-001\n    status: todo\n", encoding="utf-8"
    )
    (tmp / "plan" / "products" / "auth" / "TASKS.yml").write_text(
        "tasks:\n  - id: TASK-001\n    status: done\n", encoding="utf-8"
    )
    (tmp / "GATES.yml").write_text("gates: []\n", encoding="utf-8")
    (tmp / "DEPLOYMENT_PLAN.md").write_text(
        "# Deploy\n\n**Updated:** 2026-01-15\n", encoding="utf-8"
    )
    return tmp


class SupersessionParsing(unittest.TestCase):
    def test_supersedes_field_maps_old_to_new(self):
        self.assertEqual("D-002", superseded_map(make_workspace()).get("D-001"))

    def test_table_cell_superseded_does_not_map(self):
        ws = make_workspace()
        path = ws / "DECISIONS.md"
        path.write_text(
            path.read_text(encoding="utf-8")
            + "\n## D-003: Something else\n\n"
            "| item | state |\n| A | **Superseded** by D-009 |\n",
            encoding="utf-8",
        )
        self.assertNotIn("D-003", superseded_map(ws))


class StaleCitations(unittest.TestCase):
    def test_live_citation_of_dead_decision_is_blocker(self):
        findings = [f for f in check(make_workspace()) if f["code"] == "stale-citation"]
        files = {Path(f["file"]).name for f in findings}
        self.assertIn("main_plan.md", files)
        self.assertIn("prd.md", files)
        self.assertTrue(all(f["level"] == "blocker" for f in findings))

    def test_historical_neighbourhood_is_not_flagged(self):
        ws = make_workspace()
        path = ws / "plan" / "main_plan.md"
        path.write_text(
            "# Plan\n\nReverses D-001: auth is now a centralized service.\n", encoding="utf-8"
        )
        self.assertEqual(
            [], [f for f in check(ws) if Path(f["file"]).name == "main_plan.md"]
        )

    def test_logs_are_not_scanned(self):
        ws = make_workspace()
        (ws / "CURRENT_STATE.md").write_text("# State\n\n## 2026-01-01 log\n\nD-001 unchanged.\n", encoding="utf-8")
        (ws / "HANDOFF.md").write_text("# Handoff\n\nShipped under D-001.\n", encoding="utf-8")
        flagged = [f for f in check(ws) if Path(f["file"]).name in ("CURRENT_STATE.md", "HANDOFF.md")]
        self.assertEqual([], flagged)


class Mirrors(unittest.TestCase):
    def test_same_task_different_status_is_blocker(self):
        findings = [f for f in check(make_workspace()) if f["code"] == "task-mirror"]
        self.assertEqual(1, len(findings))
        self.assertIn("TASK-001", findings[0]["message"])


class MapTracker(unittest.TestCase):
    def test_built_row_with_missing_artifacts_is_blocker(self):
        findings = [f for f in check(make_workspace()) if f["code"] == "map-tracker"]
        self.assertEqual(1, len(findings))
        self.assertIn("01", findings[0]["message"])


class Fanout(unittest.TestCase):
    def test_fanout_lists_citing_and_scope_files(self):
        result = fanout(make_workspace(), "D-001", scope="auth")
        update = result["groups"]["update"]
        self.assertIn("plan/main_plan.md", [u.replace("\\", "/") for u in update])
        self.assertTrue(any("products/auth/prd.md" in u.replace("\\", "/") for u in update))
        self.assertTrue(any("ULTRAPLAN_STATUS" in r for r in result["groups"]["regenerate"]))


class Retirement(unittest.TestCase):
    def test_retire_records_ledger_and_lists_remaining(self):
        ws = make_workspace()
        result = retire(ws, rid="D-001", by="D-002", reason="service, not library", rtype="decision")
        self.assertTrue(result["recorded"])
        ledger = (ws / "plan" / "RETIRED.md").read_text(encoding="utf-8")
        self.assertIn("D-001", ledger)
        self.assertIn("D-002", ledger)
        self.assertTrue(result["remaining"], "live citations must still be listed")
        again = retire(ws, rid="D-001", by="D-002", reason="x")
        self.assertFalse(again["recorded"], "retire is idempotent")

    def test_retired_id_cited_live_is_blocker(self):
        ws = make_workspace()
        retire(ws, rid="D-009", by="D-002", reason="no longer pursued")
        (ws / "plan" / "main_plan.md").write_text("# Plan\n\nProceed with D-009.\n", encoding="utf-8")
        self.assertTrue(
            any(f["code"] == "stale-citation" and "D-009" in f["message"] for f in check(ws))
        )


class ManifestSurface(unittest.TestCase):
    def test_blockers_surface_in_session_manifest(self):
        from session_lifecycle import attention_block

        lines = attention_block(make_workspace())
        text = "\n".join(lines)
        self.assertIn("plan-reconcile blocker", text)
        self.assertIn("loop plan-reconcile check", text)

    def test_clean_plan_has_no_reconcile_line(self):
        from session_lifecycle import attention_block

        ws = make_workspace()
        (ws / "plan" / "main_plan.md").write_text("# Plan\n\nAuth is a centralized service (D-002).\n", encoding="utf-8")
        (ws / "plan" / "products" / "auth" / "prd.md").write_text("# PRD\n\nService (D-002).\n", encoding="utf-8")
        (ws / "TASKS.yml").write_text("tasks:\n  - id: TASK-001\n    status: todo\n", encoding="utf-8")
        (ws / "plan" / "products" / "auth" / "TASKS.yml").write_text(
            "tasks:\n  - id: TASK-002\n    status: todo\n", encoding="utf-8"
        )
        (ws / "plan" / "PRODUCT_MAP.md").write_text("# Map\n", encoding="utf-8")
        (ws / "plan" / "ULTRAPLAN_STATUS.md").write_text("# Ultraplan Status\n", encoding="utf-8")
        text = "\n".join(attention_block(ws))
        self.assertNotIn("plan-reconcile blocker", text)


class DoctorHook(unittest.TestCase):
    def test_doctor_warns_on_reconcile_blockers(self):
        from doctor import check_plan_reconcile

        errors, warnings, passes = [], [], []
        check_plan_reconcile(make_workspace(), errors, warnings, passes)
        self.assertEqual([], errors)
        self.assertTrue(any("plan-reconcile blocker" in w for w in warnings))


if __name__ == "__main__":
    unittest.main(verbosity=2)
