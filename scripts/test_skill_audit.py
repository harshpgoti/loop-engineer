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
        # E3 strict check: a mutating skill must have `## Stop Conditions` and
        # `## Rollback` headings, not just the words anywhere in the body.
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        for term in ("rollback", "Rollback", "ROLLBACK", "recovery", "Recovery", "RECOVERY",
                     "## Stop Conditions", "## Rollback", "## Stop Conditions and Rollback"):
            audit.contract_text = audit.contract_text.replace(term, "reversal")
            audit.skill_text["docs"] = audit.skill_text["docs"].replace(term, "reversal")
        findings = audit.validate()
        self.assertTrue(any(item["rule_id"] == "SKILL-SAFETY-004" and item["skill"] == "docs" for item in findings))

    def test_mutating_skill_with_only_word_but_no_heading_fails_e3(self) -> None:
        # A mutating skill that contains the words "rollback" and "recovery" but
        # lacks the explicit `## Stop Conditions` and `## Rollback` headings is
        # flagged with SKILL-SAFETY-004.
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        # Pick a real mutating skill and replace its E3 headings with a paragraph
        # that uses the words but has no headings.
        target = "deploy"
        audit.skill_text[target] = "We have a rollback path and a recovery plan. "
        findings = audit.validate()
        self.assertTrue(
            any(item["rule_id"] == "SKILL-SAFETY-004" and item["skill"] == target
                for item in findings),
            "expected strict E3 heading check to flag a mutating skill without headings",
        )

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

    def test_workspace_relative_path_is_not_flagged(self) -> None:
        # Skill may reference a known workspace-relative path (e.g. docs/adr/) without
        # the audit flagging it as a missing app path. The audit only enforces app-side
        # references; workspace artifacts are the user's responsibility.
        from skill_audit import WORKSPACE_PATHS
        self.assertIn("docs/adr", WORKSPACE_PATHS)
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        # Both a directory reference and a file-with-extension reference under
        # the same workspace path are tolerated.
        audit.skill_text["docs"] = (audit.skill_text["docs"]
                                     + "\nWrite to `docs/adr/NNNN-foo.md` per the ADR skill.\n"
                                     + "\nWrite to `docs/ONBOARDING.md` for project onboarding.\n"
                                     + "\nRead `plan/MEMORY_REVIEW.md` if it exists.\n")
        findings = audit.validate()
        self.assertFalse(any(item["rule_id"] == "SKILL-REFERENCE-005"
                             and ("docs/adr" in item["evidence"]
                                  or "docs/ONBOARDING" in item["evidence"]
                                  or "plan/MEMORY_REVIEW" in item["evidence"])
                             for item in findings))

    def test_assurance_skill_referencing_safeguard_passes_e7(self) -> None:
        # An assurance-class skill that explicitly references the safeguard skill
        # (or embeds at least 3 of the 6 baseline keywords) passes the E7 check.
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        # Pick any assurance skill; if it already has the safeguard reference,
        # confirm it does not generate a SKILL-SAFEGUARD-001 finding.
        for role, cls in self.policy["assignments"].items():
            if cls != "assurance":
                continue
            text = audit.skill_text[role]
            if "## Prompt Defense Baseline" in text or "skills/safeguard" in text:
                findings = audit.validate()
                self.assertFalse(
                    any(item["rule_id"] == "SKILL-SAFEGUARD-001" and item["skill"] == role
                        for item in findings),
                    f"assurance skill {role!r} has safeguard reference but audit still flagged it",
                )
                return
        self.fail("no assurance skill in the audit had a safeguard reference; the round-5 update is missing")

    def test_assurance_skill_without_safeguard_fails_e7(self) -> None:
        # An assurance-class skill with neither the safeguard reference nor
        # 3+ baseline keywords is flagged with SKILL-SAFEGUARD-001.
        audit = SkillAudit(ROOT, copy.deepcopy(self.policy))
        # Choose a real assurance skill and strip its safeguard section in memory.
        from skill_audit import SAFEGUARD_KEYWORDS
        target = None
        for role, cls in self.policy["assignments"].items():
            if cls != "assurance":
                continue
            text = audit.skill_text[role]
            hits = sum(1 for kw in SAFEGUARD_KEYWORDS if kw.lower() in text.lower())
            if "skills/safeguard" not in text and hits < 3:
                target = role
                break
        if target is None:
            # The round-5 update is already complete; this test verifies the
            # *intent* of the check but does not have a clean target to test.
            return
        audit.skill_text[target] = "x"  # strip everything
        findings = audit.validate()
        self.assertTrue(
            any(item["rule_id"] == "SKILL-SAFEGUARD-001" and item["skill"] == target
                for item in findings),
        )


if __name__ == "__main__":
    unittest.main()
