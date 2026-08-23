#!/usr/bin/env python3
"""The evals loop: recorded runs, regressions, and error analysis that decides what next.

The harness had gates, QA and release checks - all traditional software checks - and
one line in `agent-builder` saying "wire evals: golden cases under `agent/evals/`".
So a real product ended up with 52 golden cases across three files, an eval gate, and
no way to record what a run scored, notice when a score dropped, or let failures decide
what to build next. The discipline was there; the loop was not.

This deliberately does **not** define a case schema. The cases in that workspace carry
domain fields - `expected_root_cause`, `must_refuse_workflows`, `requires_human_approval` -
that no generic format would have predicted, and a harness that insisted on its own
shape would just be ignored. Any JSON list of objects with an `id` is a suite. What the
harness owns is the part that is the same for every product: the loop around them.

Three rules, taken from the same places as the rest of this harness:

- **Deterministic before judged** (`AGENTS.md` #4). A check that can be code is code. An
  LLM-as-judge verdict is accepted, but it must carry a written rationale, because a
  judge verdict with no reasoning is unreviewable and cannot be argued with later.
- **Report, never auto-act.** A regression is surfaced with the cases that broke; it
  does not roll anything back or edit a plan.
- **Scores settle.** Run records are compacted like everything else here: the last
  `KEEP_RUNS` stay whole, older ones keep their scores and lose their per-case detail.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

EVAL_DIRS = ("agent/evals", "evals", "agent/eval")
RUNS_DIR = "runs"
ANALYSIS_FILE = "plan/EVAL_ANALYSIS.md"

# Below this, a scored run does not satisfy an eval gate. Deliberately not 100%:
# a suite nobody can ever pass gets disabled, and a suite everyone always passes
# has stopped measuring anything.
DEFAULT_THRESHOLD = 0.9

# Run records kept in full. Older ones keep their score and drop per-case detail.
KEEP_RUNS = 10

VERDICT_KINDS = ("deterministic", "judge", "human")


def eval_root(workspace: Path) -> Path | None:
    """Where this product keeps its cases, whatever it chose to call it."""
    product = workspace.parent if workspace.name == ".loop-engineer" else workspace
    for base in (product, workspace):
        for rel in EVAL_DIRS:
            candidate = base / rel
            if candidate.is_dir():
                return candidate
    return None


def runs_dir(workspace: Path) -> Path | None:
    root = eval_root(workspace)
    return root / RUNS_DIR if root else None


# ---------------------------------------------------------------------------
# cases
# ---------------------------------------------------------------------------


def discover_cases(workspace: Path) -> dict[str, dict]:
    """Every case id found, with the file it came from and its own fields.

    Any JSON list of objects carrying an `id` counts. Files under `runs/` are
    excluded - a run record is not a case, and reading one as a case would make
    the suite appear to grow every time it is exercised.
    """
    root = eval_root(workspace)
    if root is None:
        return {}

    cases: dict[str, dict] = {}
    for path in sorted(root.rglob("*.json")):
        if RUNS_DIR in path.relative_to(root).parts:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        items = data if isinstance(data, list) else data.get("cases", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                cases.setdefault(
                    str(item["id"]),
                    {"suite": path.name, "category": item.get("category") or item.get("market") or "", "case": item},
                )
    return cases


def suites(workspace: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in discover_cases(workspace).values():
        counts[entry["suite"]] = counts.get(entry["suite"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# runs
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def record_run(workspace: Path, results: dict[str, dict], *, model: str = "", notes: str = "") -> Path | None:
    """Persist one scored run.

    `results` maps case id -> {"pass": bool, "kind": deterministic|judge|human,
    "why": str}. A failing judged verdict without a `why` is rejected rather than
    stored: an unreviewable verdict is worse than no verdict, because it looks like
    evidence.
    """
    directory = runs_dir(workspace)
    if directory is None:
        return None

    cleaned: dict[str, dict] = {}
    for case_id, verdict in results.items():
        kind = str(verdict.get("kind", "deterministic")).lower()
        if kind not in VERDICT_KINDS:
            kind = "deterministic"
        passed = bool(verdict.get("pass"))
        why = str(verdict.get("why", "")).strip()
        if kind in ("judge", "human") and not passed and not why:
            raise ValueError(f"{case_id}: a failing {kind} verdict must record why")
        cleaned[str(case_id)] = {"pass": passed, "kind": kind, "why": why}

    passed = sum(1 for v in cleaned.values() if v["pass"])
    run = {
        "id": _now(),
        "model": model,
        "total": len(cleaned),
        "passed": passed,
        "score": round(passed / len(cleaned), 4) if cleaned else 0.0,
        "notes": notes.strip(),
        "results": cleaned,
    }

    directory.mkdir(parents=True, exist_ok=True)
    # Two runs in the same instant must be distinguishable *by id*, not just by
    # filename. Disambiguating only the path leaves both records carrying the same id,
    # so ordering them falls back to filename order - where a `-2` suffix sorts before
    # `.json` and silently reverses which run counts as "previous". A comparison that
    # can invert is worse than no comparison, so the suffix goes into the id too.
    stem = run["id"].replace(":", "-").replace(".", "-")
    path = directory / f"{stem}.json"
    suffix = 2
    while path.exists():
        run["id"] = f"{run['id']}#{suffix}"
        path = directory / f"{stem}-{suffix}.json"
        suffix += 1
    path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compact_runs(workspace)
    return path


def runs(workspace: Path) -> list[dict]:
    directory = runs_dir(workspace)
    if directory is None or not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(out, key=lambda r: str(r.get("id", "")))


def latest_run(workspace: Path) -> dict | None:
    found = runs(workspace)
    return found[-1] if found else None


def compact_runs(workspace: Path, *, keep: int = KEEP_RUNS) -> int:
    """Older runs keep their score and lose per-case detail. Same rule as everywhere.

    The score is the trend; the per-case detail is only interesting while it is recent
    enough to act on. Without this, a suite exercised in CI writes an unbounded pile of
    per-case records into the product repo.
    """
    directory = runs_dir(workspace)
    if directory is None or not directory.is_dir():
        return 0
    paths = sorted(directory.glob("*.json"))
    trimmed = 0
    for path in paths[: max(len(paths) - keep, 0)]:
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not run.get("results"):
            continue
        run["failed_ids"] = sorted(cid for cid, v in run["results"].items() if not v.get("pass"))
        run["results"] = {}
        run["compacted"] = True
        path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        trimmed += 1
    return trimmed


# ---------------------------------------------------------------------------
# regression
# ---------------------------------------------------------------------------


def compare(previous: dict | None, current: dict | None) -> dict:
    """What changed between two runs. Regressions are the point of the whole loop."""
    empty = {"regressed": [], "fixed": [], "new": [], "dropped": [], "delta": 0.0}
    if not current:
        return empty
    if not previous or not previous.get("results"):
        return dict(empty, new=sorted(current.get("results", {})), delta=current.get("score", 0.0))

    before, after = previous["results"], current.get("results", {})
    return {
        "regressed": sorted(c for c in after if c in before and before[c].get("pass") and not after[c].get("pass")),
        "fixed": sorted(c for c in after if c in before and not before[c].get("pass") and after[c].get("pass")),
        "new": sorted(c for c in after if c not in before),
        "dropped": sorted(c for c in before if c not in after),
        "delta": round(current.get("score", 0.0) - previous.get("score", 0.0), 4),
    }


def regressions(workspace: Path) -> dict:
    found = runs(workspace)
    if len(found) < 2:
        return compare(None, found[-1] if found else None)
    return compare(found[-2], found[-1])


# ---------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------


def gate_status(workspace: Path, *, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Whether a recorded run satisfies an eval gate, and why not when it does not."""
    cases = discover_cases(workspace)
    run = latest_run(workspace)
    if not cases:
        return {"ok": False, "reason": "no eval cases found", "score": None, "coverage": 0.0}
    if not run:
        return {
            "ok": False,
            "reason": f"{len(cases)} case(s) exist but no run has ever been recorded",
            "score": None,
            "coverage": 0.0,
        }

    scored = set(run.get("results") or run.get("failed_ids") or [])
    coverage = round(len(scored & set(cases)) / len(cases), 4) if run.get("results") else 0.0
    score = run.get("score", 0.0)

    if run.get("results") and coverage < 1.0:
        missing = len(cases) - len(scored & set(cases))
        return {"ok": False, "reason": f"{missing} case(s) not exercised in the last run", "score": score, "coverage": coverage}
    if score < threshold:
        return {"ok": False, "reason": f"score {score:.0%} is below the {threshold:.0%} bar", "score": score, "coverage": coverage}
    return {"ok": True, "reason": f"score {score:.0%} over {len(cases)} case(s)", "score": score, "coverage": coverage}


# ---------------------------------------------------------------------------
# error analysis
# ---------------------------------------------------------------------------


def failure_groups(workspace: Path) -> dict[str, list[dict]]:
    """Failing cases grouped by their own category, worst group first.

    This is the input to error analysis: not "4 cases failed" but "every failure is
    in the Ontario pack", which is a decision about what to build next.
    """
    run = latest_run(workspace)
    if not run or not run.get("results"):
        return {}
    cases = discover_cases(workspace)
    groups: dict[str, list[dict]] = {}
    for case_id, verdict in run["results"].items():
        if verdict.get("pass"):
            continue
        entry = cases.get(case_id, {})
        key = entry.get("category") or entry.get("suite") or "uncategorised"
        groups.setdefault(key, []).append({"id": case_id, "why": verdict.get("why", ""), "kind": verdict.get("kind", "")})
    return dict(sorted(groups.items(), key=lambda kv: -len(kv[1])))


def write_analysis(workspace: Path) -> Path | None:
    """Generate plan/EVAL_ANALYSIS.md - what failed, grouped, and what it implies."""
    run = latest_run(workspace)
    if not run:
        return None

    cases = discover_cases(workspace)
    groups = failure_groups(workspace)
    change = regressions(workspace)

    lines = [
        "# Eval Analysis",
        "",
        f"**Run:** {run['id']}  **Score:** {run.get('score', 0):.0%} "
        f"({run.get('passed', 0)}/{run.get('total', 0)})"
        + (f"  **Model:** {run['model']}" if run.get("model") else ""),
        "",
        "Generated by `loop eval analyse`. This is the input to the next build decision:",
        "the question is not how many cases failed, it is what the failures have in common.",
        "",
    ]

    if change.get("regressed"):
        lines.extend(
            [
                f"## Regressed since the last run ({len(change['regressed'])})",
                "",
                "These passed before and fail now. Treat as a defect in the change, not a flaky suite,",
                "until shown otherwise.",
                "",
            ]
        )
        lines.extend(f"- `{cid}`" for cid in change["regressed"])
        lines.append("")

    if groups:
        lines.extend([f"## Failures by category ({run.get('total', 0) - run.get('passed', 0)})", ""])
        for name, items in groups.items():
            lines.append(f"### {name} - {len(items)} failing")
            lines.append("")
            for item in items[:12]:
                why = f" - {item['why']}" if item["why"] else ""
                lines.append(f"- `{item['id']}` ({item['kind']}){why}")
            if len(items) > 12:
                lines.append(f"- ...and {len(items) - 12} more")
            lines.append("")
        biggest = next(iter(groups))
        lines.extend(
            [
                "## What this points at",
                "",
                f"The largest group is **{biggest}** with {len(groups[biggest])} failure(s). "
                "Fix the group, not the individual cases - a category that fails together usually",
                "has one cause, and fixing cases one at a time hides it.",
                "",
            ]
        )
    else:
        lines.extend(["## Failures", "", "None in the last run.", ""])

    if change.get("fixed"):
        lines.extend([f"## Fixed since the last run ({len(change['fixed'])})", ""])
        lines.extend(f"- `{cid}`" for cid in change["fixed"])
        lines.append("")

    unexercised = sorted(set(cases) - set(run.get("results") or {}))
    if unexercised and run.get("results"):
        lines.extend(
            [
                f"## Not exercised ({len(unexercised)})",
                "",
                "Cases the run never touched. An untouched case is not a passing case.",
                "",
            ]
        )
        lines.extend(f"- `{cid}`" for cid in unexercised[:20])
        lines.append("")

    path = workspace / ANALYSIS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------


def summary(workspace: Path, *, threshold: float = DEFAULT_THRESHOLD) -> dict:
    cases = discover_cases(workspace)
    run = latest_run(workspace)
    return {
        "cases": len(cases),
        "suites": suites(workspace),
        "runs": len(runs(workspace)),
        "last_score": run.get("score") if run else None,
        "last_run": run.get("id") if run else None,
        "gate": gate_status(workspace, threshold=threshold),
        "regressions": regressions(workspace),
    }


def describe(workspace: Path, *, threshold: float = DEFAULT_THRESHOLD) -> str:
    data = summary(workspace, threshold=threshold)
    if not data["cases"]:
        return (
            "No eval cases found.\n"
            "  Put a JSON list of objects with an `id` under `agent/evals/`.\n"
            "  Any shape works - the harness owns the loop, not the case format."
        )

    lines = [
        f"{data['cases']} case(s) across {len(data['suites'])} suite(s): "
        + ", ".join(f"{name} ({count})" for name, count in data["suites"].items()),
    ]
    if data["last_score"] is None:
        lines.append("")
        lines.append("No run has ever been recorded. Cases that are never run are not evidence -")
        lines.append("score them with `loop eval record`.")
        return "\n".join(lines)

    gate = data["gate"]
    lines.append(f"Last run {data['last_run']}: {data['last_score']:.0%}  ({data['runs']} run(s) recorded)")
    lines.append(f"Gate: {'satisfied' if gate['ok'] else 'NOT satisfied'} - {gate['reason']}")

    change = data["regressions"]
    if change.get("regressed"):
        lines.append("")
        lines.append(f"REGRESSED ({len(change['regressed'])}): " + ", ".join(change["regressed"][:8]))
    if change.get("fixed"):
        lines.append(f"Fixed ({len(change['fixed'])}): " + ", ".join(change["fixed"][:8]))
    if change.get("delta"):
        lines.append(f"Score moved {change['delta']:+.1%} since the previous run.")
    return "\n".join(lines)


def manifest_block(workspace: Path, *, threshold: float = DEFAULT_THRESHOLD) -> list[str]:
    """Lines for plan/SESSION_MANIFEST.md. Absent when there is nothing to act on."""
    cases = discover_cases(workspace)
    if not cases:
        return []

    change = regressions(workspace)
    gate = gate_status(workspace, threshold=threshold)
    if gate["ok"] and not change.get("regressed"):
        return []

    lines = ["", "## Evals", ""]
    if change.get("regressed"):
        lines.append(
            f"- **{len(change['regressed'])} case(s) regressed** since the last run "
            f"({', '.join(change['regressed'][:5])}) - `loop eval analyse`, then fix before building on top."
        )
    if not gate["ok"]:
        lines.append(f"- Eval gate not satisfied: {gate['reason']} - `loop eval`")
    lines.append("")
    return lines


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="Eval cases, recorded runs, regressions, error analysis.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("status", help="Cases, last score, gate, regressions.")
    sub.add_parser("analyse", help="Write plan/EVAL_ANALYSIS.md from the last run.")
    sub.add_parser("cases", help="List discovered case ids by suite.")
    record = sub.add_parser("record", help="Record a scored run from a JSON results file.")
    record.add_argument("results", help='JSON: {"CASE-1": {"pass": true, "kind": "deterministic"}}')
    record.add_argument("--model", default="")
    record.add_argument("--notes", default="")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    cmd = args.cmd or "status"

    if cmd == "cases":
        found = discover_cases(workspace)
        if not found:
            print("No eval cases found.")
            return 0
        for suite, count in suites(workspace).items():
            print(f"{suite}  ({count})")
            for cid, entry in sorted(found.items()):
                if entry["suite"] == suite:
                    print(f"    {cid}{'  [' + entry['category'] + ']' if entry['category'] else ''}")
        return 0

    if cmd == "record":
        try:
            results = json.loads(Path(args.results).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            try:
                results = json.loads(args.results)
            except json.JSONDecodeError:
                print("results must be a JSON file path or a JSON string")
                return 2
        try:
            path = record_run(workspace, results, model=args.model, notes=args.notes)
        except ValueError as exc:
            print(str(exc))
            return 2
        print(f"Recorded {path}" if path else "No eval directory - nothing recorded.")
        if path:
            print(describe(workspace, threshold=args.threshold))
        return 0

    if cmd == "analyse":
        path = write_analysis(workspace)
        print(f"Wrote {path}" if path else "No run recorded yet - nothing to analyse.")
        return 0

    print(describe(workspace, threshold=args.threshold))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
