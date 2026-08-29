#!/usr/bin/env python3
"""Audit every canonical skill against the shared operating contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = re.compile(
    r"(?<![\w./-])((?:skills|commands|scripts|templates|docs|manifests|tools|harnesses|fixtures|evals)/[A-Za-z0-9_./*-]+)"
)
FILE_SUFFIXES = {".md", ".py", ".json", ".yml", ".yaml", ".sh", ".ps1", ".tsx", ".ts", ".js"}


def load_policy(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "manifests" / "skill_policy.json").read_text(encoding="utf-8"))


class SkillAudit:
    def __init__(self, root: Path, policy: dict[str, Any]) -> None:
        self.root = root
        self.policy = policy
        self.contract_marker = policy.get("contract_marker", "")
        self.contract_text = (root / self.contract_marker).read_text(encoding="utf-8")
        self.skill_files = {
            path.parent.name: path for path in sorted((root / "skills").glob("*/SKILL.md"))
        }
        self.skill_text = {name: path.read_text(encoding="utf-8") for name, path in self.skill_files.items()}
        self.assignments = policy.get("assignments", {})

    def _activation_sources(self) -> dict[Path, str]:
        sources = {self.root / "AGENTS.md": (self.root / "AGENTS.md").read_text(encoding="utf-8")}
        for base in (self.root / "commands", self.root / "skills"):
            for path in base.rglob("*.md"):
                sources[path] = path.read_text(encoding="utf-8")
        return sources

    def _referenced_paths(self, text: str) -> set[str]:
        paths: set[str] = set()
        for match in APP_PATH.finditer(text):
            relative = match.group(1).rstrip(".,:;`)]}")
            if (
                not any(token in relative for token in ("*", "<", ">", "{"))
                and Path(relative).suffix.lower() in FILE_SUFFIXES
            ):
                paths.add(relative)
        return paths

    @staticmethod
    def _finding(rule_id: str, severity: str, skill: str, evidence: str, remediation: str) -> dict[str, str]:
        raw = f"{rule_id}|{skill}|{evidence}".encode("utf-8")
        return {
            "rule_id": rule_id,
            "severity": severity,
            "confidence": "high",
            "skill": skill,
            "location": f"skills/{skill}/SKILL.md" if skill else "manifests/skill_policy.json",
            "evidence": evidence,
            "remediation": remediation,
            "fingerprint": hashlib.sha256(raw).hexdigest()[:16],
        }

    def validate(self) -> list[dict[str, str]]:
        findings: list[dict[str, str]] = []
        actual = set(self.skill_files)
        assigned = set(self.assignments)
        for name in sorted(actual - assigned):
            findings.append(self._finding("SKILL-OWNERSHIP-001", "high", name, "No policy class assigned", "Assign a skill class."))
        for name in sorted(assigned - actual):
            findings.append(self._finding("SKILL-OWNERSHIP-002", "high", name, "Assignment has no canonical skill", "Remove the stale assignment."))

        classes = self.policy.get("classes", {})
        activation_sources = self._activation_sources()
        for name, text in self.skill_text.items():
            if self.contract_marker not in text:
                findings.append(self._finding("SKILL-CONTRACT-001", "high", name, "Shared contract reference missing", f"Reference `{self.contract_marker}`."))
            class_name = self.assignments.get(name)
            if class_name not in classes:
                findings.append(self._finding("SKILL-CLASS-003", "high", name, f"Unknown policy class: {class_name}", "Use a declared skill class."))
                continue
            effective = f"{text}\n{self.contract_text}".lower()
            for term in classes[class_name].get("required_terms", []):
                if term.lower() not in effective:
                    findings.append(self._finding("SKILL-CONTRACT-003", "medium", name, f"Required concept missing: {term}", f"Document `{term}` behavior."))
            if classes[class_name].get("requires_rollback") and not any(term in effective for term in ("rollback", "recovery")):
                findings.append(self._finding("SKILL-SAFETY-004", "high", name, "No rollback or recovery guidance", "Declare the reversal path before mutation."))
            for relative in sorted(self._referenced_paths(text)):
                if not (self.root / relative).exists() and not (self.root / "templates" / "starter" / relative).exists():
                    findings.append(
                        self._finding(
                            "SKILL-REFERENCE-005",
                            "high",
                            name,
                            f"Referenced app path does not exist: {relative}",
                            "Fix the path or remove the stale instruction.",
                        )
                    )
            canonical_path = f"skills/{name}/SKILL.md"
            incoming = [
                path
                for path, source in activation_sources.items()
                if path != self.skill_files[name] and canonical_path in source
            ]
            if not incoming:
                findings.append(
                    self._finding(
                        "SKILL-REACHABILITY-006",
                        "high",
                        name,
                        "No incoming activation reference from AGENTS.md, commands, or another skill",
                        "Wire the skill into a public command or a deterministically selected parent skill.",
                    )
                )
        return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    audit = SkillAudit(ROOT, load_policy(ROOT))
    findings = audit.validate()
    if args.json:
        print(json.dumps({"version": 1, "skills": len(audit.skill_files), "findings": findings}, indent=2))
    elif findings:
        for finding in findings:
            print(f"{finding['severity'].upper()} {finding['rule_id']} {finding['location']}: {finding['evidence']}")
    else:
        print(f"Skill audit OK: {len(audit.skill_files)} canonical skills satisfy the shared contract.")
    return 1 if any(item["severity"] in {"high", "critical"} for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
