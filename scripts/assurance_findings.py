#!/usr/bin/env python3
"""Structured assurance findings, baseline deltas, policy verdicts, and SARIF."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
CONFIDENCE = {"low", "medium", "high"}


def fingerprint(rule_id: str, location: str) -> str:
    stable_location = re.sub(r":\d+(?::\d+)?$", "", location.strip().lower())
    return hashlib.sha256(f"{rule_id.strip().upper()}|{stable_location}".encode("utf-8")).hexdigest()[:20]


def finding(*, rule_id: str, severity: str, confidence: str, location: str, evidence: str,
            remediation: str, provenance: str) -> dict[str, str]:
    if severity not in SEVERITY:
        raise ValueError(f"invalid severity: {severity}")
    if confidence not in CONFIDENCE:
        raise ValueError(f"invalid confidence: {confidence}")
    required = {"rule_id": rule_id, "location": location, "evidence": evidence,
                "remediation": remediation, "provenance": provenance}
    missing = [name for name, value in required.items() if not str(value).strip()]
    if missing:
        raise ValueError(f"missing finding fields: {', '.join(missing)}")
    return {**required, "severity": severity, "confidence": confidence,
            "fingerprint": fingerprint(rule_id, location)}


def evaluate(findings: list[dict[str, str]], *, threshold: str = "high",
             baseline: set[str] | None = None) -> dict[str, Any]:
    if threshold not in SEVERITY:
        raise ValueError(f"invalid policy threshold: {threshold}")
    baseline = baseline or set()
    validated: list[dict[str, str]] = []
    errors: list[str] = []
    for index, item in enumerate(findings):
        try:
            expected = finding(**{name: item[name] for name in ("rule_id", "severity", "confidence", "location", "evidence", "remediation", "provenance")})
            if item.get("fingerprint") and item["fingerprint"] != expected["fingerprint"]:
                raise ValueError("fingerprint does not match stable identity")
            expected["baseline_status"] = "unchanged" if expected["fingerprint"] in baseline else "new"
            validated.append(expected)
        except (KeyError, ValueError) as exc:
            errors.append(f"finding[{index}]: {exc}")
    current = {item["fingerprint"] for item in validated}
    blocking = [item for item in validated if item["baseline_status"] == "new" and SEVERITY[item["severity"]] >= SEVERITY[threshold]]
    verdict = "error" if errors else "fail" if blocking else "warn" if validated else "pass"
    return {"version": 1, "verdict": verdict, "threshold": threshold, "findings": validated,
            "new": sorted(current - baseline), "unchanged": sorted(current & baseline),
            "resolved": sorted(baseline - current), "blocking": [item["fingerprint"] for item in blocking],
            "errors": errors}


def sarif(report: dict[str, Any]) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results = []
    level = {"info": "note", "low": "note", "medium": "warning", "high": "error", "critical": "error"}
    for item in report.get("findings", []):
        rules.setdefault(item["rule_id"], {"id": item["rule_id"], "shortDescription": {"text": item["remediation"]}})
        results.append({"ruleId": item["rule_id"], "level": level[item["severity"]],
                        "message": {"text": item["evidence"]},
                        "locations": [{"physicalLocation": {"artifactLocation": {"uri": item["location"]}}}],
                        "partialFingerprints": {"primaryLocationLineHash": item["fingerprint"]}})
    return {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "runs": [{"tool": {"driver": {"name": "Loop Assurance", "rules": list(rules.values())}}, "results": results}]}


def main() -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--threshold", choices=tuple(SEVERITY), default="high")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--sarif", action="store_true")
    args = parser.parse_args()
    findings = json.loads(args.input.read_text(encoding="utf-8"))
    baseline = set(json.loads(args.baseline.read_text(encoding="utf-8"))) if args.baseline else set()
    report = evaluate(findings, threshold=args.threshold, baseline=baseline)
    print(json.dumps(sarif(report) if args.sarif else report, indent=2))
    return 1 if report["verdict"] in {"fail", "error"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
