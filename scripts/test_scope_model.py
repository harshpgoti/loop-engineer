"""Scopes: addressing, text matching, stickiness, dependency order, unioned state."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import scope_layout as sl  # noqa: E402
import scope_paths as sp  # noqa: E402
import scope_state as st  # noqa: E402
import task_context as tc  # noqa: E402


MAP = """# Product Map

| ID | Step file | Type | Title | Depends on | Status |
|----|---|---|---|---|---|
| 01 | step_01 | sub-product | Auth and Identity | | ACTIVE |
| 02 | step_02 | sub-product | Customer Portal | 01 | ACTIVE |
| 03 | step_03 | sub-product | Billing API | 01 | ACTIVE |
"""

ROOT_TASKS = """tasks:
  - id: TASK-001
    title: shared CI
    status: done
  - id: TASK-002
    title: database schema
    status: todo
"""

AUTH_TASKS = """tasks:
  - id: AUTH-TASK-001
    title: session endpoint
    gate: G-AUTH-01
    status: done
  - id: AUTH-TASK-003
    title: tenant claims
    status: todo
"""

PORTAL_TASKS = """tasks:
  - id: PORTAL-TASK-002
    title: login screen
    status: todo
    blocked_by: [AUTH-TASK-003]
  - id: PORTAL-TASK-004
    title: dashboard
    status: todo
    blocked_by: [MISSING-TASK-9]
"""

AUTH_GATES = """gates:
  G-AUTH-01:
    name: Auth usable
    status: passed
"""

ROOT_GATES = """gates:
  G-PLATFORM-01:
    name: Platform foundation
    status: blocked
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        self.product = self.root / "Platform"
        self.ws = self.product / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True)
        (self.ws / "plan" / "PRODUCT_MAP.md").write_text(MAP, encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(ROOT_TASKS, encoding="utf-8")
        (self.ws / "GATES.yml").write_text(ROOT_GATES, encoding="utf-8")

        self.auth = sp.create_scope(
            self.ws, "auth", name="Auth and Identity", map_id="01", code_dir="services/auth"
        )
        self.auth.provides = ["auth.session-v1"]
        sp.write_scope(self.ws, self.auth)
        self.auth.tasks_file.write_text(AUTH_TASKS, encoding="utf-8")
        self.auth.gates_file.write_text(AUTH_GATES, encoding="utf-8")

        self.portal = sp.create_scope(
            self.ws, "portal", name="Customer Portal", map_id="02", code_dir="apps/portal"
        )
        self.portal.consumes = ["auth.session-v1"]
        sp.write_scope(self.ws, self.portal)
        self.portal.tasks_file.write_text(PORTAL_TASKS, encoding="utf-8")


class Addressing(Sandbox):
    def test_a_scope_is_found_by_slug_map_id_name_and_code_dir(self) -> None:
        for token in ("auth", "01", "Auth and Identity", "services/auth"):
            with self.subTest(token=token):
                found = sp.find_scope(self.ws, token)
                self.assertIsNotNone(found, token)
                self.assertEqual(found.slug, "auth")

    def test_an_unknown_token_finds_nothing_rather_than_guessing(self) -> None:
        self.assertIsNone(sp.find_scope(self.ws, "payments"))

    def test_the_folder_name_is_not_the_binding_key(self) -> None:
        """Retitling the map row must not unbind the scope - that was the federated bug."""
        self.auth.name = "Identity Platform"
        sp.write_scope(self.ws, self.auth)
        self.assertEqual(sp.find_scope(self.ws, "01").slug, "auth")

    def test_a_scope_folder_without_scope_json_is_still_seen(self) -> None:
        (sp.scopes_dir(self.ws) / "legacy").mkdir()
        slugs = [s.slug for s in sp.list_scopes(self.ws)]
        self.assertIn("legacy", slugs)

    def test_a_malformed_scope_json_does_not_break_the_session(self) -> None:
        (self.auth.path / "scope.json").write_text("{not json", encoding="utf-8")
        found = sp.find_scope(self.ws, "auth")
        self.assertIsNotNone(found)
        self.assertIsNone(found.map_id)

    def test_code_path_resolves_against_the_product_folder_not_the_data_dir(self) -> None:
        self.assertEqual(self.auth.code_path(self.ws), (self.product / "services" / "auth").resolve())


class TextMatching(Sandbox):
    def test_the_scope_named_in_the_command_text_is_matched(self) -> None:
        match = sp.match_text(self.ws, "start working on auth product")
        self.assertTrue(match.ok)
        self.assertEqual(match.scope.slug, "auth")

    def test_a_full_name_is_matched_as_a_phrase(self) -> None:
        match = sp.match_text(self.ws, "continue the Customer Portal checkout flow")
        self.assertTrue(match.ok)
        self.assertEqual(match.scope.slug, "portal")

    def test_an_alias_is_matched(self) -> None:
        self.auth.aliases = ["login service"]
        sp.write_scope(self.ws, self.auth)
        self.assertEqual(sp.match_text(self.ws, "fix the login service").scope.slug, "auth")

    def test_two_scopes_named_is_ambiguous_and_picks_neither(self) -> None:
        match = sp.match_text(self.ws, "wire auth into portal")
        self.assertFalse(match.ok)
        self.assertTrue(match.ambiguous)
        self.assertEqual({s.slug for s in match.candidates}, {"auth", "portal"})

    def test_an_ambiguous_prefix_picks_neither(self) -> None:
        sp.create_scope(self.ws, "portal-admin", name="Portal Admin", map_id="04")
        match = sp.match_text(self.ws, "work on porta")
        self.assertFalse(match.ok)
        self.assertGreater(len(match.candidates), 1)

    def test_text_naming_nothing_matches_nothing(self) -> None:
        self.assertFalse(sp.match_text(self.ws, "build the next thing").ok)

    def test_a_substring_of_another_word_does_not_match(self) -> None:
        """`auth` inside `author` is the substring bug the federated binder had."""
        self.assertFalse(sp.match_text(self.ws, "update the author metadata").ok)


class Resolution(Sandbox):
    def test_shared_platform_text_resolves_root_work_explicitly(self) -> None:
        res = sp.resolve(
            self.ws,
            text="Deep-plan shared-platform Step 19 Identity and Access Platform",
        )
        self.assertTrue(res.resolved)
        self.assertTrue(res.is_platform)
        self.assertEqual(res.source, "text")

    def test_shared_platform_resolves_even_before_the_first_sub_product_exists(self) -> None:
        empty = self.root / "Empty" / ".loop-engineer"
        empty.mkdir(parents=True)
        res = sp.resolve(empty, text="continue shared platform work")
        self.assertTrue(res.resolved)
        self.assertTrue(res.is_platform)

    def test_platform_can_be_selected_explicitly_and_remembered(self) -> None:
        res = sp.resolve(self.ws, explicit="platform")
        self.assertTrue(res.resolved)
        self.assertTrue(res.is_platform)

        sp.set_active(self.ws, sp.PLATFORM, session="s1")
        remembered = sp.resolve(self.ws, session="s1")
        self.assertTrue(remembered.resolved)
        self.assertTrue(remembered.is_platform)
        self.assertEqual(remembered.source, "remembered")

    def test_an_explicit_scope_beats_platform_words_in_the_text(self) -> None:
        """The flag is what scripts and internal calls pass; text must never override it."""
        res = sp.resolve(self.ws, explicit="portal", text="align with shared platform work")
        self.assertEqual(res.slug, "portal")
        self.assertFalse(res.is_platform)
        self.assertEqual(res.source, "flag")

    def test_text_naming_a_sub_product_and_platform_asks_rather_than_guessing(self) -> None:
        """Picking either would write into the wrong plan - the same rule as two scopes."""
        res = sp.resolve(self.ws, text="work on auth to match the root plan")
        self.assertFalse(res.resolved)
        self.assertFalse(res.is_platform)
        self.assertIn("both", res.reason)

    def test_a_named_scope_alone_is_unaffected_by_the_platform_path(self) -> None:
        res = sp.resolve(self.ws, text="work on auth product")
        self.assertEqual(res.slug, "auth")
        self.assertFalse(res.is_platform)

    def test_an_explicit_flag_wins(self) -> None:
        res = sp.resolve(self.ws, explicit="portal", text="work on auth")
        self.assertEqual(res.slug, "portal")
        self.assertEqual(res.source, "flag")

    def test_text_beats_a_remembered_scope(self) -> None:
        sp.set_active(self.ws, "auth", session="s1")
        res = sp.resolve(self.ws, text="continue the portal work", session="s1")
        self.assertEqual(res.slug, "portal")
        self.assertEqual(res.source, "text")

    def test_a_remembered_scope_continues_silently_in_the_same_session(self) -> None:
        sp.set_active(self.ws, "auth", session="s1")
        res = sp.resolve(self.ws, session="s1")
        self.assertEqual(res.slug, "auth")
        self.assertFalse(res.needs_confirm)

    def test_a_remembered_scope_from_another_session_is_re_confirmed(self) -> None:
        sp.set_active(self.ws, "auth", session="s1")
        res = sp.resolve(self.ws, session="s2")
        self.assertEqual(res.slug, "auth")
        self.assertTrue(res.needs_confirm)

    def test_a_remembered_scope_older_than_the_window_is_re_confirmed(self) -> None:
        stale = (datetime.now(timezone.utc) - timedelta(hours=sp.STICKY_HOURS + 1)).isoformat()
        sp.active_file(self.ws).parent.mkdir(parents=True, exist_ok=True)
        sp.active_file(self.ws).write_text(
            json.dumps({"slug": "auth", "set_at": stale, "set_by_session": "s1"}), encoding="utf-8"
        )
        res = sp.resolve(self.ws, session="s1")
        self.assertTrue(res.needs_confirm)
        self.assertIn("Continue there, or switch?", res.reason)

    def test_nothing_named_and_nothing_remembered_asks_rather_than_defaulting(self) -> None:
        """A forgotten word must never become edits to shared CI or schema."""
        res = sp.resolve(self.ws)
        self.assertIsNone(res.scope)
        self.assertEqual(res.source, "none")
        self.assertEqual({s.slug for s in res.candidates}, {"auth", "portal"})

    def test_ambiguous_text_asks_and_names_the_candidates(self) -> None:
        res = sp.resolve(self.ws, text="wire auth into portal")
        self.assertIsNone(res.scope)
        self.assertIn("more than one", res.reason)

    def test_a_pointer_file_resolves_when_nothing_else_does(self) -> None:
        folder = self.product / "services" / "auth"
        folder.mkdir(parents=True)
        sp.write_pointer(folder, "auth")
        res = sp.resolve(self.ws, cwd=folder)
        self.assertEqual(res.slug, "auth")
        self.assertEqual(res.source, "pointer")

    def test_an_unknown_explicit_scope_is_refused_not_guessed(self) -> None:
        res = sp.resolve(self.ws, explicit="payments")
        self.assertIsNone(res.scope)
        self.assertIn("No scope named", res.reason)


class DependencyOrder(Sandbox):
    def test_a_provider_is_ordered_before_its_consumer(self) -> None:
        ordered, cycles = sp.dependency_order(self.ws)
        slugs = [s.slug for s in ordered]
        self.assertLess(slugs.index("auth"), slugs.index("portal"))
        self.assertEqual(cycles, [])

    def test_the_product_map_depends_on_column_is_honoured(self) -> None:
        billing = sp.create_scope(self.ws, "billing", name="Billing API", map_id="03")
        self.assertIsNotNone(billing)
        ordered, _ = sp.dependency_order(self.ws)
        slugs = [s.slug for s in ordered]
        self.assertLess(slugs.index("auth"), slugs.index("billing"))

    def test_a_cycle_is_reported_and_not_silently_broken(self) -> None:
        self.auth.consumes = ["portal.thing-v1"]
        sp.write_scope(self.ws, self.auth)
        self.portal.provides = ["portal.thing-v1"]
        sp.write_scope(self.ws, self.portal)
        ordered, cycles = sp.dependency_order(self.ws)
        self.assertTrue(cycles, "a mutual dependency must be reported")
        self.assertEqual(ordered, [])


class UnionedState(Sandbox):
    def test_tasks_from_every_scope_load_with_their_scope_attached(self) -> None:
        tasks = st.load_tasks(self.ws)
        by_id = {t["id"]: t for t in tasks}
        self.assertEqual(by_id["TASK-002"]["scope"], sp.PLATFORM)
        self.assertEqual(by_id["AUTH-TASK-003"]["scope"], "auth")
        self.assertEqual(by_id["PORTAL-TASK-002"]["scope"], "portal")

    def test_one_scope_still_sees_platform_tasks(self) -> None:
        """Platform work gates scope work; hiding it would report a false 'ready'."""
        scoped = {t["id"] for t in st.load_tasks(self.ws, scope="auth")}
        self.assertIn("TASK-002", scoped)
        self.assertNotIn("PORTAL-TASK-002", scoped)

    def test_a_cross_scope_dependency_resolves(self) -> None:
        blocks = st.cross_scope_blocks(st.load_tasks(self.ws))
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]["task"], "PORTAL-TASK-002")
        self.assertEqual(blocks[0]["provider_scope"], "auth")
        self.assertFalse(blocks[0]["satisfied"])

    def test_a_blocked_task_is_not_ready(self) -> None:
        ready = {t["id"] for t in st.ready_tasks(st.load_tasks(self.ws))}
        self.assertNotIn("PORTAL-TASK-002", ready)
        self.assertIn("AUTH-TASK-003", ready)

    def test_a_dangling_blocker_is_reported_not_dropped(self) -> None:
        missing = st.unresolved_blockers(st.load_tasks(self.ws))
        self.assertEqual([m.missing for m in missing], ["MISSING-TASK-9"])

    def test_a_gate_id_in_blocked_by_is_not_a_dangling_task(self) -> None:
        self.portal.tasks_file.write_text(
            "tasks:\n  - id: PORTAL-TASK-009\n    blocked_by: [G-AUTH-01]\n", encoding="utf-8"
        )
        self.assertEqual(st.unresolved_blockers(st.load_tasks(self.ws)), [])

    def test_gates_union_platform_and_scope(self) -> None:
        ids = {g["id"] for g in st.load_gates(self.ws)}
        self.assertEqual(ids, {"G-PLATFORM-01", "G-AUTH-01"})
        self.assertEqual(st.duplicate_gate_ids(st.load_gates(self.ws)), [])

    def test_the_same_gate_id_in_two_scopes_is_reported(self) -> None:
        self.portal.gates_file.write_text(AUTH_GATES, encoding="utf-8")
        clashes = st.duplicate_gate_ids(st.load_gates(self.ws))
        self.assertEqual(len(clashes), 1)
        self.assertIn("G-AUTH-01", clashes[0])

    def test_summary_lists_scopes_in_dependency_order(self) -> None:
        rows = st.summarize(self.ws)
        self.assertEqual([r.slug for r in rows], ["auth", "portal"])
        self.assertIn("blocked on auth", rows[1].line())


#: The other shape a `GATES.yml` is written in - valid YAML for the same data, and the
#: shape a real root file had while every scope used the mapping form above.
ROOT_GATES_SEQUENCE = """gates:

  - id: G-PLATFORM-01
    name: Platform foundation
    status: blocked
    criteria:
      - CI runs on every push
      - schema migrations are reversible

  # ---- next section ----
  - id: G-PLATFORM-02
    name: Deploy pipeline
    status: todo
"""

PORTAL_ROW_AT_ROOT = "  - id: TASK-003\n    title: portal billing screen\n    scope: portal\n    status: todo\n"


def row(task_id: str, **fields: str) -> str:
    body = "".join(f"    {key}: {value}\n" for key, value in fields.items())
    return f"  - id: {task_id}\n" + body


class GateFileShapes(Sandbox):
    """Both declaration shapes read alike, or platform gates vanish without an error."""

    def test_sequence_form_gates_are_parsed(self) -> None:
        (self.ws / "GATES.yml").write_text(ROOT_GATES_SEQUENCE, encoding="utf-8")
        gates = st.parse_gates_file(self.ws / "GATES.yml")
        self.assertEqual([g["id"] for g in gates], ["G-PLATFORM-01", "G-PLATFORM-02"])
        self.assertEqual(gates[0]["name"], "Platform foundation")
        self.assertEqual(gates[0]["status"], "blocked")

    def test_a_sequence_form_root_file_still_joins_the_union(self) -> None:
        (self.ws / "GATES.yml").write_text(ROOT_GATES_SEQUENCE, encoding="utf-8")
        ids = {g["id"] for g in st.load_gates(self.ws)}
        self.assertEqual(ids, {"G-PLATFORM-01", "G-PLATFORM-02", "G-AUTH-01"})

    def test_a_brief_carries_the_required_gate_in_either_shape(self) -> None:
        """`gate_block` returning '' is how a brief lost its gate section silently."""
        (self.ws / "GATES.yml").write_text(ROOT_GATES_SEQUENCE, encoding="utf-8")
        block = tc.gate_block(self.ws, "G-PLATFORM-01")
        self.assertIn("G-PLATFORM-01", block)
        self.assertIn("CI runs on every push", block)
        self.assertNotIn("G-PLATFORM-02", block)
        self.assertNotIn("next section", block)
        self.assertIn("name: Auth usable", tc.gate_block(self.auth.path, "G-AUTH-01"))

    def test_mixed_shapes_across_the_workspace_are_reported(self) -> None:
        (self.ws / "GATES.yml").write_text(ROOT_GATES_SEQUENCE, encoding="utf-8")
        self.assertIn("gate-form-split", [f.kind for f in sl.findings(self.ws)])


class RowsInTheWrongFile(Sandbox):
    """A row that names its scope belongs to that scope, wherever it is written."""

    def _put_portal_row_in_root(self) -> None:
        (self.ws / "TASKS.yml").write_text(ROOT_TASKS + PORTAL_ROW_AT_ROOT, encoding="utf-8")

    def test_a_declared_scope_is_not_overwritten_with_platform(self) -> None:
        self._put_portal_row_in_root()
        by_id = {t["id"]: t for t in st.load_tasks(self.ws)}
        self.assertEqual(by_id["TASK-003"]["scope"], "portal")
        self.assertEqual(by_id["TASK-001"]["scope"], sp.PLATFORM)

    def test_the_scope_counter_sees_a_row_written_at_the_root(self) -> None:
        self._put_portal_row_in_root()
        rows = {r.slug: r for r in st.summarize(self.ws)}
        self.assertEqual(rows["portal"].tasks_total, 3)

    def test_a_scope_that_is_not_declared_stays_platform(self) -> None:
        (self.ws / "TASKS.yml").write_text(
            ROOT_TASKS + row("TASK-004", title="unknown", scope="payments", status="todo"),
            encoding="utf-8",
        )
        by_id = {t["id"]: t for t in st.load_tasks(self.ws)}
        self.assertEqual(by_id["TASK-004"]["scope"], sp.PLATFORM)
        self.assertIn("scope-unknown", [f.kind for f in sl.findings(self.ws)])


class LayoutInvariant(Sandbox):
    """The layout every sub-product shares, checked rather than assumed."""

    def test_a_clean_workspace_has_no_layout_findings(self) -> None:
        self.portal.gates_file.write_text("gates: []\n", encoding="utf-8")
        self.assertEqual([f.kind for f in sl.findings(self.ws)], [])

    def test_rows_at_the_root_and_a_stub_scope_file_are_both_reported(self) -> None:
        self.portal.tasks_file.write_text("tasks: []\n", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(ROOT_TASKS + PORTAL_ROW_AT_ROOT, encoding="utf-8")
        kinds = {f.kind for f in sl.findings(self.ws)}
        self.assertIn("scope-rows-in-root", kinds)
        self.assertIn("scope-file-stub", kinds)

    def test_a_scope_no_row_claims_is_reported_not_guessed_at(self) -> None:
        self.portal.tasks_file.write_text("tasks: []\n", encoding="utf-8")
        found = [f for f in sl.findings(self.ws) if f.kind == "scope-unplanned"]
        self.assertEqual([f.scope for f in found], ["portal"])

    def test_a_missing_scope_file_is_reported(self) -> None:
        self.portal.tasks_file.unlink()
        found = [f for f in sl.findings(self.ws) if f.kind == "scope-file-missing"]
        self.assertTrue(any("TASKS.yml" in f.message for f in found))

    def test_a_scope_ultraplan_pack_left_at_the_root_is_reported(self) -> None:
        (self.ws / "plan" / "steps" / "02-portal").mkdir(parents=True)
        found = [f for f in sl.findings(self.ws) if f.kind == "scope-steps-in-root"]
        self.assertEqual([f.scope for f in found], ["portal"])

    def test_the_master_plans_row_summary_at_the_root_is_not_drift(self) -> None:
        """`plan/step_NN_<slug>.md` is where the master plan keeps its row summary."""
        (self.ws / "plan" / "step_02_portal.md").write_text("# Portal\n", encoding="utf-8")
        self.assertEqual([f for f in sl.findings(self.ws) if f.kind == "scope-steps-in-root"], [])

    def test_a_gate_no_file_declares_is_reported(self) -> None:
        self.portal.tasks_file.write_text(
            PORTAL_TASKS + row("PORTAL-TASK-006", title="checkout", gate="G-NOWHERE-01", status="todo"),
            encoding="utf-8",
        )
        found = [f for f in sl.findings(self.ws) if f.kind == "gate-undeclared"]
        self.assertEqual([f.scope for f in found], ["portal"])
        self.assertIn("G-NOWHERE-01", found[0].message)

    def test_a_scope_task_gated_by_a_platform_gate_is_not_a_finding(self) -> None:
        """Platform work gates scope work - that is the model, not drift."""
        self.portal.gates_file.write_text("gates: []\n", encoding="utf-8")
        self.portal.tasks_file.write_text(
            PORTAL_TASKS + row("PORTAL-TASK-007", title="deploy", gate="G-PLATFORM-01", status="todo"),
            encoding="utf-8",
        )
        self.assertEqual([f for f in sl.findings(self.ws) if f.kind == "gate-undeclared"], [])


if __name__ == "__main__":
    unittest.main()
