"""The evals loop: a run must be recorded, comparable, and impossible to invert."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_suite as ev  # noqa: E402

CASES = [
    {"id": "c-001", "category": "auth", "expected_root_cause": "no prior auth"},
    {"id": "c-002", "category": "auth", "expected_root_cause": "expired auth"},
    {"id": "c-003", "category": "coding", "expected_root_cause": "wrong modifier"},
    {"id": "c-004", "category": "coding", "expected_root_cause": "bundled"},
]
OTHER = [{"id": "o-001", "market": "ontario", "requires_human_approval": True}]


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-eval-"))
        self.product = self.tmp / "engine"
        self.ws = self.product / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        evals = self.product / "agent" / "evals"
        evals.mkdir(parents=True, exist_ok=True)
        (evals / "cases.json").write_text(json.dumps(CASES), encoding="utf-8")
        (evals / "ontario.json").write_text(json.dumps(OTHER), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def results(self, failing: set[str], kind: str = "deterministic") -> dict:
        ids = list(ev.discover_cases(self.ws))
        return {
            cid: {"pass": cid not in failing, "kind": kind, "why": "" if cid not in failing else "mismatch"}
            for cid in ids
        }


class Discovery(Sandbox):
    def test_any_json_list_with_ids_is_a_suite(self) -> None:
        """No imposed schema - a product keeps its own domain fields."""
        found = ev.discover_cases(self.ws)
        self.assertEqual({"c-001", "c-002", "c-003", "c-004", "o-001"}, set(found))
        self.assertEqual({"cases.json": 4, "ontario.json": 1}, ev.suites(self.ws))

    def test_the_case_keeps_its_own_fields(self) -> None:
        self.assertEqual("no prior auth", ev.discover_cases(self.ws)["c-001"]["case"]["expected_root_cause"])

    def test_category_falls_back_across_naming(self) -> None:
        found = ev.discover_cases(self.ws)
        self.assertEqual("auth", found["c-001"]["category"])
        self.assertEqual("ontario", found["o-001"]["category"])

    def test_run_records_are_not_mistaken_for_cases(self) -> None:
        """Reading runs/ as cases would grow the suite every time it is exercised."""
        ev.record_run(self.ws, self.results(set()))
        self.assertEqual(5, len(ev.discover_cases(self.ws)))

    def test_no_eval_directory_is_not_an_error(self) -> None:
        shutil.rmtree(self.product / "agent")
        self.assertEqual({}, ev.discover_cases(self.ws))
        self.assertIsNone(ev.record_run(self.ws, {}))


class Recording(Sandbox):
    def test_a_run_is_scored_and_persisted(self) -> None:
        ev.record_run(self.ws, self.results({"c-001"}), model="test-model")
        run = ev.latest_run(self.ws)
        self.assertEqual(5, run["total"])
        self.assertEqual(4, run["passed"])
        self.assertEqual(0.8, run["score"])
        self.assertEqual("test-model", run["model"])

    def test_a_failing_judged_verdict_must_say_why(self) -> None:
        """An unreviewable verdict is worse than none - it looks like evidence."""
        with self.assertRaises(ValueError):
            ev.record_run(self.ws, {"c-001": {"pass": False, "kind": "judge", "why": ""}})

    def test_a_passing_judged_verdict_needs_no_rationale(self) -> None:
        ev.record_run(self.ws, {"c-001": {"pass": True, "kind": "judge"}})
        self.assertIsNotNone(ev.latest_run(self.ws))

    def test_an_unknown_verdict_kind_falls_back_to_deterministic(self) -> None:
        ev.record_run(self.ws, {"c-001": {"pass": True, "kind": "vibes"}})
        self.assertEqual("deterministic", ev.latest_run(self.ws)["results"]["c-001"]["kind"])


class Comparison(Sandbox):
    def test_regression_and_fix_are_not_confused(self) -> None:
        ev.record_run(self.ws, self.results({"c-001"}))
        ev.record_run(self.ws, self.results({"c-003"}))
        change = ev.regressions(self.ws)
        self.assertEqual(["c-003"], change["regressed"])
        self.assertEqual(["c-001"], change["fixed"])

    def test_two_runs_in_the_same_instant_still_order_correctly(self) -> None:
        """A `-2` filename suffix sorts before `.json` and once inverted the verdict."""
        original = ev._now
        ev._now = lambda: "2026-08-23T00:00:00.000+00:00"
        try:
            ev.record_run(self.ws, self.results({"c-001"}), model="first")
            ev.record_run(self.ws, self.results({"c-003"}), model="second")
        finally:
            ev._now = original

        self.assertEqual(["first", "second"], [r["model"] for r in ev.runs(self.ws)])
        change = ev.regressions(self.ws)
        self.assertEqual(["c-003"], change["regressed"])
        self.assertEqual(["c-001"], change["fixed"])

    def test_the_first_run_has_nothing_to_regress_against(self) -> None:
        ev.record_run(self.ws, self.results({"c-001"}))
        self.assertEqual([], ev.regressions(self.ws)["regressed"])

    def test_a_dropped_case_is_reported(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        partial = self.results(set())
        partial.pop("c-004")
        ev.record_run(self.ws, partial)
        self.assertIn("c-004", ev.regressions(self.ws)["dropped"])


class Gate(Sandbox):
    def test_cases_with_no_run_do_not_satisfy_the_gate(self) -> None:
        status = ev.gate_status(self.ws)
        self.assertFalse(status["ok"])
        self.assertIn("no run has ever been recorded", status["reason"])

    def test_a_low_score_blocks(self) -> None:
        ev.record_run(self.ws, self.results({"c-001", "c-002"}))
        status = ev.gate_status(self.ws)
        self.assertFalse(status["ok"])
        self.assertIn("below", status["reason"])

    def test_an_unexercised_case_blocks_even_at_a_perfect_score(self) -> None:
        """An untouched case is not a passing case."""
        partial = {"c-001": {"pass": True, "kind": "deterministic"}}
        ev.record_run(self.ws, partial)
        status = ev.gate_status(self.ws)
        self.assertFalse(status["ok"])
        self.assertIn("not exercised", status["reason"])

    def test_full_coverage_above_the_bar_satisfies(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        self.assertTrue(ev.gate_status(self.ws)["ok"])


class Analysis(Sandbox):
    def test_failures_group_by_category_worst_first(self) -> None:
        ev.record_run(self.ws, self.results({"c-001", "c-002", "c-003"}))
        groups = ev.failure_groups(self.ws)
        self.assertEqual(["auth", "coding"], list(groups))
        self.assertEqual(2, len(groups["auth"]))

    def test_the_report_names_the_dominant_category(self) -> None:
        ev.record_run(self.ws, self.results({"c-001", "c-002"}))
        path = ev.write_analysis(self.ws)
        text = path.read_text(encoding="utf-8")
        self.assertIn("auth", text)
        self.assertIn("Fix the group, not the individual cases", text)

    def test_unexercised_cases_are_listed(self) -> None:
        ev.record_run(self.ws, {"c-001": {"pass": True, "kind": "deterministic"}})
        self.assertIn("Not exercised", ev.write_analysis(self.ws).read_text(encoding="utf-8"))

    def test_no_run_means_nothing_to_analyse(self) -> None:
        self.assertIsNone(ev.write_analysis(self.ws))


class Settlement(Sandbox):
    def test_old_runs_keep_their_score_and_lose_detail(self) -> None:
        for index in range(13):
            ev.record_run(self.ws, self.results({"c-001"} if index % 2 else set()))
        found = ev.runs(self.ws)
        self.assertEqual(13, len(found))
        self.assertTrue(found[0].get("compacted"))
        self.assertEqual({}, found[0]["results"])
        self.assertIsNotNone(found[0]["score"])
        self.assertTrue(found[-1]["results"], "recent runs keep full detail")


class Surface(Sandbox):
    def test_the_manifest_is_silent_when_healthy(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        self.assertEqual([], ev.manifest_block(self.ws))

    def test_the_manifest_speaks_up_on_a_regression(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        ev.record_run(self.ws, self.results({"c-003"}))
        block = "\n".join(ev.manifest_block(self.ws))
        self.assertIn("regressed", block)
        self.assertIn("c-003", block)

    def test_the_manifest_speaks_up_when_the_gate_is_unmet(self) -> None:
        self.assertIn("Eval gate not satisfied", "\n".join(ev.manifest_block(self.ws)))

    def test_no_cases_means_no_block(self) -> None:
        shutil.rmtree(self.product / "agent")
        self.assertEqual([], ev.manifest_block(self.ws))


class BehaviourDrift(Sandbox):
    """A score describes the agent that earned it, not whatever the agent is now."""

    def declare(self) -> None:
        (self.product / "agent" / "evals" / "behaviour.json").write_text(
            json.dumps({"behaviour": ["src/**/*.py"]}), encoding="utf-8"
        )
        (self.product / "src").mkdir(parents=True, exist_ok=True)
        (self.product / "src" / "prompt.py").write_text("PROMPT = 'v1'\n", encoding="utf-8")

    def test_a_declared_surface_beats_the_default_guess(self) -> None:
        """The real surface in a real product was backend/app/agent - no default finds that."""
        _globs, declared = ev.behaviour_globs(self.ws)
        self.assertFalse(declared)
        self.declare()
        globs, declared = ev.behaviour_globs(self.ws)
        self.assertTrue(declared)
        self.assertEqual(["src/**/*.py"], globs)

    def test_a_run_records_what_the_agent_looked_like(self) -> None:
        self.declare()
        ev.record_run(self.ws, self.results(set()))
        self.assertIn("src/prompt.py", ev.latest_run(self.ws)["behaviour"])

    def test_an_unchanged_agent_is_not_stale(self) -> None:
        self.declare()
        ev.record_run(self.ws, self.results(set()))
        self.assertFalse(ev.behaviour_changed(self.ws)["stale"])

    def test_changing_the_agent_invalidates_the_score(self) -> None:
        self.declare()
        ev.record_run(self.ws, self.results(set()))
        (self.product / "src" / "prompt.py").write_text("PROMPT = 'v2'\n", encoding="utf-8")
        drift = ev.behaviour_changed(self.ws)
        self.assertTrue(drift["stale"])
        self.assertIn("src/prompt.py", drift["changed"])

    def test_a_stale_score_does_not_satisfy_the_gate(self) -> None:
        self.declare()
        ev.record_run(self.ws, self.results(set()))
        self.assertTrue(ev.gate_status(self.ws)["ok"])
        (self.product / "src" / "prompt.py").write_text("PROMPT = 'v2'\n", encoding="utf-8")
        status = ev.gate_status(self.ws)
        self.assertFalse(status["ok"])
        self.assertIn("behaviour changed", status["reason"])

    def test_adding_a_behaviour_file_counts_as_a_change(self) -> None:
        self.declare()
        ev.record_run(self.ws, self.results(set()))
        (self.product / "src" / "tools.py").write_text("def t(): pass\n", encoding="utf-8")
        self.assertTrue(ev.behaviour_changed(self.ws)["stale"])

    def test_no_cases_means_no_staleness_to_report(self) -> None:
        shutil.rmtree(self.product / "agent")
        self.assertFalse(ev.behaviour_changed(self.ws)["stale"])


class BuildRouting(Sandbox):
    """The trigger is computed, not judged - /product-develop reaches it on its own."""

    def setUp(self) -> None:
        super().setUp()
        (self.ws / "TASKS.yml").write_text(
            "tasks:\n  - id: TASK-001\n    title: t\n    gate: G-A\n    status: in_progress\n",
            encoding="utf-8",
        )
        (self.product / "src").mkdir(parents=True, exist_ok=True)
        (self.product / "src" / "prompt.py").write_text("PROMPT = 'v1'\n", encoding="utf-8")
        (self.product / "agent" / "evals" / "behaviour.json").write_text(
            json.dumps({"behaviour": ["src/**/*.py"]}), encoding="utf-8"
        )

    def phase(self) -> str:
        import build_phase

        return build_phase.compute_build_phase(self.ws)["phase"]

    def test_cases_with_no_run_route_to_evaluate(self) -> None:
        self.assertEqual("evaluate", self.phase())

    def test_a_clean_scored_suite_routes_to_the_real_work(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        self.assertEqual("implement", self.phase())

    def test_a_regression_routes_back_to_evaluate(self) -> None:
        ev.record_run(self.ws, self.results(set()))
        ev.record_run(self.ws, self.results({"c-001"}))
        self.assertEqual("evaluate", self.phase())

    def test_a_behaviour_change_routes_back_to_evaluate(self) -> None:
        """The whole point: nobody had to notice, and nobody had to decide."""
        ev.record_run(self.ws, self.results(set()))
        self.assertEqual("implement", self.phase())
        (self.product / "src" / "prompt.py").write_text("PROMPT = 'v2'\n", encoding="utf-8")
        self.assertEqual("evaluate", self.phase())

    def test_a_product_with_no_eval_suite_is_unaffected(self) -> None:
        shutil.rmtree(self.product / "agent")
        self.assertEqual("implement", self.phase())

if __name__ == "__main__":
    unittest.main(verbosity=2)
