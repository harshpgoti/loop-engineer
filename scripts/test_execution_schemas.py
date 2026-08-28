from __future__ import annotations

import json
import unittest
from pathlib import Path

from execution_schemas import validate_dispatch, validate_event, validate_research, validate_review, validate_worker


class ExecutionSchemaContracts(unittest.TestCase):
    def test_golden_phase_zero_records_validate_deterministically(self) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = json.loads((root / "fixtures" / "execution" / "golden_cases.json").read_text(encoding="utf-8"))
        self.assertFalse(fixture["dirty_worktree"]["teardown"])
        validate_worker({"schema_version": 1, "run_id": "run-123456789abc", "task_id": "TASK-1", "kind": "delivery", "generation": 1, "state": "created", "run_dir": "run"})
        validate_event({"run_id": "run-123456789abc", "generation": 1, "sequence": 1, "timestamp": "2026-01-01T00:00:00+00:00", "event": "created", "event_id": "event-1", "summary": "safe"})
        validate_review({"validation_run_id": "run-aaaaaaaaaaaa", "run_id": "run-123456789abc", "validator": "reviewer", "base_commit": "base", "head_commit": "head", "verdict": "pass", "spec": "pass", "standards": "pass"})
        validate_research({"run_id": "run-123456789abc", "report": "finding", "citations": ["https://example.test"], "decision_inventory": []})
        validate_dispatch({"request_id": "dispatch-123456789abc", "task_id": "TASK-1", "repository": "repo", "command": ["agent"], "kind": "delivery", "priority": 10, "depends_on": [], "state": "queued"})

    def test_stale_or_malformed_records_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            validate_worker({"schema_version": 1, "run_id": "unsafe"})
        with self.assertRaises(ValueError):
            validate_event({"run_id": "run-123456789abc", "generation": 0, "sequence": 1, "timestamp": "x", "event": "created", "event_id": "x"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
