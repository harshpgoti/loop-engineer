from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from learning_candidates import candidates, observe, promote


class LearningCandidateTests(unittest.TestCase):
    def test_requires_repeated_distinct_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            for session in ("s1", "s2", "s3"):
                observe(workspace, pattern="Run schema validation before generation", evidence="Prevented stale output", session_id=session, confidence=.9, source="session-review")
            self.assertTrue(candidates(workspace)[0]["eligible"])

    def test_duplicate_session_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            for _ in range(2):
                observe(workspace, pattern="Same", evidence="Evidence", session_id="s1", confidence=.9, source="review")
            self.assertEqual(1, candidates(workspace)[0]["observations"])

    def test_sensitive_observation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                observe(Path(tmp), pattern="Remember API key", evidence="secret=abc", session_id="s1", confidence=.9, source="review")

    def test_promotion_requires_eligibility_and_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            item = observe(workspace, pattern="Candidate", evidence="Evidence", session_id="s1", confidence=.9, source="review")
            with self.assertRaises(ValueError):
                promote(workspace, item["fingerprint"], approved_by="")
            with self.assertRaises(ValueError):
                promote(workspace, item["fingerprint"], approved_by="owner")


if __name__ == "__main__":
    unittest.main()
