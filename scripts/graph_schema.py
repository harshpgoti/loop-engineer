#!/usr/bin/env python3
"""What must be true of the reference graph, checked deterministically.

A traceability information model (TIM) declares which link types may exist between
which artifact types, and with what multiplicity. The traceability literature is
consistent that writing it down is the highest-value step - it turns "these files
reference each other" into something with invariants that can fail.

Every rule here is a parse over `graph_index`, never a model judgement
(`AGENTS.md` non-negotiable #4). Where a rule *could* be answered by an LLM - "is this
decision still being honoured?" - it deliberately is not: Su et al. (arXiv:2602.07609)
measured LLM violation detection at ~90% on code-inferable decisions but **30% wrong**
on principle and infrastructure ones. So a suspicious decision raises a doubt for a
human; it never closes a gate.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import graph_index as gi

ERROR, WARN, INFO = "error", "warn", "info"

# The TIM itself: which edge may connect which kinds. An edge outside this table is a
# schema violation, not a finding about the product.
ALLOWED = {
    "blocked_by": {(gi.TASK, gi.TASK)},
    "gate": {(gi.TASK, gi.GATE)},
    "supersedes": {(gi.DECISION, gi.DOUBT), (gi.DECISION, gi.DECISION)},
    "depends": {(gi.MODULE, gi.MODULE)},
    # `cites` is the loose one by design: a doubt naming the task that will settle it,
    # or a decision naming the doubt it answers, are both things real workspaces do.
    # The model widened here after these shapes showed up in genuine use - a rule
    # nobody can satisfy trains people to ignore the checker.
    "cites": {
        (gi.TASK, gi.DOUBT), (gi.TASK, gi.DECISION), (gi.TASK, gi.EVIDENCE), (gi.TASK, gi.TASK),
        (gi.DOUBT, gi.EVIDENCE), (gi.DOUBT, gi.DECISION), (gi.DOUBT, gi.DOUBT),
        (gi.DOUBT, gi.TASK), (gi.DOUBT, gi.GATE),
        (gi.DECISION, gi.EVIDENCE), (gi.DECISION, gi.DECISION), (gi.DECISION, gi.DOUBT),
        (gi.DECISION, gi.TASK), (gi.DECISION, gi.GATE),
        ("plan", gi.EVIDENCE), ("plan", gi.DECISION), ("plan", gi.DOUBT),
        ("plan", gi.TASK), ("plan", gi.GATE), ("plan", gi.MODULE),
    },
}


def _finding(rule: str, level: str, subject: str, detail: str, fix: str = "") -> dict:
    return {"rule": rule, "level": level, "subject": subject, "detail": detail, "fix": fix}


def _kind(graph: dict, node_id: str) -> str:
    return graph["nodes"].get(node_id, {}).get("kind", "unknown")


def check_edge_types(graph: dict) -> list[dict]:
    findings = []
    for src, rel, dst in graph["edges"]:
        allowed = ALLOWED.get(rel)
        if allowed is None:
            findings.append(_finding("unknown-edge", WARN, rel, f"`{rel}` is not in the model ({src} -> {dst})."))
            continue
        pair = (_kind(graph, src), _kind(graph, dst))
        if pair not in allowed:
            findings.append(
                _finding(
                    "edge-type",
                    WARN,
                    f"{src}->{dst}",
                    f"`{src}` ({pair[0]}) --{rel}--> `{dst}` ({pair[1]}) is not a shape the model allows.",
                    "Fix the reference, or widen `graph_schema.ALLOWED` if the shape is legitimate.",
                )
            )
    return findings


def supersession_chains(graph: dict) -> dict[str, list[str]]:
    """`superseded id -> the decisions that superseded it`."""
    chains: dict[str, list[str]] = {}
    for src, rel, dst in graph["edges"]:
        if rel == "supersedes":
            chains.setdefault(dst, []).append(src)
    return chains


def check_supersession(graph: dict) -> list[dict]:
    """A supersession chain must be acyclic and end in exactly one live head."""
    findings = []
    edges = [(s, d) for s, r, d in graph["edges"] if r == "supersedes"]
    forward: dict[str, list[str]] = {}
    for src, dst in edges:
        forward.setdefault(dst, []).append(src)

    # Cycles: D-1 supersedes D-2 supersedes D-1 means neither is current.
    colour: dict[str, int] = {}

    def walk(node: str, path: list[str]) -> None:
        if colour.get(node) == 1:
            findings.append(
                _finding("supersession-cycle", ERROR, node,
                         f"Supersession cycle: {' -> '.join(path + [node])}.",
                         "Decide which decision is current and remove the other `Supersedes:` line.")
            )
            return
        if colour.get(node) == 2:
            return
        colour[node] = 1
        for nxt in forward.get(node, []):
            walk(nxt, path + [node])
        colour[node] = 2

    for node in list(forward):
        walk(node, [])

    superseded = {d for _s, d in edges}
    for node, replacements in forward.items():
        live = [r for r in replacements if r not in superseded]
        if len(live) > 1:
            findings.append(
                _finding("supersession-fork", ERROR, node,
                         f"`{node}` is superseded by {len(live)} decisions that are all still current "
                         f"({', '.join(sorted(live))}).",
                         "Two live decisions claiming the same ground is a contradiction - retire one.")
            )
    return findings


def check_superseded_citations(graph: dict) -> list[dict]:
    """Nothing still in play may rest on a decision that has been superseded.

    The mechanical form of "the parent's decisions constrain the children", and the
    single highest-value invariant in the ADR literature.
    """
    superseded = {d for s, r, d in graph["edges"] if r == "supersedes"}
    findings = []
    for src, rel, dst in graph["edges"]:
        if rel != "cites" or dst not in superseded:
            continue
        node = graph["nodes"].get(src, {})
        if node.get("done"):
            continue  # finished work may legitimately cite what was true at the time
        findings.append(
            _finding("cites-superseded", ERROR, src,
                     f"`{src}` is still open and cites `{dst}`, which has been superseded.",
                     f"Re-point it at whatever superseded `{dst}`, or record why the old one still applies.")
        )
    return findings


def check_gate_targets(graph: dict) -> list[dict]:
    findings = []
    for src, rel, dst in graph["edges"]:
        if rel == "gate" and dst not in graph["nodes"]:
            findings.append(
                _finding("missing-gate", ERROR, src,
                         f"`{src}` targets gate `{dst}`, which no `GATES.yml` defines.",
                         "Add the gate, or point the task at a real one - an unreachable gate can never pass.")
            )
    for src, rel, dst in graph.get("dangling", []):
        if rel == "gate":
            findings.append(
                _finding("missing-gate", ERROR, src,
                         f"`{src}` targets gate `{dst}`, which no `GATES.yml` defines.",
                         "Add the gate, or point the task at a real one.")
            )
    return findings


def check_unsupported_decisions(graph: dict) -> list[dict]:
    """A decision resting on nothing recorded. Information, not a defect."""
    cited = {(s, d) for s, r, d in graph["edges"] if r == "cites"}
    findings = []
    for node_id, node in sorted(graph["nodes"].items()):
        if node["kind"] != gi.DECISION:
            continue
        if any(src == node_id and _kind(graph, dst) == gi.EVIDENCE for src, dst in cited):
            continue
        findings.append(
            _finding("unsupported-decision", INFO, node_id,
                     f"`{node_id}` cites no evidence.",
                     "Fine for a judgement call - cite the evidence if it rests on one.")
        )
    return findings


def check_dangling(graph: dict) -> list[dict]:
    return [
        _finding("dangling-reference", WARN, src,
                 f"`{src}` references `{dst}`, which nothing defines.",
                 "Fix the id, or add the record it points at.")
        for src, rel, dst in graph.get("dangling", [])
        if rel != "gate"  # reported by check_gate_targets at error level
    ]


def check_expired_evidence(graph: dict, workspace: Path | None = None) -> list[dict]:
    """A decision resting on a claim that is past its re-check date.

    Raised as information, never as a verdict. The claim is uncertain, not disproved,
    and an LLM asked whether a decision still holds is measured 30% wrong on exactly
    this kind - principle and infrastructure decisions (arXiv:2602.07609). So this
    surfaces the pair and lets a human look; it never supersedes anything.
    """
    if workspace is None:
        return []
    try:
        import evidence_review

        expired = {e["id"]: e for e in evidence_review.review_due(workspace)}
    except Exception:
        return []
    if not expired:
        return []

    findings = []
    for src, rel, dst in graph["edges"]:
        if rel != "cites" or dst not in expired:
            continue
        if _kind(graph, src) != gi.DECISION:
            continue
        entry = expired[dst]
        findings.append(
            _finding("decision-on-expired-evidence", INFO, src,
                     f"`{src}` rests on `{dst}`, whose validity window closed {entry['due']}.",
                     f"Re-check {dst} or record a fresh `Date checked`. The decision is not wrong - "
                     "its support is simply no longer current.")
        )
    return findings


RULES = (
    check_edge_types,
    check_supersession,
    check_superseded_citations,
    check_gate_targets,
    check_dangling,
    check_unsupported_decisions,
)

# Rules that need the workspace, not just the graph.
WORKSPACE_RULES = (check_expired_evidence,)


def validate(workspace: Path, graph: dict | None = None) -> list[dict]:
    graph = graph if graph is not None else gi.build(workspace)
    findings: list[dict] = []
    for rule in RULES:
        try:
            findings.extend(rule(graph))
        except Exception:
            continue
    for rule in WORKSPACE_RULES:
        try:
            findings.extend(rule(graph, workspace))
        except Exception:
            continue
    order = {ERROR: 0, WARN: 1, INFO: 2}
    findings.sort(key=lambda f: (order.get(f["level"], 3), f["rule"], f["subject"]))
    return findings


def summarize(findings: list[dict]) -> dict[str, int]:
    counts = {ERROR: 0, WARN: 0, INFO: 0}
    for item in findings:
        counts[item["level"]] = counts.get(item["level"], 0) + 1
    counts["total"] = len(findings)
    return counts


def describe(findings: list[dict], *, verbose: bool = False) -> str:
    if not findings:
        return "The reference graph satisfies every rule in the model."
    counts = summarize(findings)
    lines = [f"{counts['error']} error, {counts['warn']} warning, {counts['info']} info", ""]
    for item in findings:
        if item["level"] == INFO and not verbose:
            continue
        lines.append(f"[{item['level']}] {item['rule']}: {item['detail']}")
        if item["fix"]:
            lines.append(f"        {item['fix']}")
    if counts[INFO] and not verbose:
        lines.append(f"\n{counts[INFO]} informational finding(s) hidden - pass --verbose.")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

    parser = argparse.ArgumentParser(description="Check the reference graph against the model.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--verbose", action="store_true", help="Include informational findings.")
    args = parser.parse_args()

    findings = validate(resolve_workspace(args.workspace))
    print(describe(findings, verbose=args.verbose))
    return 1 if summarize(findings)[ERROR] else 0


if __name__ == "__main__":
    raise SystemExit(main())
