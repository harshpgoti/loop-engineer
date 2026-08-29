from __future__ import annotations

import copy
import unittest
from pathlib import Path

from skill_audit import SkillAudit, load_policy


ROOT = Path(__file__).resolve().parents[1]


class SkillAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy(ROOT)

    def test_all_canonical_skills_satisfy_shared_contract(self) -> None:
        self.assertEqual([], SkillAudit(ROOT, self.policy).validate())

    def test_every_registered_skill_has_a_policy_class(self) -> None:
        audit = SkillAudit(ROOT, self.policy)
        self.assertEqual(set(audit.skill_files), set(audit.assignments))

    def test_unknown_skill_assignment_is_rejected(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["assignments"]["missing-skill"] = "read-only"
        findings = SkillAudit(ROOT, policy).validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-OWNERSHIP-002" for item in findings))

    def test_missing_contract_reference_is_rejected(self) -> None:
        audit = SkillAudit(ROOT, self.policy)
        name = next(iter(audit.skill_files))
        audit.skill_text[name] = audit.skill_text[name].replace(audit.contract_marker, "")
        findings = audit.validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-CONTRACT-001" and item["skill"] == name for item in findings))

    def test_mutating_skill_requires_rollback_or_recovery_guidance(self) -> None:
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        audit.contract_text = audit.contract_text.replace("rollback", "reversal").replace("recovery", "reversal")
        audit.skill_text["docs"] = audit.skill_text["docs"].replace("rollback", "reversal").replace("recovery", "reversal")
        findings = audit.validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-SAFETY-004" and item["skill"] == "docs" for item in findings))

    def test_missing_referenced_app_path_is_rejected(self) -> None:
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        audit.skill_text["docs"] += "\nRead `scripts/definitely_missing.py`.\n"
        findings = audit.validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-REFERENCE-005" and item["skill"] == "docs" for item in findings))

    def test_skill_without_activation_path_is_rejected(self) -> None:
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        original = audit._activation_sources
        audit._activation_sources = lambda: {
            path: text.replace("skills/docs/SKILL.md", "")
            for path, text in original().items()
        }
        findings = audit.validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-REACHABILITY-006" and item["skill"] == "docs" for item in findings))


if __name__ == "__main__":
    unittest.main()
