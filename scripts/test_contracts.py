"""The contract registry, and the four things it must catch."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import contracts as ct  # noqa: E402
import scope_paths as sp  # noqa: E402


CONTRACT = """id: auth.session-v1
provider: auth
status: agreed
surface: "POST /session/verify -> {tenant_id, subject, scopes[]}"
consumers:
  - scope: portal
    status: agreed
  - scope: billing
    status: declined
    rationale: "signed JWT instead (D-014)"
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.ws = self.root / "Platform" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)

        self.auth = sp.create_scope(self.ws, "auth", name="Auth", map_id="01")
        self.auth.provides = ["auth.session-v1"]
        sp.write_scope(self.ws, self.auth)

        self.portal = sp.create_scope(self.ws, "portal", name="Portal", map_id="02")
        self.portal.consumes = ["auth.session-v1"]
        sp.write_scope(self.ws, self.portal)

        self.billing = sp.create_scope(self.ws, "billing", name="Billing", map_id="03")

        ct.contracts_dir(self.ws).mkdir(parents=True)
        (ct.contracts_dir(self.ws) / "auth.session-v1.yml").write_text(CONTRACT, encoding="utf-8")

    def kinds(self, tasks=None):
        return [f.kind for f in ct.check(self.ws, tasks=tasks or [])]


class Parsing(Sandbox):
    def test_a_contract_round_trips_without_a_yaml_dependency(self) -> None:
        parsed = ct.parse_contract(ct.contracts_dir(self.ws) / "auth.session-v1.yml")
        self.assertEqual(parsed.id, "auth.session-v1")
        self.assertEqual(parsed.provider, "auth")
        self.assertEqual(parsed.status, "agreed")
        self.assertIn("POST /session/verify", parsed.surface)
        self.assertEqual([c.scope for c in parsed.consumers], ["portal", "billing"])
        self.assertEqual(parsed.consumer("billing").status, "declined")
        self.assertIn("D-014", parsed.consumer("billing").rationale)

    def test_writing_and_re_reading_preserves_the_record(self) -> None:
        original = ct.parse_contract(ct.contracts_dir(self.ws) / "auth.session-v1.yml")
        original.status = ct.IMPLEMENTED
        ct.write_contract(self.ws, original)
        again = ct.parse_contract(ct.contracts_dir(self.ws) / "auth.session-v1.yml")
        self.assertEqual(again.status, ct.IMPLEMENTED)
        self.assertEqual(len(again.consumers), 2)
        self.assertEqual(again.surface, original.surface)

    def test_a_healthy_registry_reports_nothing(self) -> None:
        self.assertEqual(self.kinds(), [])


class Checks(Sandbox):
    def test_consuming_something_nobody_provides_is_an_error(self) -> None:
        self.portal.consumes = ["auth.session-v1", "search.index-v1"]
        sp.write_scope(self.ws, self.portal)
        findings = ct.check(self.ws, tasks=[])
        self.assertEqual([f.kind for f in findings], ["contract-unprovided"])
        self.assertIn("search.index-v1", findings[0].message)
        self.assertEqual(findings[0].scope, "portal")

    def test_a_provider_that_is_not_a_scope_is_an_error(self) -> None:
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(CONTRACT.replace("provider: auth", "provider: identity"), encoding="utf-8")
        findings = ct.check(self.ws, tasks=[])
        self.assertIn("contract-unprovided", [f.kind for f in findings])

    def test_building_against_a_draft_contract_is_an_error(self) -> None:
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(CONTRACT.replace("status: agreed", "status: draft", 1), encoding="utf-8")
        tasks = [{"id": "PORTAL-TASK-002", "scope": "portal", "status": "in_progress"}]
        findings = [f for f in ct.check(self.ws, tasks=tasks) if f.kind == "contract-unimplemented"]
        self.assertEqual(len(findings), 1)
        self.assertIn("PORTAL-TASK-002", findings[0].message)

    def test_a_declined_consumer_is_an_answer_not_a_gap(self) -> None:
        """Deciding not to integrate is a real decision - it must not be reported."""
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(CONTRACT.replace("status: agreed", "status: draft", 1), encoding="utf-8")
        tasks = [{"id": "BILLING-TASK-001", "scope": "billing", "status": "in_progress"}]
        self.assertEqual(
            [f for f in ct.check(self.ws, tasks=tasks) if f.kind == "contract-unimplemented"], []
        )

    def test_editing_a_frozen_surface_is_a_breaking_change(self) -> None:
        ct.lock_surfaces(self.ws)
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(
            CONTRACT.replace("{tenant_id, subject, scopes[]}", "{subject}"), encoding="utf-8"
        )
        findings = [f for f in ct.check(self.ws, tasks=[]) if f.kind == "contract-breaking"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].scope, "auth")

    def test_a_draft_surface_may_change_freely(self) -> None:
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(CONTRACT.replace("status: agreed", "status: draft", 1), encoding="utf-8")
        ct.lock_surfaces(self.ws)
        path.write_text(
            CONTRACT.replace("status: agreed", "status: draft", 1).replace("{subject}", "{x}"),
            encoding="utf-8",
        )
        self.assertNotIn("contract-breaking", self.kinds())

    def test_a_consumer_left_on_a_superseded_version_is_warned(self) -> None:
        (ct.contracts_dir(self.ws) / "auth.session-v2.yml").write_text(
            "id: auth.session-v2\nprovider: auth\nstatus: draft\nsupersedes: auth.session-v1\nconsumers: []\n",
            encoding="utf-8",
        )
        self.auth.provides = ["auth.session-v1", "auth.session-v2"]
        sp.write_scope(self.ws, self.auth)
        findings = [f for f in ct.check(self.ws, tasks=[]) if f.kind == "consumer-unnotified"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].scope, "portal")

    def test_a_contract_the_provider_does_not_declare_is_warned(self) -> None:
        self.auth.provides = []
        sp.write_scope(self.ws, self.auth)
        self.assertIn("contract-undeclared", self.kinds())

    def test_a_consumer_that_is_not_a_scope_is_warned(self) -> None:
        path = ct.contracts_dir(self.ws) / "auth.session-v1.yml"
        path.write_text(CONTRACT.replace("- scope: portal", "- scope: ghost"), encoding="utf-8")
        self.assertIn("contract-unknown-consumer", self.kinds())


class Impact(Sandbox):
    def test_impact_names_the_provider_and_live_consumers(self) -> None:
        impact = ct.impact_of(self.ws, "auth.session-v1")
        self.assertTrue(impact["known"])
        self.assertEqual(impact["provider"], "auth")
        self.assertEqual(impact["consumers"], ["portal"])

    def test_an_unknown_contract_reports_unknown_rather_than_guessing(self) -> None:
        self.assertFalse(ct.impact_of(self.ws, "nope-v1")["known"])


if __name__ == "__main__":
    unittest.main()
