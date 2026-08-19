#!/usr/bin/env python3
"""What a sub-product still owes its parent an answer about, computed on demand.

The main product used to *stage* each finding as a note in the sub-product's
`.loop/pending/`, and the user had to remember to run `loop pending list` over
there. Two things were wrong with that: a queued note is a frozen copy of derived
state and cannot self-heal, and nothing in the sub-product's own commands ever
surfaced it.

This computes the same findings from the sub-product's side, filtered to itself
and to what the user has not already decided (`finding_log`). Nothing is stored,
so a disagreement that is resolved upstream simply stops appearing.

`ask` vs `report` is the whole point of the split: only errors and genuine upstream
changes are worth interrupting for. Opening `/product-develop` with fifteen
questions is how the old queue died.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import finding_log
from workspace_utils import resolve_workspace

# Kinds that are the sub-product's business. Map-level findings (`unbuilt-row`,
# `missing-product-map`) belong to whoever owns the master plan.
SUB_KINDS = (
    "decision-conflict",
    "deployment-conflict",
    "contract-gap",
    "dependency-gap",
    "unmapped-sub",
    "uninitialized-sub",
    "parent-added",
    "parent-changed",
    "parent-removed",
)


def drop_legacy_queue(workspace: Path) -> int:
    """Remove staged drift notes left by the old approval queue.

    Every one of them is a frozen copy of a finding that is now recomputed. A note
    whose finding is still live will simply be raised again, in the session, with a
    recommended answer; a note whose finding is gone was pure noise - this repo's
    own sub-product was holding six of those for conflicts that no longer existed.

    Only notes this harness staged are touched, identified by `origin.finding_id`.
    """
    import pending_writes as pw

    removed = 0
    for item in pw.list_pending(workspace):
        if item.get("kind") != "file":
            continue
        if not (item.get("origin") or {}).get("finding_id"):
            continue
        try:
            Path(item["_path"]).unlink(missing_ok=True)
            removed += 1
        except OSError:
            continue
    return removed


def _parent_and_self(workspace: Path) -> tuple[Path, dict] | None:
    """This workspace's parent, and its own entry in that parent's child list."""
    from workspace_tree import data_dir_for, product_folder, read_meta, resolve_children

    folder = product_folder(workspace)
    stored = read_meta(workspace).get("parent")
    if folder is None or not stored:
        return None
    parent_folder = (folder / str(stored)).resolve()
    if not parent_folder.is_dir():
        return None
    parent_ws = data_dir_for(parent_folder)

    for child in resolve_children(parent_ws):
        if child.get("folder") and Path(child["folder"]).resolve() == folder.resolve():
            return parent_ws, child
    return None


def findings_for(workspace: Path) -> list[dict]:
    """Every live finding the parent has about this sub-product."""
    import hierarchy_drift as drift

    pair = _parent_and_self(workspace)
    if pair is None:
        return []
    parent_ws, child = pair
    name = child.get("name")
    try:
        all_findings = drift.check_children(parent_ws, [child])
    except Exception:
        return []
    return [f for f in all_findings if f.get("sub") == name and f.get("kind") in SUB_KINDS]


def inbox(workspace: Path) -> dict:
    """Unresolved findings, split into what to ask about and what to just report."""
    result = {
        "parent": None,
        "ask": [],
        "report": [],
        "resolved": finding_log.summarize(workspace),
        "total": 0,
    }
    pair = _parent_and_self(workspace)
    if pair is None:
        return result

    parent_ws, _child = pair
    result["parent"] = parent_ws.parent.name if parent_ws.name == ".loop-engineer" else parent_ws.name

    live = findings_for(workspace)
    finding_log.prune(workspace, live)
    open_findings = finding_log.unresolved(workspace, live)

    for item in open_findings:
        target = "ask" if (item.get("level") == drift_error() or item.get("stage")) else "report"
        result[target].append(item)
    result["total"] = len(open_findings)
    return result


def drift_error() -> str:
    import hierarchy_drift as drift

    return drift.LEVEL_ERROR


def suggestion(finding: dict) -> tuple[str, str]:
    """A recommended answer and the reason for it.

    Deterministic, from the finding's kind and level - never model-generated
    (`AGENTS.md` non-negotiable #4). The agent presents this as the default so the
    user can move fast; it is a suggestion, not a decision.
    """
    kind = str(finding.get("kind", ""))

    if kind in ("parent-added", "parent-changed"):
        return (
            finding_log.ACCEPTED,
            "A platform-level constraint changed. The parent owns it, so the usual "
            "answer is to fold it in here - decline only if this sub-product has a "
            "constraint the platform decision did not account for.",
        )
    if kind == "parent-removed":
        return (
            finding_log.DEFERRED,
            "The platform dropped a constraint this sub-product may still be built "
            "around. Nothing breaks today; check it before the next release slice.",
        )
    if kind in ("decision-conflict", "deployment-conflict"):
        return (
            finding_log.ACCEPTED,
            "Parent decisions are constraints on sub-products, so the usual answer is "
            "to change this side. Decline if this plan has evidence the platform "
            "decision is wrong - then fix it in the master plan.",
        )
    if kind == "contract-gap":
        return (
            finding_log.ACCEPTED,
            "The platform defined an integration this plan does not cover. It has to "
            "be planned here before build, or the contract has no owner.",
        )
    if kind == "dependency-gap":
        return (
            finding_log.DEFERRED,
            "The map says this sub-product depends on something its plan never "
            "mentions. Usually a planning gap rather than a live problem.",
        )
    if kind == "unmapped-sub":
        return (
            finding_log.DECLINED,
            "This is the master plan's gap, not this workspace's - the map needs a row "
            "for this sub-product. Nothing to change here.",
        )
    return (finding_log.DEFERRED, "No default for this kind - decide with the user.")


def question(finding: dict) -> dict:
    """One finding rendered as a question with a recommended answer."""
    recommended, why = suggestion(finding)
    return {
        "id": finding.get("id"),
        "kind": finding.get("kind"),
        "level": finding.get("level"),
        "question": finding.get("detail"),
        "context": finding.get("note"),
        "recommended": recommended,
        "why": why,
        "options": list(finding_log.DECISIONS),
    }


def manifest_block(workspace: Path, data: dict | None = None) -> list[str]:
    """Lines for plan/SESSION_MANIFEST.md, so every command sees the inbox."""
    data = data if data is not None else inbox(workspace)
    if not data.get("parent") or not data.get("total"):
        return []

    lines = [
        "",
        "## Parent findings - answer these first",
        "",
        f"`{data['parent']}` (the main product) and this plan disagree on "
        f"{data['total']} point(s). Resolve them **before** planning or building on top:",
        "",
    ]
    if data["ask"]:
        lines.append(f"- **{len(data['ask'])} needing a decision** - ask the user about each, one at a time,")
        lines.append("  with the recommended answer and what it costs. Record each answer with")
        lines.append("  `loop findings resolve <id> <accepted|declined|deferred>`.")
    if data["report"]:
        lines.append(f"- **{len(data['report'])} for information** - mention, do not interrogate.")
    lines.extend(
        [
            "",
            "Run `loop findings list` for the full text, or `loop findings ask` for the",
            "questions with recommended answers. A finding is a *disagreement*, not a",
            "verdict - the master plan may be the side that is wrong.",
            "",
        ]
    )
    return lines


def describe(data: dict, *, verbose: bool = False) -> str:
    if not data.get("parent"):
        return "No parent product - this workspace has no findings to answer."
    if not data.get("total"):
        counts = data.get("resolved", {})
        settled = sum(counts.values())
        tail = f" ({settled} previously resolved)" if settled else ""
        return f"Nothing open from parent `{data['parent']}`{tail}."

    lines = [f"Parent `{data['parent']}`: {data['total']} open finding(s)", ""]
    for label, items in (("Needs a decision", data["ask"]), ("For information", data["report"])):
        if not items:
            continue
        lines.append(f"{label}:")
        for item in items:
            lines.append(f"  [{item['level']}] {item['kind']}  ({item['id']})")
            lines.append(f"      {item['detail']}")
            if verbose:
                recommended, why = suggestion(item)
                lines.append(f"      suggested: {recommended} - {why}")
            lines.append("")
    return "\n".join(lines).rstrip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Findings this sub-product owes its parent an answer about.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")

    listing = sub.add_parser("list", help="Open findings from the parent product.")
    listing.add_argument("--verbose", action="store_true", help="Include the recommended answer for each.")

    sub.add_parser("ask", help="Open findings as questions with recommended answers.")

    resolve_p = sub.add_parser("resolve", help="Record a decision about one finding.")
    resolve_p.add_argument("finding_id")
    resolve_p.add_argument("decision", choices=list(finding_log.DECISIONS))
    resolve_p.add_argument("--note", default="")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    cmd = args.cmd or "list"

    if cmd == "resolve":
        live = findings_for(workspace)
        match = next((f for f in live if f.get("id") == args.finding_id), None)
        if match is None:
            print(f"No live finding with id {args.finding_id!r}. Run `loop findings list`.")
            return 1
        finding_log.resolve(workspace, match, args.decision, note=args.note)
        print(f"Recorded: {args.finding_id} -> {args.decision}")
        remaining = inbox(workspace)["total"]
        print(f"{remaining} finding(s) still open.")
        return 0

    data = inbox(workspace)

    if cmd == "ask":
        if not data["ask"]:
            print(describe(data))
            return 0
        for index, item in enumerate(data["ask"], start=1):
            q = question(item)
            print(f"[{index}/{len(data['ask'])}] {q['kind']}  ({q['id']})")
            print(f"  {q['question']}")
            print(f"  Recommended: {q['recommended']} - {q['why']}")
            print(f"  Options: {', '.join(q['options'])}")
            print()
        return 0

    print(describe(data, verbose=getattr(args, "verbose", False)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
