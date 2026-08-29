from __future__ import annotations

import unittest

from assurance_findings import evaluate, finding, sarif


class AssuranceFindingTests(unittest.TestCase):
    def sample(self, severity: str = "high") -> dict[str, str]:
        return finding(rule_id="SEC-001", severity=severity, confidence="high", location="app.py:12",
                       evidence="Untrusted input reaches a privileged operation.", remediation="Validate authority before execution.", provenance="deterministic-rule@1")

    def test_new_high_finding_fails_policy(self) -> None:
        self.assertEqual("fail", evaluate([self.sample()], threshold="high")["verdict"])

    def test_unchanged_baseline_does_not_block_but_remains_visible(self) -> None:
        item = self.sample()
        report = evaluate([item], threshold="high", baseline={item["fingerprint"]})
        self.assertEqual("warn", report["verdict"])
        self.assertEqual("unchanged", report["findings"][0]["baseline_status"])

    def test_resolved_baseline_is_reported(self) -> None:
        self.assertEqual(["old"], evaluate([], baseline={"old"})["resolved"])

    def test_invalid_finding_fails_closed(self) -> None:
        report = evaluate([{"rule_id": "X"}])
        self.assertEqual("error", report["verdict"])

    def test_sarif_preserves_rule_and_fingerprint(self) -> None:
        item = self.sample("medium")
        result = sarif(evaluate([item]))["runs"][0]["results"][0]
        self.assertEqual("SEC-001", result["ruleId"])
        self.assertEqual(item["fingerprint"], result["partialFingerprints"]["primaryLocationLineHash"])


if __name__ == "__main__":
    unittest.main()
