"""Verify the loop closes itself: closeout writes memory, queue stays empty, repeats are no-ops."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_paths import ensure_memory_layout, memory_file  # noqa: E402
from pending_writes import list_pending, stage_memory_write  # noqa: E402
from session_lifecycle import session_end  # noqa: E402


class LoopClosesItself(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / ".loop-engineer"
        self.tmp.mkdir(parents=True)
        ensure_memory_layout(self.tmp)
        (self.tmp / "DECISIONS.md").write_text(
            "# Decisions\n\n"
            "- Chose Postgres over DynamoDB for the billing ledger, needs transactions\n"
            "- Auth uses short-lived JWTs issued by the gateway, refresh server-side\n",
            encoding="utf-8",
        )
        (self.tmp / "HANDOFF.md").write_text(
            "# Handoff\n\n- Intake agent retry budget capped at three attempts per claim\n",
            encoding="utf-8",
        )

    def test_closeout_writes_memory_without_approval(self):
        session_end(self.tmp, command="/product-develop", summary="t")
        memory = memory_file(self.tmp).read_text(encoding="utf-8")
        self.assertIn("Postgres over DynamoDB", memory)
        self.assertIn("short-lived JWTs", memory)
        self.assertIn("retry budget", memory)
        self.assertEqual([], list_pending(self.tmp), "closeout must not queue same-workspace memory")

    def test_repeat_closeout_does_not_duplicate(self):
        session_end(self.tmp, command="/product-develop", summary="t")
        first = memory_file(self.tmp).read_text(encoding="utf-8")
        for _ in range(4):
            session_end(self.tmp, command="/product-develop", summary="t")
        after = memory_file(self.tmp).read_text(encoding="utf-8")
        self.assertEqual(
            first.count("Postgres over DynamoDB"),
            after.count("Postgres over DynamoDB"),
            "repeated closeouts duplicated a memory entry",
        )
        self.assertEqual([], list_pending(self.tmp))

    def test_staging_is_idempotent_when_explicitly_requested(self):
        for _ in range(5):
            stage_memory_write(
                self.tmp, target="memory", action="append", content="same entry", reason="r"
            )
        self.assertEqual(1, len(list_pending(self.tmp)), "identical proposals must collapse to one")

    def test_stage_mode_still_available(self):
        session_end(self.tmp, command="/product-develop", summary="t", stage=True)
        self.assertTrue(list_pending(self.tmp), "--stage must still queue instead of applying")


if __name__ == "__main__":
    unittest.main(verbosity=2)
