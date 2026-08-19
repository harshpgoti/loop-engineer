"""Main-plan changes must reach an in-development sub-product, and say what changed."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hierarchy_drift as drift  # noqa: E402
import parent_watermark as wm  # noqa: E402

DEPLOY = "## Deployment & Infrastructure\n\n| Item | Choice |\n|---|---|\n| Cloud provider | {cloud} |\n"
PLAN = "# Main Plan\n\nStatus: **INITIALIZED**\n\n" + DEPLOY
MAP = (
    "# Product Map\n\n| ID | Step file | Type | Title | Depends on | Ultraplan status |\n"
    "|----|---|---|---|---|---|\n{rows}"
)


def make_workspace(folder: Path, *, cloud: str = "AWS") -> Path:
    ws = folder / ".loop-engineer"
    (ws / "plan").mkdir(parents=True, exist_ok=True)
    (ws / "plan" / "main_plan.md").write_text(PLAN.format(cloud=cloud), encoding="utf-8")
    return ws


def child_entry(name: str, ws: Path, map_id: str) -> dict:
    return {"name": name, "data_dir": ws, "path": str(ws.parent), "map_id": map_id}


class ParentPropagation(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.main = make_workspace(self.root)
        (self.main / "plan" / "PRODUCT_MAP.md").write_text(
            MAP.format(rows="| 01 | step_01 | service | auth svc |  | outline |\n"), encoding="utf-8"
        )
        self.sub = make_workspace(self.root / "auth-svc")
        self.children = [child_entry("auth-svc", self.sub, "01")]

    def _findings(self, kind_prefix="parent-"):
        return [f for f in drift.check_children(self.main, self.children) if f["kind"].startswith(kind_prefix)]

    def test_no_baseline_stays_silent(self):
        (self.main / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Tracing | OpenTelemetry spans required |\n",
            encoding="utf-8",
        )
        self.assertEqual([], self._findings(), "a sub-product with no watermark must not be spammed")

    def test_new_platform_decision_reaches_subproduct(self):
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Tracing | OpenTelemetry spans required |\n",
            encoding="utf-8",
        )
        found = self._findings()
        self.assertTrue(found, "a new platform decision must produce a finding")
        self.assertEqual("parent-added", found[0]["kind"])
        self.assertIn("OpenTelemetry", found[0]["detail"])
        self.assertTrue(found[0]["stage"], "parent updates must reach the sub-product")

    def test_changed_value_reports_both_sides(self):
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")
        found = [f for f in self._findings() if f["kind"] == "parent-changed"]
        self.assertTrue(found)
        self.assertIn("AWS", found[0]["detail"])
        self.assertIn("GCP", found[0]["detail"])

    def test_removed_decision_is_reported(self):
        (self.main / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Tracing | OpenTelemetry spans required |\n",
            encoding="utf-8",
        )
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "DECISIONS.md").write_text("# Decisions\n", encoding="utf-8")
        self.assertTrue([f for f in self._findings() if f["kind"] == "parent-removed"])

    def test_in_flight_work_escalates_to_error(self):
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")
        self.assertEqual(drift.LEVEL_WARN, self._findings()[0]["level"])

        (self.sub / "TASKS.yml").write_text(
            "tasks:\n  - id: TASK-001\n    title: build token issuer\n    status: in_progress\n", encoding="utf-8"
        )
        self.assertEqual(drift.LEVEL_ERROR, self._findings()[0]["level"])

    def test_resync_clears_the_finding(self):
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")
        self.assertTrue(self._findings())
        wm.sync(self.sub, self.main, map_id="01")
        self.assertEqual([], self._findings(), "after the sub-product syncs, the change is no longer news")

    def test_repeated_checks_are_stable(self):
        wm.sync(self.sub, self.main, map_id="01")
        (self.main / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")
        first = [f["id"] for f in self._findings()]
        for _ in range(3):
            self.assertEqual(first, [f["id"] for f in self._findings()], "finding ids must be stable for dedupe")


class ManyMainsManySubs(unittest.TestCase):
    """Multiple main products, each with several sub-products, must stay independent."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.mains = {}
        for main_name, subs in (("alpha", ("auth", "portal")), ("beta", ("billing", "search", "notify"))):
            main = make_workspace(self.root / main_name)
            rows = "".join(
                f"| {i:02d} | step_{i:02d} | service | {s} |  | outline |\n" for i, s in enumerate(subs, start=1)
            )
            (main / "plan" / "PRODUCT_MAP.md").write_text(MAP.format(rows=rows), encoding="utf-8")
            children = []
            for i, s in enumerate(subs, start=1):
                ws = make_workspace(self.root / main_name / s)
                wm.sync(ws, main, map_id=f"{i:02d}")
                children.append(child_entry(s, ws, f"{i:02d}"))
            self.mains[main_name] = (main, children)

    def test_change_in_one_main_does_not_touch_the_other(self):
        alpha, alpha_children = self.mains["alpha"]
        beta, beta_children = self.mains["beta"]

        (alpha / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")

        alpha_hits = [f for f in drift.check_children(alpha, alpha_children) if f["kind"].startswith("parent-")]
        beta_hits = [f for f in drift.check_children(beta, beta_children) if f["kind"].startswith("parent-")]

        self.assertEqual({"auth", "portal"}, {f["sub"] for f in alpha_hits}, "both alpha subs must be told")
        self.assertEqual([], beta_hits, "beta and its sub-products must be unaffected")

    def test_one_subproduct_syncing_does_not_clear_its_siblings(self):
        alpha, alpha_children = self.mains["alpha"]
        (alpha / "plan" / "main_plan.md").write_text(PLAN.format(cloud="GCP"), encoding="utf-8")

        auth = next(c for c in alpha_children if c["name"] == "auth")
        wm.sync(auth["data_dir"], alpha, map_id="01")

        hits = [f for f in drift.check_children(alpha, alpha_children) if f["kind"].startswith("parent-")]
        self.assertEqual({"portal"}, {f["sub"] for f in hits})

    def test_relinking_to_another_parent_starts_a_fresh_baseline(self):
        alpha, _ = self.mains["alpha"]
        beta, _ = self.mains["beta"]
        moved = make_workspace(self.root / "moved")
        wm.sync(moved, alpha, map_id="01")

        self.assertIsNotNone(wm.read_watermark(moved, alpha))
        self.assertIsNone(wm.read_watermark(moved, beta), "a different parent must not reuse the old baseline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
