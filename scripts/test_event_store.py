from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from event_store import append, read


class EventStoreTests(unittest.TestCase):
    def test_append_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            first = append(workspace, "session.started", {"command": "plan"}, idempotency_key="s1:start")
            second = append(workspace, "session.started", {"command": "changed"}, idempotency_key="s1:start")
            self.assertEqual(first, second)
            self.assertEqual(1, len(read(workspace)))

    def test_sensitive_keys_are_redacted_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            event = append(Path(tmp), "finding.recorded", {"nested": {"token": "private"}}, idempotency_key="f1")
            self.assertEqual("[REDACTED]", event["payload"]["nested"]["token"])

    def test_unknown_event_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                append(Path(tmp), "shell.execute", {}, idempotency_key="x")

    def test_reusing_key_for_another_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            append(workspace, "session.started", {}, idempotency_key="same")
            with self.assertRaises(ValueError):
                append(workspace, "session.ended", {}, idempotency_key="same")


if __name__ == "__main__":
    unittest.main()
