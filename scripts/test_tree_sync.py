"""`/product-tree-sync` must work from either end, and stage only from the main product."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pending_writes as pw  # noqa: E402
import tree_sync  # noqa: E402
import workspace_tree as wt  # noqa: E402

MAIN_PLAN = (
    "# Main Plan\n\n- **Name:** Platform\n\n## Deployment & Infrastructure\n\n"
    "| Item | Choice |\n|---|---|\n| Cloud provider | AWS |\n"
)
PRODUCT_MAP = (
    "# Product Map\n\n| ID | Step file | Type | Title | Depends on | Status |\n"
    "|----|---|---|---|---|---|\n"
    "| 01 | step_01 | sub-product | auth svc | | outline |\n"
)


class TreeSyncSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-tree-sync-"))
        self._prev = os.environ.get("LOOP_ENGINEER_HOME")
        os.environ["LOOP_ENGINEER_HOME"] = str(self.tmp / "home")

        self.main = self.tmp / "main"
        self.main_ws = self._seed(self.main, **{"plan/main_plan.md": MAIN_PLAN, "plan/PRODUCT_MAP.md": PRODUCT_MAP})
        self.sub_ws = self._seed(
            self.main / "auth-svc",
            **{"plan/main_plan.md": "# Main Plan\n\n- **Name:** Auth\n"},
        )
        wt.refresh(self.main_ws)

    def tearDown(self) -> None:
        if self._prev is None:
            os.environ.pop("LOOP_ENGINEER_HOME", None)
        else:
            os.environ["LOOP_ENGINEER_HOME"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _seed(self, folder: Path, **files: str) -> Path:
        ws = folder / ".loop-engineer"
        (ws / "plan").mkdir(parents=True, exist_ok=True)
        (ws / "memories").mkdir(parents=True, exist_ok=True)
        (ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        for rel, body in files.items():
            path = ws / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return ws


class SyncFromEitherEnd(TreeSyncSandbox):
    def test_sync_from_main_writes_the_rollup(self) -> None:
        result = tree_sync.sync(self.main_ws)
        self.assertTrue((self.main_ws / "plan" / "SUBPRODUCTS.md").exists())
        self.assertIsNone(result["parent_refreshed"], "the main product has no parent to refresh")

    def test_sync_from_main_refreshes_each_child_parent_context(self) -> None:
        """A main-product command must publish generated context without a child-side chore."""
        context = self.sub_ws / "plan" / "PARENT_CONTEXT.md"
        self.assertFalse(context.exists())

        result = tree_sync.sync(self.main_ws)

        self.assertTrue(context.exists())
        self.assertIn("auth svc", context.read_text(encoding="utf-8"))
        self.assertEqual([str(self.sub_ws)], result["children_refreshed"])

    def test_sync_from_sub_refreshes_both_ends(self) -> None:
        """The point of the command: the parent stops being stale without going there."""
        rollup = self.main_ws / "plan" / "SUBPRODUCTS.md"
        if rollup.exists():
            rollup.unlink()

        result = tree_sync.sync(self.sub_ws)

        self.assertTrue((self.sub_ws / "plan" / "PARENT_CONTEXT.md").exists())
        self.assertTrue(rollup.exists(), "syncing from the sub-product must refresh the parent roll-up")
        self.assertEqual(str(self.main_ws), result["parent_refreshed"])

    def test_sync_from_sub_advances_its_watermark(self) -> None:
        import parent_watermark as wmk

        self.assertIsNone(wmk.read_watermark(self.sub_ws, self.main_ws))
        tree_sync.sync(self.sub_ws)
        self.assertIsNotNone(wmk.read_watermark(self.sub_ws, self.main_ws))

    def _conflict(self) -> None:
        (self.main_ws / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | Postgres |\n", encoding="utf-8"
        )
        (self.sub_ws / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | DynamoDB |\n", encoding="utf-8"
        )

    def test_sync_never_queues_anything(self) -> None:
        """Findings are derived on both sides - the pending queue stays empty."""
        self._conflict()
        tree_sync.sync(self.main_ws)
        tree_sync.sync(self.sub_ws)
        self.assertEqual([], pw.list_pending(self.sub_ws))

    def test_repeated_sync_is_idempotent(self) -> None:
        import parent_inbox

        self._conflict()
        for _ in range(3):
            tree_sync.sync(self.main_ws)
        self.assertEqual(1, parent_inbox.inbox(self.sub_ws)["total"], "one disagreement, one open finding")

    def test_watermark_is_held_while_findings_are_open(self) -> None:
        """Advancing it early would silence a question the user was never asked."""
        import finding_log
        import parent_inbox
        import parent_watermark as wmk

        self._conflict()
        tree_sync.sync(self.sub_ws)
        self.assertIsNone(wmk.read_watermark(self.sub_ws, self.main_ws))

        box = parent_inbox.inbox(self.sub_ws)
        finding_log.resolve(self.sub_ws, box["ask"][0], finding_log.ACCEPTED)
        tree_sync.sync(self.sub_ws)
        self.assertIsNotNone(wmk.read_watermark(self.sub_ws, self.main_ws))

    def test_standalone_workspace_is_a_no_op(self) -> None:
        alone = self._seed(self.tmp / "alone", **{"plan/main_plan.md": MAIN_PLAN})
        result = tree_sync.sync(alone)
        self.assertEqual(0, result["self"].get("children"))
        self.assertIsNone(result["self"].get("parent"))
        self.assertIn("standalone", tree_sync.describe(result).lower())

    def test_no_stage_reports_without_queueing(self) -> None:
        (self.main_ws / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | Postgres |\n", encoding="utf-8"
        )
        (self.sub_ws / "DECISIONS.md").write_text(
            "# Decisions\n\n| Topic | Decision |\n|---|---|\n| Datastore | DynamoDB |\n", encoding="utf-8"
        )
        result = tree_sync.sync(self.main_ws, stage=False)
        self.assertTrue(result["self"]["counts"]["error"])
        self.assertEqual([], pw.list_pending(self.sub_ws))


class AutoMaintenance(TreeSyncSandbox):
    """Chores folded into session-start so they stop being separate commands."""

    def test_every_main_session_publishes_generated_context_to_children(self) -> None:
        from session_lifecycle import session_start

        context = self.sub_ws / "plan" / "PARENT_CONTEXT.md"
        context.unlink(missing_ok=True)

        session_start(self.main_ws, command="/revise-plan", tool="codex", skip_recall=True)

        self.assertTrue(context.exists())
        manifest = (self.main_ws / "plan" / "SESSION_MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("refreshed automatically for 1 linked sub-product", manifest)

    def test_revise_plan_text_does_not_rebootstrap_the_product(self) -> None:
        from session_lifecycle import session_start

        product_map = self.main_ws / "plan" / "PRODUCT_MAP.md"
        before = product_map.read_text(encoding="utf-8")

        session_start(
            self.main_ws,
            command="/revise-plan",
            tool="codex",
            text="Use centralized IAM for every sub-product",
            skip_recall=True,
        )

        self.assertEqual(before, product_map.read_text(encoding="utf-8"))
        self.assertFalse((self.main_ws / "plan" / "PLAN_BOOTSTRAP.md").exists())

    def test_plan_loop_text_still_bootstraps_the_product(self) -> None:
        from session_lifecycle import session_start

        session_start(
            self.main_ws,
            command="/plan-loop",
            tool="codex",
            text="A platform with centralized IAM and two workflow sub-products",
            skip_recall=True,
        )

        self.assertTrue((self.main_ws / "plan" / "PLAN_BOOTSTRAP.md").exists())

    def test_session_start_refreshes_ultraplan_status(self) -> None:
        from session_lifecycle import session_start

        status = self.main_ws / "plan" / "ULTRAPLAN_STATUS.md"
        self.assertFalse(status.exists())
        session_start(self.main_ws, command="/plan-loop", tool="claude", skip_recall=True)
        self.assertTrue(status.exists())

    def test_session_start_dedupes_pending_writes(self) -> None:
        from session_lifecycle import session_start

        for _ in range(2):
            pw.stage_file_write(
                self.sub_ws,
                relative_path="DOUBTS.md",
                action="append",
                content="- [ ] same note",
                reason="test",
                origin={"finding_id": "x"},
            )
        session_start(self.sub_ws, command="/develop-product", tool="claude", skip_recall=True)
        self.assertLessEqual(len(pw.list_pending(self.sub_ws)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
