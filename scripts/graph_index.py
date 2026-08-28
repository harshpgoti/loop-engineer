#!/usr/bin/env python3
"""One index of how a workspace's records reference each other.

The graph already exists - it is just re-derived, partially and slightly
differently, in six places:

    task_context.dependencies          TASK -> TASK      (blocked_by)
    doubts.supersessions               D    -> DQ        (Supersedes:)
    state_archive.live_references      * -> E            (citations, by regex)
    dependency_ledger.resolve          MAP  -> MAP       (Depends on)
    hierarchy_drift.parse_depends      MAP  -> MAP       (again)
    subproducts_report                 task counts

Each answers a slice of the same question and none of them can answer the others'.
This builds the whole thing once, deterministically, from the ID conventions the
files already use (`AGENTS.md` non-negotiable #4 - parsers, never a model).

It is deliberately *additive*: nothing is required to use it. Consumers migrate one
at a time, and the existing parsers keep working until they do.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

GRAPH_FILE = ".loop/graph.json"
HISTORY_FILE = ".loop/graph-history.json"

# How an edge left the graph. The distinction is the point: a bi-temporal store that
# collapses these cannot answer "was that decision defensible when it was made?",
# which is the reason an ADR log exists at all. TGMS (arXiv:2607.10265) measured
# latest-state graphs at 0.000 on exactly this class of question.
RETRACTED = "retracted"  # it was true, the world moved on
CORRECTED = "corrected"  # it was never true, we recorded it wrongly

TASK, GATE, DOUBT, DECISION, EVIDENCE, MODULE = "task", "gate", "doubt", "decision", "evidence", "module"

# Order matters: `DQ-` must be tested before `D-`.
PREFIXES = (
    ("DQ-", DOUBT),
    ("TASK-", TASK),
    ("TEMPLATE-", TASK),
    ("G-", GATE),
    ("E-", EVIDENCE),
    ("ADR-", DECISION),
    ("D-", DECISION),
)

# An identifier as it appears in prose: `E-M-012`, `DQ-007`, `TASK-PR-A`, `G-EVAL-01`.
REF = re.compile(r"\b((?:DQ|TASK|TEMPLATE|ADR|G|D|E)(?:-[A-Z0-9]+)+)\b")

DONE_STATUSES = ("completed", "done", "complete", "passed", "resolved")


def graph_path(workspace: Path) -> Path:
    return workspace / GRAPH_FILE


def history_path(workspace: Path) -> Path:
    return workspace / HISTORY_FILE


def edge_key(edge: list[str]) -> str:
    return "|".join(edge)


def read_history(workspace: Path) -> dict:
    path = history_path(workspace)
    if not path.exists():
        return {"edges": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"edges": {}}
    return data if isinstance(data.get("edges"), dict) else {"edges": {}}


def record_history(workspace: Path, graph: dict, *, today: str | None = None) -> dict:
    """Fold the current parse into the edge log. Never deletes; only closes intervals.

    A single parse sees only the present, so history has to be accumulated across
    rebuilds. An edge that has disappeared is treated as **retracted** - the ordinary
    case, where a plan changed. `correct()` is the explicit escape hatch for the other
    case, and it is deliberately not inferred: nothing in a file diff distinguishes
    "we changed our mind" from "that was always wrong".
    """
    from datetime import date

    stamp = today or date.today().isoformat()
    history = read_history(workspace)
    log = history["edges"]
    present = {edge_key(e) for e in graph["edges"]}

    for key in present:
        entry = log.setdefault(key, {"asserted": stamp})
        entry["last_seen"] = stamp
        # Re-asserting an edge reopens it: the plan says this again.
        entry.pop("closed_at", None)
        entry.pop("closed_as", None)

    for key, entry in log.items():
        if key in present or entry.get("closed_at"):
            continue
        entry["closed_at"] = stamp
        entry["closed_as"] = RETRACTED

    history["edges"] = log
    history_path(workspace).parent.mkdir(parents=True, exist_ok=True)
    history_path(workspace).write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return history


# Edge churn worth remembering, in days. Beyond this a closed edge is history nobody
# queries: the *decision* about a finding lives in `finding_log`, and `as-of` past
# this horizon is answering about a plan that no longer resembles the current one.
HISTORY_RETENTION_DAYS = 400


def prune_history(workspace: Path, *, keep_days: int = HISTORY_RETENTION_DAYS, today: str | None = None) -> int:
    """Drop long-closed edges. Open edges are never touched, whatever their age."""
    from datetime import date, datetime, timedelta

    stamp = today or date.today().isoformat()
    try:
        cutoff = (datetime.strptime(stamp, "%Y-%m-%d").date() - timedelta(days=keep_days)).isoformat()
    except ValueError:
        return 0

    history = read_history(workspace)
    log = history["edges"]
    stale = [k for k, v in log.items() if v.get("closed_at") and v["closed_at"] < cutoff]
    for key in stale:
        del log[key]
    if stale:
        history["edges"] = log
        history_path(workspace).write_text(
            json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return len(stale)


def correct(workspace: Path, edge: list[str], *, note: str = "") -> bool:
    """Mark an edge as never having been valid, rather than no longer valid."""
    from datetime import date

    history = read_history(workspace)
    entry = history["edges"].get(edge_key(edge))
    if entry is None:
        return False
    entry["closed_at"] = date.today().isoformat()
    entry["closed_as"] = CORRECTED
    if note:
        entry["note"] = note
    history_path(workspace).write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def as_of(workspace: Path, when: str, graph: dict | None = None) -> dict:
    """The graph as it stood on `when` (YYYY-MM-DD).

    Answers "what did this plan believe in March?" - which no parse of the current
    files can, however good the parser.
    """
    graph = graph if graph is not None else build(workspace)
    log = read_history(workspace)["edges"]
    edges: list[list[str]] = []
    for key, entry in log.items():
        if entry.get("asserted", "9999") > when:
            continue
        closed = entry.get("closed_at")
        # A corrected edge was never valid, so it is absent from every past view.
        if entry.get("closed_as") == CORRECTED:
            continue
        if closed and closed <= when:
            continue
        parts = key.split("|")
        if len(parts) == 3:
            edges.append(parts)
    nodes = {n for e in edges for n in (e[0], e[2])}
    return {
        "nodes": {n: graph["nodes"].get(n, {"kind": "unknown", "label": "", "done": True}) for n in nodes},
        "edges": sorted(edges),
        "as_of": when,
    }


def closed_edges(workspace: Path, *, kind: str | None = None) -> list[dict]:
    """Edges no longer asserted, with how and when they closed."""
    out = []
    for key, entry in read_history(workspace)["edges"].items():
        if not entry.get("closed_at"):
            continue
        if kind and entry.get("closed_as") != kind:
            continue
        parts = key.split("|")
        if len(parts) == 3:
            out.append({"edge": parts, "closed_at": entry["closed_at"], "closed_as": entry.get("closed_as", RETRACTED)})
    return sorted(out, key=lambda item: item["closed_at"], reverse=True)


def kind_of(node_id: str) -> str | None:
    for prefix, kind in PREFIXES:
        if node_id.startswith(prefix):
            return kind
    return None


def _read(path: Path, limit: int | None = 200_000) -> str:
    if not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text if limit is None else text[:limit]
    except OSError:
        return ""


def _refs(text: str, *, exclude: str = "") -> list[str]:
    return sorted({r for r in REF.findall(text or "") if r != exclude and kind_of(r)})


# ---------------------------------------------------------------------------
# extraction - one function per source file
# ---------------------------------------------------------------------------


def _sections(text: str) -> list[tuple[str, str]]:
    """`(id, body)` for every `### ID: title` block."""
    heading = re.compile(r"^#{2,4}\s+((?:DQ|TASK|TEMPLATE|ADR|G|D|E)(?:-[A-Z0-9]+)+)\s*[:.]?\s*(.*)$")
    out: list[tuple[str, str]] = []
    current_id, buffer = None, []
    for line in text.splitlines():
        match = heading.match(line.strip())
        if match:
            if current_id:
                out.append((current_id, "\n".join(buffer)))
            current_id, buffer = match.group(1), [match.group(2)]
            continue
        if current_id:
            buffer.append(line)
    if current_id:
        out.append((current_id, "\n".join(buffer)))
    return out


def _from_tasks(workspace: Path, nodes: dict, edges: list) -> None:
    try:
        from task_context import parse_tasks
    except ImportError:
        return
    for task in parse_tasks(workspace):
        node_id = task["id"]
        status = str(task.get("status", "")).lower()
        nodes[node_id] = {
            "kind": TASK,
            "label": task.get("title", ""),
            "status": status,
            "done": status in DONE_STATUSES,
        }
        blockers = task.get("blocked_by") or []
        if isinstance(blockers, str):
            blockers = [blockers]
        for blocker in blockers:
            edges.append([node_id, "blocked_by", str(blocker).strip()])
        gate = str(task.get("gate", "")).strip()
        if gate:
            edges.append([node_id, "gate", gate])
        # A task body often cites the doubt or evidence that motivated it.
        for ref in _refs("\n".join(task.get("raw", [])), exclude=node_id):
            if kind_of(ref) in (DOUBT, EVIDENCE, DECISION):
                edges.append([node_id, "cites", ref])


# Both shapes occur in real workspaces: `G-INIT-01:` as a mapping key, and
# `- id: G-M-INIT-01` as a list item. Handling only the first parsed zero gates from
# the main product, which then reported every gate reference as a dangling one.
GATE_KEY = re.compile(r"^(G-[A-Z0-9-]+):\s*$")
GATE_ITEM = re.compile(r"^-\s+id:\s*(G-[A-Z0-9-]+)\s*$")


def _from_gates(workspace: Path, nodes: dict, edges: list) -> None:
    text = _read(workspace / "GATES.yml")
    current, status, label = None, "", ""

    def flush() -> None:
        if current:
            nodes[current] = {"kind": GATE, "label": label, "status": status, "done": status in DONE_STATUSES}

    for line in text.splitlines():
        stripped = line.strip()
        match = GATE_KEY.match(stripped) or GATE_ITEM.match(stripped)
        if match:
            flush()
            current, status, label = match.group(1), "", ""
            continue
        if not current:
            continue
        if stripped.startswith("status:"):
            status = stripped.split(":", 1)[1].strip().lower()
        elif stripped.startswith("name:") and not label:
            label = stripped.split(":", 1)[1].strip()
    flush()


def _from_doubts(workspace: Path, nodes: dict, edges: list) -> None:
    try:
        import doubts as doubts_mod
    except ImportError:
        return
    for entry in doubts_mod.parse(workspace):
        nodes[entry.id] = {
            "kind": DOUBT,
            "label": entry.title,
            "status": entry.status,
            "done": entry.status != doubts_mod.OPEN,
            "blocking": entry.blocking,
        }
        body = f"{entry.title} {entry.question} {entry.why} {entry.default} {entry.note}"
        for ref in _refs(body, exclude=entry.id):
            edges.append([entry.id, "cites", ref])


def _from_decisions(workspace: Path, nodes: dict, edges: list) -> None:
    for node_id, body in _sections(_read(workspace / "DECISIONS.md")):
        if kind_of(node_id) != DECISION:
            continue
        title = body.splitlines()[0] if body else ""
        nodes[node_id] = {"kind": DECISION, "label": title.strip(), "status": "recorded", "done": True}
        for line in body.splitlines():
            supersedes = re.match(r"^[-*]\s+\*\*Supersedes:?\*\*:?\s*(.+)$", line.strip(), re.I)
            if supersedes:
                target = supersedes.group(1).strip()
                # "Supersedes: nothing. Extends ..." is explanatory prose, not
                # a supersession edge to the references that follow it.
                if re.match(r"nothing\b", target, re.I):
                    continue
                relation = "amends" if re.match(r"amends?\b", target, re.I) else "supersedes"
                for ref in _refs(target, exclude=node_id):
                    edges.append([node_id, relation, ref])
        for ref in _refs(body, exclude=node_id):
            if kind_of(ref) == EVIDENCE:
                edges.append([node_id, "cites", ref])


def _from_architecture(workspace: Path, nodes: dict, edges: list) -> None:
    """ADRs recorded inside root or scope-owned architecture docs.

    A real workspace defines `### ADR-06-05 - Canada private ingests exports` there
    and cites it from tasks and doubts. Scanning only DECISIONS.md reported five of
    those citations as broken references.
    """
    folders: list[Path] = []
    root_steps = workspace / "plan" / "steps"
    if root_steps.is_dir():
        folders.extend(d for d in root_steps.iterdir() if d.is_dir())
    try:
        from scope_paths import list_scopes

        for scope in list_scopes(workspace):
            folders.append(scope.path)
            if scope.steps_dir.is_dir():
                folders.extend(d for d in scope.steps_dir.iterdir() if d.is_dir())
    except ImportError:
        pass

    for folder in sorted(set(folders), key=lambda d: d.as_posix()):
        for doc in ("architecture.md", "overview.md"):
            for node_id, body in _sections(_read(folder / doc, 60_000)):
                if kind_of(node_id) != DECISION or node_id in nodes:
                    continue
                nodes[node_id] = {
                    "kind": DECISION,
                    "label": (body.splitlines()[0] if body else "").strip(),
                    "status": "recorded",
                    "done": True,
                    "source": (folder / doc).relative_to(workspace).as_posix(),
                }
                for ref in _refs(body, exclude=node_id):
                    if kind_of(ref) == EVIDENCE:
                        edges.append([node_id, "cites", ref])


def _from_evidence(workspace: Path, nodes: dict, edges: list) -> None:
    # Evidence logs are append-only and can exceed the bounded plan-document read.
    # Truncating here creates false dangling references for valid late entries.
    for node_id, body in _sections(_read(workspace / "EVIDENCE_LOG.md", limit=None)):
        if kind_of(node_id) != EVIDENCE:
            continue
        nodes[node_id] = {
            "kind": EVIDENCE,
            "label": (body.splitlines()[0] if body else "").strip(),
            "status": "recorded",
            "done": True,
        }


def _from_live_plan(workspace: Path, nodes: dict, edges: list) -> None:
    """The live plan and handoff as citing nodes.

    Without these the graph under-counts what is in play: `main_plan.md` cites the
    evidence the current strategy rests on, and nothing else points at it. Archiving
    is driven off liveness, so a missing edge here means over-archiving - the failure
    direction that loses information.
    """
    from memory_paths import main_plan_file

    for node_id, path in (("PLAN", main_plan_file(workspace)), ("HANDOFF", workspace / "HANDOFF.md")):
        text = _read(path)
        if not text.strip():
            continue
        nodes[node_id] = {"kind": "plan", "label": path.name, "status": "live", "done": False}
        for ref in _refs(text):
            edges.append([node_id, "cites", ref])


def _from_map(workspace: Path, nodes: dict, edges: list) -> None:
    try:
        from ultraplan_harness import parse_product_map
    except ImportError:
        return
    for row in parse_product_map(workspace):
        node_id = f"MAP-{row['id']}"
        nodes[node_id] = {
            "kind": MODULE,
            "label": row.get("title", ""),
            "status": str(row.get("status", "")).lower(),
            "done": False,
            "type": row.get("type", ""),
        }
        for token in re.split(r"[,;/]| and ", str(row.get("depends", ""))):
            token = token.strip()
            if token.isdigit():
                edges.append([node_id, "depends", f"MAP-{token.zfill(2)}"])


SOURCES = (
    _from_tasks,
    _from_gates,
    _from_doubts,
    _from_decisions,
    _from_architecture,
    _from_evidence,
    _from_live_plan,
    _from_map,
)


# ---------------------------------------------------------------------------
# build + query
# ---------------------------------------------------------------------------


def build(workspace: Path) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[list[str]] = []
    for source in SOURCES:
        try:
            source(workspace, nodes, edges)
        except Exception:
            continue  # a malformed file must never break the index

    # A reference that resolves in the parent or a sub-product is `external`, not
    # broken: `D-M-003 --supersedes--> DQ-007` is the cross-workspace supersession
    # this harness supports on purpose. Only a reference nothing anywhere defines is
    # dangling. Without this the main product reported 40 false broken links.
    known = set(nodes) | _related_ids(workspace)

    seen: set[tuple[str, str, str]] = set()
    kept, external, missing = [], [], []
    for src, rel, dst in edges:
        key = (src, rel, dst)
        if key in seen:
            continue
        seen.add(key)
        if dst in nodes:
            kept.append([src, rel, dst])
        elif dst in known:
            external.append([src, rel, dst])
        else:
            missing.append([src, rel, dst])

    return {
        "nodes": nodes,
        "edges": sorted(kept),
        "external": sorted(external),
        "dangling": sorted(missing),
    }


def _related_ids(workspace: Path) -> set[str]:
    """Node IDs defined in the parent product or in any sub-product."""
    found: set[str] = set()

    # Unified workspaces keep scopes under plan/products rather than as child
    # workspaces. Read them first; hierarchy metadata refresh may be unavailable
    # in a read-only diagnostic invocation.
    try:
        import scope_paths as sp

        for scope in sp.list_scopes(workspace):
            for name in ("DECISIONS.md", "DOUBTS.md", "EVIDENCE_LOG.md", "GATES.yml", "TASKS.yml"):
                limit = None if name == "EVIDENCE_LOG.md" else 60_000
                text = _read(scope.path / name, limit)
                found.update(node_id for node_id, _body in _sections(text))
                found.update(_refs(text))
    except (ImportError, OSError):
        pass

    try:
        from workspace_tree import refresh

        tree = refresh(workspace)
    except Exception:
        tree = {}

    neighbours = [c.get("data_dir") for c in (tree.get("children") or []) if not c.get("missing")]
    parent = (tree.get("parent") or {}).get("data_dir")
    if parent:
        neighbours.append(parent)

    for other in neighbours:
        if not other:
            continue
        for name in ("DECISIONS.md", "DOUBTS.md", "EVIDENCE_LOG.md", "GATES.yml", "TASKS.yml"):
            limit = None if name == "EVIDENCE_LOG.md" else 60_000
            for node_id, _body in _sections(_read(Path(other) / name, limit)):
                found.add(node_id)
            found.update(_refs(_read(Path(other) / name, limit)))

    return found


def write(workspace: Path, graph: dict | None = None) -> Path:
    graph = graph if graph is not None else build(workspace)
    path = graph_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def out_edges(graph: dict, node_id: str) -> list[list[str]]:
    return [e for e in graph["edges"] if e[0] == node_id]


def in_edges(graph: dict, node_id: str) -> list[list[str]]:
    return [e for e in graph["edges"] if e[2] == node_id]


def live_nodes(graph: dict) -> set[str]:
    """Nodes representing work still in play: unfinished tasks and open doubts."""
    return {nid for nid, n in graph["nodes"].items() if not n.get("done")}


def reachable_from(graph: dict, roots: set[str], *, depth: int = 3) -> set[str]:
    """Everything the live work points at, transitively - the live frontier.

    This is `state_archive.live_references` done properly: it follows citations
    through decisions, instead of scraping IDs out of four files' raw text.
    """
    seen = set(roots)
    frontier = set(roots)
    for _ in range(max(depth, 0)):
        nxt: set[str] = set()
        for node in frontier:
            for _src, _rel, dst in out_edges(graph, node):
                if dst not in seen:
                    seen.add(dst)
                    nxt.add(dst)
        if not nxt:
            break
        frontier = nxt
    return seen


def orphans(graph: dict) -> dict[str, list[str]]:
    """Records nothing references - what the plan is carrying but not using.

    A new capability: today an evidence entry cited by nothing, or a gate no task
    targets, is invisible. Reported as information, never as an error - an orphan is
    a candidate for compaction or a sign of a missing link, not a defect by itself.
    """
    referenced = {e[2] for e in graph["edges"]}
    found: dict[str, list[str]] = {}
    for node_id, node in graph["nodes"].items():
        if node_id in referenced or out_edges(graph, node_id):
            continue
        found.setdefault(node["kind"], []).append(node_id)
    return {k: sorted(v) for k, v in sorted(found.items())}


def dangling(graph: dict) -> list[list[str]]:
    """Edges pointing at an ID no file defines - a broken cross-reference."""
    return graph.get("dangling", [])


def subgraph(graph: dict, node_id: str, *, depth: int = 1) -> dict:
    """One node and its neighbourhood - the shape `BUILD_CONTEXT.md` renders.

    Depth 1 by default, expanded on demand. RepoGraph's ablation (arXiv:2410.14684)
    measured 2-hop context as *worse* than 1-hop on SWE-bench-Lite - 26.00% vs
    29.67% resolve rate - because the extra hop adds more noise than signal. Take
    the second hop deliberately, never by default.
    """
    seen = {node_id}
    frontier = {node_id}
    for _ in range(max(depth, 0)):
        nxt: set[str] = set()
        for node in frontier:
            for edge in out_edges(graph, node) + in_edges(graph, node):
                for end in (edge[0], edge[2]):
                    if end not in seen:
                        seen.add(end)
                        nxt.add(end)
        if not nxt:
            break
        frontier = nxt
    return {
        "nodes": {n: graph["nodes"][n] for n in seen if n in graph["nodes"]},
        "edges": [e for e in graph["edges"] if e[0] in seen and e[2] in seen],
    }


def summarize(graph: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in graph["nodes"].values():
        counts[node["kind"]] = counts.get(node["kind"], 0) + 1
    counts["edges"] = len(graph["edges"])
    counts["external"] = len(graph.get("external", []))
    counts["dangling"] = len(graph.get("dangling", []))
    return counts


def describe(graph: dict) -> str:
    counts = summarize(graph)
    order = [k for k in (TASK, GATE, DOUBT, DECISION, EVIDENCE, MODULE) if k in counts]
    lines = [
        "  ".join(f"{counts[k]} {k}" for k in order),
        f"{counts['edges']} edge(s), {counts['external']} cross-workspace, "
        f"{counts['dangling']} dangling",
        "",
    ]
    by_rel: dict[str, int] = {}
    for _s, rel, _d in graph["edges"]:
        by_rel[rel] = by_rel.get(rel, 0) + 1
    for rel, count in sorted(by_rel.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {count:4d}  {rel}")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

    parser = argparse.ArgumentParser(description="Index how this workspace's records reference each other.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("build", help="Write .loop/graph.json and fold this parse into the edge log.")
    sub.add_parser("stats", help="Node and edge counts.")
    sub.add_parser("orphans", help="Records nothing references.")
    sub.add_parser("dangling", help="References to IDs no file defines.")
    sub.add_parser("closed", help="Edges no longer asserted, and how they closed.")
    show = sub.add_parser("show", help="One node and its neighbourhood.")
    show.add_argument("node_id")
    show.add_argument("--depth", type=int, default=1)
    asof = sub.add_parser("as-of", help="The graph as it stood on a date (YYYY-MM-DD).")
    asof.add_argument("date")
    corr = sub.add_parser("correct", help="Mark an edge as never having been valid.")
    corr.add_argument("src")
    corr.add_argument("rel")
    corr.add_argument("dst")
    corr.add_argument("--note", default="")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    graph = build(workspace)
    cmd = args.cmd or "stats"

    if cmd == "build":
        print(f"Wrote {write(workspace, graph)}")
        record_history(workspace, graph)
        print(describe(graph))
        return 0

    if cmd == "closed":
        closed = closed_edges(workspace)
        if not closed:
            print("No edge has been withdrawn yet.")
            return 0
        for item in closed:
            src, rel, dst = item["edge"]
            print(f"{item['closed_at']}  {item['closed_as']:9} {src} --{rel}--> {dst}")
        return 0

    if cmd == "as-of":
        view = as_of(workspace, args.date, graph)
        print(f"As of {args.date}: {len(view['nodes'])} node(s), {len(view['edges'])} edge(s)")
        for src, rel, dst in view["edges"][:40]:
            print(f"  {src} --{rel}--> {dst}")
        return 0

    if cmd == "correct":
        ok = correct(workspace, [args.src, args.rel, args.dst], note=args.note)
        print("Recorded as never-valid." if ok else "No such edge in the history log.")
        return 0 if ok else 1

    if cmd == "orphans":
        found = orphans(graph)
        if not found:
            print("Nothing orphaned - every record is referenced or references something.")
            return 0
        for kind, ids in found.items():
            print(f"{kind} ({len(ids)}): {', '.join(ids)}")
        return 0

    if cmd == "dangling":
        broken = dangling(graph)
        if not broken:
            print("No dangling references.")
            return 0
        for src, rel, dst in broken:
            print(f"{src} --{rel}--> {dst}   (no record defines {dst})")
        return 0

    if cmd == "show":
        view = subgraph(graph, args.node_id, depth=args.depth)
        if args.node_id not in view["nodes"]:
            print(f"No record with id {args.node_id!r}.")
            return 1
        node = view["nodes"][args.node_id]
        print(f"{args.node_id}  [{node['kind']}/{node.get('status', '')}]  {node.get('label', '')}")
        # Only edges incident to the focus node - the subgraph also carries the
        # neighbours' own edges, which are noise when reading one record.
        seen: set[tuple[str, str, str]] = set()
        for src, rel, dst in view["edges"]:
            if args.node_id not in (src, dst) or (src, rel, dst) in seen:
                continue
            seen.add((src, rel, dst))
            other = dst if src == args.node_id else src
            arrow = "->" if src == args.node_id else "<-"
            label = view["nodes"].get(other, {}).get("label", "")
            print(f"  {arrow} {rel:12} {other:14} {label[:60]}")
        return 0

    print(describe(graph))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
