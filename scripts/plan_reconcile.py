#!/usr/bin/env python3
"""Reconcile a planning reform across every file its context upgrades.

`/plan-loop` phases each own a narrow file list (grill writes `main_plan.md` /
`DOUBTS.md`, task-compiler writes `TASKS.yml` / `GATES.yml`, ...). A reform that
cuts across the plan - step 19 becoming a centralized service, a decision
reversing another - touches files no single phase owns: `PRODUCT_MAP.md` header
rows, sibling step files, scope `TASKS.yml` / `GATES.yml` mirrors,
`DEPLOYMENT_PLAN.md`, `PROD-GAP.md`, contracts. Those files silently keep the
old story and the next agent inherits a contradiction.

Three subcommands. Analysis first, mutation explicit:

  fanout --decision D-M-063 [--scope slug]
      Files a reform of this decision (in this scope) can affect, grouped by
      action: update / review / regenerate. Pure analysis, no writes.

  check [--scope slug] [--write]
      Deterministic drift across the plan surface. Exit 1 while a blocker
      remains (a superseded or retired id cited as live, a scope/root mirror
      divergence, a map-vs-tracker mismatch, deployment decisions newer than
      `DEPLOYMENT_PLAN.md`, open cross-scope blocks with no `plan/contracts/`
      record). `--write` also drops `plan/RECONCILE_REPORT.md`.

  retire --id D-M-022 --by D-M-057 --reason "..." [--type decision]
      Append to `plan/RETIRED.md` (the retirement ledger), then re-check that
      id and list the live citations still to fix. Nothing is deleted: the
      ledger makes dead planning addressable, so `check` can fail on it
      instead of letting it sit forever and confuse the next agent.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

RETIRED_LEDGER = "plan/RETIRED.md"
RECONCILE_REPORT = "plan/RECONCILE_REPORT.md"

ID = re.compile(r"\b(D-(?:[A-Z]+-)?\d+|DQ-(?:[A-Z]+-)?\d+|E-(?:[A-Z]+-)?\d+|TASK-(?:[A-Z]+-)?\d+|G-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b")
HEADING = re.compile(r"^(#{2,4})\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\b\s*[:.]?\s*(?P<title>.*)$")
# Supersession is a declared `- **Status:**` / `- **Supersedes:**` field, never a
# table cell or a passing mention: a `| ... | **Superseded** by D-M-003 |` row
# inside D-M-030's own entry once mapped D-M-030 -> D-M-003.
STATUS_FIELD = re.compile(r"^\s*[-*]\s+\*\*\s*status\s*:?\s*\*\*\s*(?P<value>.*)$", re.IGNORECASE)
STATUS_SUPERSEDED = re.compile(r"superseded\b.{0,80}?by\s+[`\"']?(?P<by>[A-Z][A-Z0-9-]*\d+)", re.IGNORECASE)
SUPERSEDES_FIELD = re.compile(r"^\s*[-*]\s+\*\*\s*supersedes\s*:?\s*\*\*\s*(?P<ids>[^\n]+)$", re.IGNORECASE)
DATE_LINE = re.compile(r"\*\*\s*date\s*:\s*\*\*\s*(?P<date>\d{4}-\d{2}-\d{2})", re.IGNORECASE)
# A citation is historical, not live, when its neighbourhood says so.
HISTORICAL = re.compile(
    r"superseded|supersedes|revers\w*|withdrawn|replaced|replaces|retires?|retired"
    r"|amends?|amending|amended|overturn\w*|rewritten|rewrites?|corrected|corrects?|extended|extends?",
    re.IGNORECASE,
)

DEPLOY_KEYWORDS = re.compile(
    r"deploy|cloud|llm|model|infra|region|service|hosting|migrat|ci/?cd|secret|vendor|provider|kubernetes|ecs|container",
    re.IGNORECASE,
)
DIRECTION_KEYWORDS = re.compile(
    r"position|pivot|thesis|business|pricing|wedge|company|migrate|revenue|business model",
    re.IGNORECASE,
)
DEPLOY_STAMP = re.compile(
    r"(?:\*\*(?:updated|rewritten by hand|generated):\*\*|rewritten by hand)\s*(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)

GENERATED_SESSION_FILES = {
    "SESSION_MANIFEST.md",
    "SESSION_CLOSEOUT.md",
    "SESSION_RECALL.md",
    "MEMORY_REVIEW.md",
    "RECONCILE_REPORT.md",
    "ULTRAPLAN_STATUS.md",
    "BUILD_CONTEXT.md",
    "AUTO_SKILLS.md",
    "AUTO_AGENT_SKILLS.md",
    "AUTO_DOMAIN_SKILLS.md",
    "AUTO_AGENTS.md",
}

SCOPE_PACK_FILES = (
    "overview.md",
    "prd.md",
    "architecture.md",
    "agents.md",
    "data-model.md",
    "integrations.md",
    "risks.md",
    "acceptance.md",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def decisions_files(workspace: Path) -> list[Path]:
    found = []
    root = workspace / "DECISIONS.md"
    if root.is_file():
        found.append(root)
    for path in sorted((workspace / "plan" / "products").glob("*/DECISIONS.md")) if (workspace / "plan" / "products").is_dir() else []:
        found.append(path)
    return found


def plan_surface(workspace: Path, *, scope: str | None = None) -> list[Path]:
    """Every plan narrative file a reform can leave stale (no archives, no logs)."""
    out: list[Path] = []
    plan = workspace / "plan"
    for rel in ("main_plan.md", "PRODUCT_MAP.md", "IDEA.md", "PROD-GAP.md", "CRITICAL_PATH.md", "PROGRAMS.md"):
        path = plan / rel
        if path.is_file():
            out.append(path)
    out.extend(sorted(plan.glob("step_*.md")))
    out.extend(sorted((plan / "steps").glob("*/*.md"))) if (plan / "steps").is_dir() else None
    products = plan / "products"
    if products.is_dir():
        for scope_dir in sorted(products.iterdir()):
            if not scope_dir.is_dir() or (scope and scope_dir.name != scope):
                continue
            for name in SCOPE_PACK_FILES:
                path = scope_dir / name
                if path.is_file():
                    out.append(path)
            out.extend(sorted((scope_dir / "steps").glob("*.md"))) if (scope_dir / "steps").is_dir() else None
            for rel in ("TASKS.yml", "GATES.yml", "DOUBTS.md", "CURRENT_STATE.md", "HANDOFF.md", "PROD-GAP.md"):
                path = scope_dir / rel
                if path.is_file():
                    out.append(path)
    for rel in ("DECISIONS.md", "EVIDENCE_LOG.md", "DEPLOYMENT_PLAN.md", "COMPACT.md", "CURRENT_STATE.md", "CONTEXT.md", "TASKS.yml", "GATES.yml"):
        path = workspace / rel
        if path.is_file():
            out.append(path)
    return out


def check_surface(workspace: Path, *, scope: str | None = None) -> list[Path]:
    """Citation-scan surface: plan surface minus generated session artifacts.

    Append-only records are excluded: `CURRENT_STATE.md` and `HANDOFF.md` are
    dated running logs, and `EVIDENCE_LOG.md` entries are point-in-time
    research records ("Researched for D-M-020", "contradicts D-M-011's kept
    scope") - flagging history as contradiction teaches agents to ignore the
    check. Evidence validity is owned by `loop evidence` and the reference
    graph. `COMPACT.md` stays in: it claims to be the current summary.
    """
    return [
        p
        for p in plan_surface(workspace, scope=scope)
        if p.name not in GENERATED_SESSION_FILES
        and p.name not in ("CURRENT_STATE.md", "HANDOFF.md", "EVIDENCE_LOG.md")
    ]


def superseded_map(workspace: Path) -> dict[str, str]:
    """Superseded decision id -> superseding id, from every DECISIONS.md."""
    mapping: dict[str, str] = {}
    for path in decisions_files(workspace):
        current: str | None = None
        for line in _read(path).splitlines():
            heading = HEADING.match(line.strip())
            if heading and re.match(r"^[A-Z][A-Z0-9-]*\d+$", heading.group("id")):
                current = heading.group("id")
                continue
            status_field = STATUS_FIELD.match(line)
            if status_field and current:
                status = STATUS_SUPERSEDED.search(status_field.group("value"))
                if status:
                    mapping.setdefault(current, status.group("by"))
            supersedes = SUPERSEDES_FIELD.match(line)
            if supersedes and current:
                for old in ID.findall(supersedes.group("ids")):
                    mapping.setdefault(old, current)
    return mapping


def retired_map(workspace: Path) -> dict[str, str]:
    """Retired id -> retiring id, from the retirement ledger."""
    mapping: dict[str, str] = {}
    path = workspace / RETIRED_LEDGER
    if not path.is_file():
        return mapping
    current: str | None = None
    for line in _read(path).splitlines():
        heading = re.match(r"^##\s+(?P<id>[A-Z][A-Z0-9-]*\d+)\b.*$", line.strip())
        if heading:
            current = heading.group("id")
            by = re.search(r"\bby\s+[`\"']?([A-Z][A-Z0-9-]*\d+)", line, re.IGNORECASE)
            if by and current:
                mapping.setdefault(current, by.group(1))
            continue
    return mapping


NORMATIVE_FIELD = re.compile(r"^\s*[-*]\s+\*\*\s*(decision|consequences)\b", re.IGNORECASE)


def _citations_with_context(path: Path, wanted: set[str]) -> list[dict]:
    """Live citations of wanted ids: file, line, id, excerpt.

    Inside `DECISIONS.md` only the normative fields (`- **Decision:**`,
    `- **Consequences:**`) count: rationale, history and detail lines discuss
    dead decisions legitimately ("the substantive change from D-M-033 §4",
    "CORRECTED ... by D-M-017"). Everywhere else the whole line is a live
    claim. Duplicates on one line collapse to a single hit.
    """
    hits: list[dict] = []
    seen: set[tuple[str, int, str]] = set()
    lines = _read(path).splitlines()
    is_decisions = path.name == "DECISIONS.md"
    current_entry: str | None = None
    for index, line in enumerate(lines):
        if is_decisions:
            heading = HEADING.match(line.strip())
            if heading:
                current_entry = heading.group("id")
            if not NORMATIVE_FIELD.match(line):
                continue
        for found in ID.findall(line):
            if found not in wanted:
                continue
            if is_decisions and found == current_entry:
                continue  # an entry naming itself
            if is_decisions and re.search(r"superseded|supersedes", line, re.IGNORECASE):
                continue  # the declaration itself, not a live citation
            if str(path).replace("\\", "/").endswith(RETIRED_LEDGER):
                continue
            key = (str(path), index + 1, found)
            if key in seen:
                continue
            seen.add(key)
            window = "\n".join(lines[max(0, index - 3): index + 4])
            if HISTORICAL.search(window):
                continue  # neighbourhood already says it is dead
            hits.append({"file": str(path), "line": index + 1, "id": found, "excerpt": line.strip()[:160]})
    return hits


def check_stale_citations(workspace: Path, *, scope: str | None = None) -> list[dict]:
    dead = {**superseded_map(workspace), **retired_map(workspace)}
    if not dead:
        return []
    findings = []
    for path in check_surface(workspace, scope=scope):
        for hit in _citations_with_context(path, set(dead)):
            by = dead[hit["id"]]
            findings.append(
                {
                    "level": "blocker",
                    "code": "stale-citation",
                    "file": hit["file"],
                    "line": hit["line"],
                    "message": f"`{hit['id']}` is dead (superseded/retired by `{by}`) but cited as live: {hit['excerpt']}",
                }
            )
    return findings


def check_mirrors(workspace: Path, *, scope: str | None = None) -> list[dict]:
    """Same task/gate id, different status in root vs scope files."""
    from scope_state import parse_gates_file
    from task_context import parse_tasks_file

    findings = []
    try:
        import scope_paths as sp

        scopes = [s for s in sp.list_scopes(workspace) if scope is None or s.slug == scope]
    except Exception:
        return findings
    root_tasks = {str(t.get("id")): str(t.get("status", "")).lower() for t in parse_tasks_file(workspace / "TASKS.yml") if t.get("id")}
    root_gates = {str(g.get("id")): str(g.get("status", "")).lower() for g in parse_gates_file(workspace / "GATES.yml") if g.get("id")}
    for record in scopes:
        for name, root, parse in (("task", root_tasks, parse_tasks_file), ("gate", root_gates, parse_gates_file)):
            path = (workspace / "plan" / "products" / record.slug / ("TASKS.yml" if name == "task" else "GATES.yml"))
            if not path.is_file():
                continue
            for item in parse(path):
                gid = str(item.get("id") or "")
                status = str(item.get("status", "")).lower()
                if gid in root and root[gid] and status and root[gid] != status:
                    findings.append(
                        {
                            "level": "blocker",
                            "code": f"{name}-mirror",
                            "file": str(path),
                            "line": 0,
                            "message": f"`{gid}` is `{root[gid]}` in root but `{status}` in scope `{record.slug}` - one of them is the old story",
                        }
                    )
    return findings


def _map_rows(workspace: Path) -> list[dict]:
    path = workspace / "plan" / "PRODUCT_MAP.md"
    if not path.is_file():
        return []
    rows = []
    for line in _read(path).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 8 and re.match(r"^\d+$", cells[0]):
            rows.append({"id": cells[0], "step": cells[2], "status": cells[7]})
    return rows


def _tracker_rows(workspace: Path) -> list[dict]:
    path = workspace / "plan" / "ULTRAPLAN_STATUS.md"
    if not path.is_file():
        return []
    rows = []
    for line in _read(path).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and cells[0].lower() not in ("step", "------", ""):
            rows.append({"step": cells[0], "ultraplan": cells[2], "missing": cells[3]})
    return rows


def check_map_tracker(workspace: Path) -> list[dict]:
    findings = []
    rows = _map_rows(workspace)
    tracker = _tracker_rows(workspace)
    if not rows or not tracker:
        return findings

    def slug(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", text.lower())

    missing_by_step = {slug(r["step"]): r for r in tracker}
    for row in rows:
        key = slug(row["step"])
        match = missing_by_step.get(key)
        if not match:
            continue
        missing = match["missing"].strip().lower()
        missing_open = missing and missing not in ("-", "n/a", "na", "none", "—", "complete", "ok")
        status = row["status"].lower()
        done_claim = re.search(r"built|complete|done|active|shipped|ready", status) and "not " not in status
        if done_claim and missing_open:
            findings.append(
                {
                    "level": "blocker",
                    "code": "map-tracker",
                    "file": str(workspace / "plan" / "PRODUCT_MAP.md"),
                    "line": 0,
                    "message": f"map row {row['id']} claims `{row['status'][:80]}` but ULTRAPLAN_STATUS lists missing artifacts for `{row['step']}`: {match['missing'][:120]}",
                }
            )
    return findings


def decision_dates(workspace: Path) -> list[dict]:
    """Every decision id with its Date: and whether it touches deployment."""
    out = []
    for path in decisions_files(workspace):
        current: str | None = None
        body: list[str] = []
        dated: str | None = None

        def flush() -> None:
            if current and dated:
                text = "\n".join(body)
                out.append({"id": current, "date": dated, "deploy": bool(DEPLOY_KEYWORDS.search(text))})

        for line in _read(path).splitlines():
            heading = HEADING.match(line.strip())
            if heading and re.match(r"^D-[A-Z]+-\d+$", heading.group("id")):
                flush()
                current, body, dated = heading.group("id"), [line], None
                continue
            if current is None:
                continue
            body.append(line)
            date_match = DATE_LINE.search(line)
            if date_match:
                dated = date_match.group("date")
        flush()
    return out


def check_deployment(workspace: Path) -> list[dict]:
    plan = workspace / "DEPLOYMENT_PLAN.md"
    if not plan.is_file():
        return []
    stamps = DEPLOY_STAMP.findall(_read(plan))
    if not stamps:
        return []
    stamp = max(stamps)
    findings = []
    for decision in decision_dates(workspace):
        if decision["deploy"] and decision["date"] > stamp:
            findings.append(
                {
                    "level": "review",
                    "code": "deployment-stale",
                    "file": str(plan),
                    "line": 0,
                    "message": f"`{decision['id']}` ({decision['date']}) touches deployment but DEPLOYMENT_PLAN.md is stamped {stamp} - reconcile by hand; do not blind-regenerate (see the file's own warning)",
                }
            )
    return findings


def check_contracts(workspace: Path) -> list[dict]:
    try:
        from scope_state import cross_scope_blocks, load_tasks
    except Exception:
        return []
    try:
        blocks = [b for b in cross_scope_blocks(load_tasks(workspace)) if not b.get("satisfied")]
    except Exception:
        return []
    if not blocks:
        return []
    contracts = workspace / "plan" / "contracts"
    recorded = len(list(contracts.glob("*.md"))) if contracts.is_dir() else 0
    if recorded:
        return []
    return [
        {
            "level": "review",
            "code": "contracts-missing",
            "file": str(workspace / "plan"),
            "line": 0,
            "message": f"{len(blocks)} unsatisfied cross-scope block(s) (e.g. {blocks[0].get('task')} waits on {blocks[0].get('blocked_by')}) with no `plan/contracts/` record - `loop scope check`, then record the contract",
        }
    ]


def check(workspace: Path, *, scope: str | None = None) -> list[dict]:
    findings: list[dict] = []
    findings.extend(check_stale_citations(workspace, scope=scope))
    findings.extend(check_mirrors(workspace, scope=scope))
    if scope is None:
        findings.extend(check_map_tracker(workspace))
        findings.extend(check_deployment(workspace))
        findings.extend(check_contracts(workspace))
    order = {"blocker": 0, "review": 1}
    return sorted(findings, key=lambda f: (order.get(f["level"], 2), f["code"], f["file"]))


def describe(findings: list[dict], workspace: Path) -> str:
    lines = [
        "# Plan Reconcile Report",
        "",
        f"**Generated:** {date.today().isoformat()}",
        f"**Workspace:** `{workspace}`",
        "",
    ]
    blockers = [f for f in findings if f["level"] == "blocker"]
    reviews = [f for f in findings if f["level"] == "review"]
    lines.append(f"**Blockers:** {len(blockers)} · **Needs review:** {len(reviews)}")
    lines.append("")
    if not findings:
        lines.append("Plan surface is consistent: no live citations of dead planning, no mirror divergence.")
        return "\n".join(lines) + "\n"
    for level in ("blocker", "review"):
        items = [f for f in findings if f["level"] == level]
        if not items:
            continue
        lines.append(f"## {'Blockers' if level == 'blocker' else 'Needs review'}")
        lines.append("")
        for item in items:
            try:
                rel = str(Path(item["file"]).relative_to(workspace))
            except ValueError:
                rel = item["file"]
            loc = f"`{rel}:{item['line']}`" if item.get("line") else f"`{rel}`"
            lines.append(f"- [{item['code']}] {loc} - {item['message']}")
        lines.append("")
    lines.extend(
        [
            "Fix in the same run: update the cited file to the live decision, or record",
            "the retirement with `loop plan-reconcile retire --id <old> --by <new> --reason \"...\"`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def decision_text(workspace: Path, decision_id: str) -> str:
    """Heading title plus entry body, so keyword routing sees the whole decision."""
    for path in decisions_files(workspace):
        lines = _read(path).splitlines()
        for index, line in enumerate(lines):
            heading = HEADING.match(line.strip())
            if heading and heading.group("id") == decision_id:
                body = [heading.group("title")]
                for follow in lines[index + 1:]:
                    if HEADING.match(follow.strip()):
                        break
                    body.append(follow)
                return "\n".join(body)
    return decision_id


def fanout(workspace: Path, decision_id: str, *, scope: str | None = None) -> dict:
    decision_id = decision_id.strip()
    body = decision_text(workspace, decision_id)
    groups: dict[str, list[str]] = {"update": [], "review": [], "regenerate": []}

    def rel(path: Path) -> str:
        try:
            return str(path.relative_to(workspace))
        except ValueError:
            return str(path)

    cited = set()
    for path in check_surface(workspace):
        if decision_id in _read(path):
            cited.add(rel(path))
    groups["update"].extend(sorted(cited))
    if scope:
        pack = workspace / "plan" / "products" / scope
        if pack.is_dir():
            for name in (*SCOPE_PACK_FILES, "TASKS.yml", "GATES.yml", "DOUBTS.md"):
                path = pack / name
                if path.is_file() and rel(path) not in groups["update"]:
                    groups["update"].append(rel(path))
            groups["update"].sort()
    dtext = body + "\n" + decision_id
    if DIRECTION_KEYWORDS.search(dtext) or "PRODUCT_MAP" in "".join(cited):
        if "plan/PRODUCT_MAP.md" not in groups["update"]:
            groups["review"].append("plan/PRODUCT_MAP.md (rows + Updated: header must match the live decision)")
    elif (workspace / "plan" / "PRODUCT_MAP.md").is_file():
        groups["review"].append("plan/PRODUCT_MAP.md (confirm no row still tells the old story)")
    if DEPLOY_KEYWORDS.search(dtext):
        groups["review"].append("DEPLOYMENT_PLAN.md (hand-reconcile; do not blind-regenerate)")
    if (workspace / "plan" / "PROD-GAP.md").is_file():
        groups["review"].append("plan/PROD-GAP.md (blockers the reform resolves must come out)")
    if (workspace / "plan" / "IDEA.md").is_file() and DIRECTION_KEYWORDS.search(dtext):
        groups["review"].append("plan/IDEA.md (direction changed - flag the delta, do not silently rewrite history)")
    groups["regenerate"].append("plan/ULTRAPLAN_STATUS.md via `loop plan-loop ultraplan status`")
    return {"decision": decision_id, "scope": scope, "groups": groups}


def render_fanout(result: dict) -> str:
    lines = [f"# Fanout for `{result['decision']}`", ""]
    if result["scope"]:
        lines.append(f"Scope: `{result['scope']}`")
        lines.append("")
    for action in ("update", "review", "regenerate"):
        items = result["groups"][action]
        lines.append(f"## {action.title()} ({len(items)})")
        lines.append("")
        if items:
            lines.extend(f"- `{item}`" for item in items)
        else:
            lines.append("- Nothing.")
        lines.append("")
    return "\n".join(lines)


def retire(workspace: Path, *, rid: str, by: str, reason: str, rtype: str = "decision") -> dict:
    ledger = workspace / RETIRED_LEDGER
    entry = (
        f"## {rid} ({rtype}, retired {date.today().isoformat()} by {by})\n"
        f"- **Reason:** {reason}\n"
        f"- **Superseded by:** `{by}`\n"
    )
    if not ledger.is_file():
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(
            "# Retired Planning\n\n"
            "Planning this workspace no longer believes. Nothing here is deleted from\n"
            "history - this ledger makes dead items addressable so `loop plan-reconcile\n"
            "check` fails while a live file still cites one of them.\n\n"
            "Retire with `loop plan-reconcile retire --id <old> --by <new> --reason \"...\"`.\n\n",
            encoding="utf-8",
        )
    text = _read(ledger)
    if re.search(rf"^##\s+{re.escape(rid)}\b", text, re.MULTILINE):
        recorded = False
    else:
        ledger.write_text(text.rstrip() + "\n\n" + entry, encoding="utf-8")
        recorded = True
    remaining = [f for f in check_stale_citations(workspace) if f["message"].split("`")[1] == rid]
    return {"ledger": str(ledger), "recorded": recorded, "remaining": remaining}


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="Reconcile a planning reform across every file it touches.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    fan = sub.add_parser("fanout", help="Files a reform of one decision can affect.")
    fan.add_argument("--decision", required=True)
    fan.add_argument("--scope", default=None)

    chk = sub.add_parser("check", help="Deterministic drift across the plan surface.")
    chk.add_argument("--scope", default=None)
    chk.add_argument("--write", action="store_true", help="Also write plan/RECONCILE_REPORT.md.")

    ret = sub.add_parser("retire", help="Record a dead planning item in plan/RETIRED.md.")
    ret.add_argument("--id", required=True)
    ret.add_argument("--by", required=True)
    ret.add_argument("--reason", required=True)
    ret.add_argument("--type", default="decision")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if args.cmd == "fanout":
        print(render_fanout(fanout(workspace, args.decision, scope=args.scope)))
        return 0
    if args.cmd == "check":
        findings = check(workspace, scope=args.scope)
        report = describe(findings, workspace)
        print(report)
        if args.write:
            out = workspace / RECONCILE_REPORT
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(report, encoding="utf-8")
            print(f"Wrote {out}")
        blockers = sum(1 for f in findings if f["level"] == "blocker")
        if blockers:
            print(f"{blockers} blocker(s) remain.")
            return 1
        return 0
    result = retire(workspace, rid=args.id, by=args.by, reason=args.reason, rtype=args.type)
    print(f"{'Recorded' if result['recorded'] else 'Already recorded'} `{args.id}` in {result['ledger']}")
    if result["remaining"]:
        print(f"{len(result['remaining'])} live citation(s) still to fix:")
        for item in result["remaining"][:10]:
            print(f"- {item['file']}:{item['line']} - {item['message'][:140]}")
        return 1
    print("No live citations remain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
