"""The graph must agree with the parsers it replaces, and answer what they cannot."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import graph_index as gi  # noqa: E402

TASKS = """version: 1
tasks:
  - id: TASK-001
    title: Scaffold
    gate: G-PLATFORM-01
    status: completed

  - id: TASK-002
    title: Token issuer (DQ-001)
    gate: G-MODULE-01
    status: in_progress
    blocked_by: [TASK-001]
"""

GATES = """# Gates

```yaml
gates:
  G-PLATFORM-01:
    name: Platform core
    status: passed

  G-MODULE-01:
    name: First step
    status: blocked
```
"""

GATES_LIST = """version: 1
gates:

  - id: G-M-INIT-01
    name: Master initialized
    status: passed

  - id: G-M-EVAL-01
    name: Eval gate
    status: blocked
"""

DOUBTS = """# Doubts

### DQ-001: Token lifetime
- **Status:** open
- **Question:** How long, given E-001?

### DQ-002: Pricing
- **Status:** resolved
- **Resolution (2026-08-01):** Flat fee, per E-002.
"""

DECISIONS = """# Decision Log

### D-001: Flat fee pricing
- **Date:** 2026-08-01
- **Supersedes:** DQ-002
- **Decision:** Flat fee only, on the strength of E-002.
"""

EVIDENCE = """# Evidence Log

### E-001: Token lifetimes in the wild
- **Claim:** Most issuers use 15 minutes.

### E-002: Percentage pricing is regulated
- **Claim:** AKS exposure.

### E-003: Nothing cites this
- **Claim:** Orphaned.
"""


class Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="loop-graph-"))
        self.ws = self.tmp / "product" / ".loop-engineer"
        (self.ws / "plan").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories").mkdir(parents=True, exist_ok=True)
        (self.ws / "memories" / "MEMORY.md").write_text("# mem", encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(TASKS, encoding="utf-8")
        (self.ws / "GATES.yml").write_text(GATES, encoding="utf-8")
        (self.ws / "DOUBTS.md").write_text(DOUBTS, encoding="utf-8")
        (self.ws / "DECISIONS.md").write_text(DECISIONS, encoding="utf-8")
        (self.ws / "EVIDENCE_LOG.md").write_text(EVIDENCE, encoding="utf-8")
        (self.ws / "plan" / "main_plan.md").write_text("# Plan\n\n- **Name:** Test\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def graph(self) -> dict:
        return gi.build(self.ws)


class Structure(Sandbox):
    def test_supersedes_nothing_does_not_create_edges_from_explanatory_prose(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            DECISIONS + "\n### D-003: Concrete detail\n- **Supersedes:** nothing. Extends D-001 by adding detail.\n",
            encoding="utf-8",
        )

        graph = gi.build(self.ws)

        self.assertNotIn(["D-003", "supersedes", "D-001"], graph["edges"])

    def test_scoped_amendment_does_not_globally_supersede_the_old_decision(self) -> None:
        (self.ws / "DECISIONS.md").write_text(
            DECISIONS
            + "\n### D-004: Capture for one row\n- **Supersedes:** amends D-001 for row 12 only.\n",
            encoding="utf-8",
        )

        graph = gi.build(self.ws)

        self.assertIn(["D-004", "amends", "D-001"], graph["edges"])
        self.assertNotIn(["D-004", "supersedes", "D-001"], graph["edges"])

    def test_every_record_becomes_a_node(self) -> None:
        nodes = self.graph()["nodes"]
        for node_id in ("TASK-001", "TASK-002", "G-PLATFORM-01", "G-MODULE-01",
                        "DQ-001", "DQ-002", "D-001", "E-001", "E-002", "E-003"):
            self.assertIn(node_id, nodes, f"{node_id} missing")

    def test_edges_match_the_declared_fields(self) -> None:
        edges = {tuple(e) for e in self.graph()["edges"]}
        self.assertIn(("TASK-002", "blocked_by", "TASK-001"), edges)
        self.assertIn(("TASK-002", "gate", "G-MODULE-01"), edges)
        self.assertIn(("D-001", "supersedes", "DQ-002"), edges)
        self.assertIn(("DQ-001", "cites", "E-001"), edges)

    def test_gate_mapping_and_list_forms_both_parse(self) -> None:
        """A real workspace used `- id: G-M-INIT-01`; only the mapping form parsed."""
        self.assertGreaterEqual(sum(1 for n in self.graph()["nodes"].values() if n["kind"] == gi.GATE), 2)
        (self.ws / "GATES.yml").write_text(GATES_LIST, encoding="utf-8")
        nodes = self.graph()["nodes"]
        self.assertIn("G-M-INIT-01", nodes)
        self.assertEqual("passed", nodes["G-M-INIT-01"]["status"])
        self.assertTrue(nodes["G-M-INIT-01"]["done"])

    def test_dq_is_not_parsed_as_a_decision(self) -> None:
        self.assertEqual(gi.DOUBT, gi.kind_of("DQ-001"))
        self.assertEqual(gi.DECISION, gi.kind_of("D-001"))

    def test_adrs_in_a_step_architecture_doc_are_indexed(self) -> None:
        """Real ADRs live in plan/steps/*/architecture.md, not DECISIONS.md."""
        folder = self.ws / "plan" / "steps" / "06-claims"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "architecture.md").write_text(
            "# Architecture\n\n### ADR-06-05 - Ingest exports, not APIs\n\nBased on E-001.\n", encoding="utf-8"
        )
        graph = self.graph()
        self.assertIn("ADR-06-05", graph["nodes"])
        self.assertIn(["ADR-06-05", "cites", "E-001"], graph["edges"])

    def test_adrs_in_a_scope_owned_ultraplan_pack_are_indexed(self) -> None:
        folder = self.ws / "plan" / "products" / "evidence-bank"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "scope.json").write_text('{"slug":"evidence-bank","map_id":"12"}', encoding="utf-8")
        (folder / "architecture.md").write_text(
            "# Architecture\n\n### ADR-12-01 - Tenant keys\n\nBased on E-001.\n", encoding="utf-8"
        )

        graph = self.graph()

        self.assertIn("ADR-12-01", graph["nodes"])
        self.assertEqual("plan/products/evidence-bank/architecture.md", graph["nodes"]["ADR-12-01"]["source"])
        self.assertIn(["ADR-12-01", "cites", "E-001"], graph["edges"])

    def test_build_is_deterministic(self) -> None:
        self.assertEqual(self.graph(), self.graph())


class Queries(Sandbox):
    def test_liveness_follows_citations_transitively(self) -> None:
        """TASK-002 -> DQ-001 -> E-001. A first-hop scan cannot see E-001."""
        graph = self.graph()
        live = gi.reachable_from(graph, gi.live_nodes(graph), depth=3)
        self.assertIn("DQ-001", live)
        self.assertIn("E-001", live)

    def test_settled_evidence_is_not_live(self) -> None:
        graph = self.graph()
        live = gi.reachable_from(graph, gi.live_nodes(graph), depth=3)
        self.assertNotIn("E-003", live, "nothing references it")

    def test_orphans_are_found(self) -> None:
        found = gi.orphans(self.graph())
        self.assertIn("E-003", found.get(gi.EVIDENCE, []))

    def test_cross_workspace_reference_is_external_not_dangling(self) -> None:
        graph = self.graph()
        self.assertEqual([], graph["dangling"], "nothing here should be broken")

    def test_a_reference_to_nothing_is_dangling(self) -> None:
        (self.ws / "DOUBTS.md").write_text(
            DOUBTS + "\n### DQ-003: Broken\n- **Status:** open\n- **Question:** See E-999.\n", encoding="utf-8"
        )
        self.assertIn(["DQ-003", "cites", "E-999"], self.graph()["dangling"])

    def test_subgraph_defaults_to_one_hop(self) -> None:
        """RepoGraph measured 2-hop context as worse than 1-hop; take it deliberately."""
        view = gi.subgraph(self.graph(), "TASK-002")
        self.assertIn("TASK-001", view["nodes"])
        self.assertIn("G-MODULE-01", view["nodes"])
        self.assertNotIn("E-001", view["nodes"], "two hops away - not by default")
        self.assertIn("E-001", gi.subgraph(self.graph(), "TASK-002", depth=2)["nodes"])


class History(Sandbox):
    def test_a_withdrawn_edge_is_retracted_not_deleted(self) -> None:
        graph = self.graph()
        gi.record_history(self.ws, graph, today="2026-08-01")

        (self.ws / "TASKS.yml").write_text(TASKS.replace("    blocked_by: [TASK-001]\n", ""), encoding="utf-8")
        gi.record_history(self.ws, self.graph(), today="2026-08-10")

        closed = gi.closed_edges(self.ws)
        self.assertTrue(closed)
        entry = next(c for c in closed if c["edge"] == ["TASK-002", "blocked_by", "TASK-001"])
        self.assertEqual(gi.RETRACTED, entry["closed_as"])
        self.assertEqual("2026-08-10", entry["closed_at"])

    def test_as_of_shows_what_was_believed_then(self) -> None:
        """The question no parse of current files can answer."""
        gi.record_history(self.ws, self.graph(), today="2026-08-01")
        (self.ws / "TASKS.yml").write_text(TASKS.replace("    blocked_by: [TASK-001]\n", ""), encoding="utf-8")
        gi.record_history(self.ws, self.graph(), today="2026-08-10")

        before = gi.as_of(self.ws, "2026-08-05")
        after = gi.as_of(self.ws, "2026-08-15")
        self.assertIn(["TASK-002", "blocked_by", "TASK-001"], before["edges"])
        self.assertNotIn(["TASK-002", "blocked_by", "TASK-001"], after["edges"])

    def test_correct_removes_an_edge_from_every_past_view(self) -> None:
        """Retract = the world changed. Correct = it was never true."""
        gi.record_history(self.ws, self.graph(), today="2026-08-01")
        edge = ["TASK-002", "blocked_by", "TASK-001"]
        self.assertIn(edge, gi.as_of(self.ws, "2026-08-05")["edges"])

        self.assertTrue(gi.correct(self.ws, edge, note="never actually blocked"))
        self.assertNotIn(edge, gi.as_of(self.ws, "2026-08-05")["edges"])
        self.assertEqual(gi.CORRECTED, gi.closed_edges(self.ws)[0]["closed_as"])

    def test_reasserting_reopens_a_closed_edge(self) -> None:
        gi.record_history(self.ws, self.graph(), today="2026-08-01")
        original = (self.ws / "TASKS.yml").read_text(encoding="utf-8")
        (self.ws / "TASKS.yml").write_text(original.replace("    blocked_by: [TASK-001]\n", ""), encoding="utf-8")
        gi.record_history(self.ws, self.graph(), today="2026-08-10")
        (self.ws / "TASKS.yml").write_text(original, encoding="utf-8")
        gi.record_history(self.ws, self.graph(), today="2026-08-12")
        self.assertEqual([], gi.closed_edges(self.ws))

    def test_history_survives_a_malformed_log(self) -> None:
        gi.history_path(self.ws).parent.mkdir(parents=True, exist_ok=True)
        gi.history_path(self.ws).write_text("{not json", encoding="utf-8")
        gi.record_history(self.ws, self.graph(), today="2026-08-01")
        self.assertTrue(gi.read_history(self.ws)["edges"])


class ArchiveIntegration(Sandbox):
    def test_evidence_after_read_bound_is_indexed(self) -> None:
        late = "\n".join(["- filler"] * 40_000)
        (self.ws / "EVIDENCE_LOG.md").write_text(
            "# Evidence Log\n" + late + "\n### E-LATE-001: Late evidence\n- **Claim:** retained\n",
            encoding="utf-8",
        )

        graph = gi.build(self.ws)

        self.assertIn("E-LATE-001", graph["nodes"])

    def test_graph_liveness_is_a_superset_of_the_flat_scan(self) -> None:
        """The safety property: the graph must never archive something the scan kept."""
        import state_archive as sa

        graph_live = sa.live_references(self.ws)
        scan_live = sa._live_references_by_scan(self.ws)
        archivable = {nid for src in ("EVIDENCE_LOG.md", "DECISIONS.md")
                      for nid, _b in gi._sections(gi._read(self.ws / src))}
        self.assertEqual(set(), (scan_live - graph_live) & archivable)

    def test_graph_protects_transitively_cited_evidence(self) -> None:
        """A live task -> a settled decision -> its evidence.

        The scan reads open doubts and unfinished tasks only, so it sees `D-001` in
        the task body but never opens DECISIONS.md to find what `D-001` rests on.
        """
        import state_archive as sa

        (self.ws / "TASKS.yml").write_text(
            TASKS + "\n  - id: TASK-003\n    title: Apply the pricing decision D-001\n"
            "    gate: G-MODULE-01\n    status: in_progress\n",
            encoding="utf-8",
        )
        graph_live = sa.live_references(self.ws)
        scan_live = sa._live_references_by_scan(self.ws)

        self.assertIn("D-001", graph_live)
        self.assertIn("D-001", scan_live, "both see the first hop")
        self.assertIn("E-002", graph_live, "the graph follows D-001 to its evidence")
        self.assertNotIn("E-002", scan_live, "the scan stops at the first hop")


if __name__ == "__main__":
    unittest.main(verbosity=2)
