#!/usr/bin/env python3
"""Roll every sub-product workspace up into the main workspace's plan/SUBPRODUCTS.md.

Strictly read-only across workspaces: this reads each sub-product's own plan state
and reports it here. Corrections travel the other way as *staged* writes
(`hierarchy_sync.stage_findings`), never as direct edits.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

import hierarchy_drift as drift
from workspace_tree import ROLE_MAIN, product_folder, refresh
from workspace_utils import ROOT, resolve_workspace


SUBPRODUCTS_FILE = "plan/SUBPRODUCTS.md"


def load_template() -> str:
    path = ROOT / "templates" / "subproducts.template.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "# Sub-Products - {{MAIN_NAME}}\n\n{{SUMMARY_TABLE}}\n\n{{FINDINGS}}\n\n{{DETAILS}}\n\n{{NEXT_ACTIONS}}\n"


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def _product_name(workspace: Path) -> str:
    from memory_paths import main_plan_file

    text = drift.read_text(main_plan_file(workspace), 6000)
    for line in text.splitlines():
        if line.strip().startswith("- **Name:**"):
            value = line.split("**Name:**", 1)[-1].strip().strip("*").strip()
            if value and not drift.is_placeholder(value):
                return value
    return ""


def _scale(workspace: Path) -> str:
    try:
        from ultraplan_harness import read_scale

        return read_scale(workspace)
    except Exception:
        return "-"


def _gate(workspace: Path) -> str:
    text = drift.read_text(workspace / "GATES.yml", 8000)
    blocked = re.findall(r"(?im)^\s*-?\s*id:\s*(\S+)", text)
    for gid in blocked:
        block = re.search(rf"(?s){re.escape(gid)}.{{0,200}}", text)
        if block and re.search(r"status:\s*(blocked|fail)", block.group(0), re.I):
            return f"{gid} blocked"
    if not blocked:
        return "-"
    return blocked[-1]


def _tasks(workspace: Path) -> str:
    text = drift.read_text(workspace / "TASKS.yml", 20000)
    if not text.strip():
        return "-"
    total = len(re.findall(r"(?im)^\s*-\s+id:", text))
    done = len(re.findall(r"(?i)status:\s*(done|completed)", text))
    active = len(re.findall(r"(?i)status:\s*(in_progress|active|doing)", text))
    if not total:
        return "-"
    return f"{done}/{total} done" + (f", {active} active" if active else "")


def _open_doubts(workspace: Path) -> int:
    text = drift.read_text(workspace / "DOUBTS.md", 20000)
    count = len(re.findall(r"(?im)^- .*open", text))
    if count == 0 and "open" in text.lower():
        count = len([line for line in text.splitlines() if line.strip().startswith("- ")])
    return count


def _last_session(workspace: Path) -> str:
    seen = drift.last_session_at(workspace)
    return seen.date().isoformat() if seen else "never"


def collect_child(child: dict) -> dict:
    """Everything the roll-up shows for one sub-product. Read-only."""
    from feature_paths import read_active_feature

    ws = child["data_dir"]
    active = read_active_feature(ws)
    return {
        **child,
        "product_name": _product_name(ws),
        "initialized": not drift.is_uninitialized(ws),
        "scale": _scale(ws),
        "gate": _gate(ws),
        "tasks": _tasks(ws),
        "doubts": _open_doubts(ws),
        "feature": f"{active.get('id')} {active.get('title', '')}".strip() if active else "-",
        "last_session": _last_session(ws),
        "handoff": drift.read_text(ws / "HANDOFF.md", 600).strip(),
    }


def summary_table(rows: list[dict], findings: list[dict]) -> str:
    if not rows:
        return "_No sub-product workspaces linked yet._"
    by_sub: dict[str, list[dict]] = {}
    for item in findings:
        by_sub.setdefault(item["sub"], []).append(item)

    lines = [
        "| Sub-product | Map row | Plan | Scale | Gate | Tasks | Open doubts | Last session | Drift |",
        "|-------------|---------|------|-------|------|-------|-------------|--------------|-------|",
    ]
    for row in rows:
        issues = by_sub.get(row["name"], [])
        errors = sum(1 for i in issues if i["level"] == drift.LEVEL_ERROR)
        warns = sum(1 for i in issues if i["level"] == drift.LEVEL_WARN)
        if row.get("missing"):
            flag = "**missing**"
        elif errors:
            flag = f"**{errors} error(s)**"
        elif warns:
            flag = f"{warns} warning(s)"
        else:
            flag = "ok"
        plan = "initialized" if row["initialized"] else "**uninitialized**"
        lines.append(
            f"| `{row['name']}` | {row['map_id'] or '-'} | {plan} | {row['scale']} | {row['gate']} | "
            f"{row['tasks']} | {row['doubts']} | {row['last_session']} | {flag} |"
        )
    return "\n".join(lines)


def findings_block(findings: list[dict], staged: dict[str, str] | None = None) -> str:
    if not findings:
        return "No drift detected between the master plan and the linked sub-products."
    staged = staged or {}
    lines = [
        "| Level | Sub-product | Kind | Detail |",
        "|-------|-------------|------|--------|",
    ]
    for item in findings:
        detail = item["detail"].replace("\n", " ")
        if item["id"] in staged:
            detail += f" _(staged in `{item['sub']}` as `{staged[item['id']]}`)_"
        lines.append(f"| {item['level']} | `{item['sub']}` | {item['kind']} | {detail} |")
    return "\n".join(lines)


def details_block(rows: list[dict], findings: list[dict]) -> str:
    if not rows:
        return "_Nothing to detail._"
    by_sub: dict[str, list[dict]] = {}
    for item in findings:
        by_sub.setdefault(item["sub"], []).append(item)

    blocks: list[str] = []
    for row in rows:
        parts = [f"### {row['name']}", ""]
        title = row["product_name"] or "(unnamed)"
        parts.append(f"- **Product:** {title}")
        parts.append(f"- **Path:** `{row['path']}` ({row['source']})")
        parts.append(f"- **Workspace:** `{row['data_dir']}`")
        parts.append(f"- **Map row:** {row['map_id'] or 'unmapped'}")
        parts.append(f"- **Active feature:** {row['feature']}")
        if row.get("missing"):
            parts.append("- **Status:** folder missing - link is broken")
        issues = by_sub.get(row["name"], [])
        if issues:
            parts.append("- **Findings:**")
            parts.extend(f"  - `{i['level']}` {i['kind']}: {i['detail']}" for i in issues)
        if row["handoff"]:
            excerpt = "\n".join(f"  > {ln}" for ln in row["handoff"].splitlines()[:6])
            parts.extend(["- **Handoff:**", excerpt])
        blocks.append("\n".join(parts))
    return "\n\n".join(blocks)


def next_actions(rows: list[dict], findings: list[dict]) -> str:
    actions: list[str] = []
    if any(f["level"] == drift.LEVEL_ERROR for f in findings):
        actions.append(
            "Resolve the `error` findings above - run `/resolve-doubts` here, then "
            "`loop pending approve --all` inside each affected sub-product."
        )
    if any(f["kind"] == "unmapped-sub" for f in findings):
        actions.append("Add the unmapped sub-product(s) to `plan/PRODUCT_MAP.md`, then re-run `/plan-loop`.")
    if any(f["kind"] == "unbuilt-row" for f in findings):
        actions.append(
            "For each unbuilt map row: `cd <folder> && loop setup --use-cwd --role sub`, then `/plan-loop` there."
        )
    if any(not r["initialized"] for r in rows if not r.get("missing")):
        actions.append("Run `/plan-loop` inside each uninitialized sub-product.")
    if not actions:
        actions.append("Sub-products are aligned with the master plan - continue `/plan-loop` or `/product-develop`.")
    return "\n".join(f"- {a}" for a in actions)


def build_report(
    workspace: Path,
    tree: dict | None = None,
    staged: dict[str, str] | None = None,
    findings: list[dict] | None = None,
) -> tuple[str, list[dict], list[dict]]:
    tree = tree or refresh(workspace)
    children = [c for c in (tree.get("children") or [])]
    rows = [collect_child(c) for c in children]
    if findings is None:
        findings = drift.check_children(workspace, children)

    folder = product_folder(workspace)
    content = render(
        load_template(),
        {
            "UPDATED_DATE": date.today().isoformat(),
            "MAIN_NAME": _product_name(workspace) or (tree.get("name") or (folder.name if folder else "Product")),
            "MAIN_PATH": str(folder or workspace),
            "SUB_COUNT": str(len(rows)),
            "SUMMARY_TABLE": summary_table(rows, findings),
            "FINDINGS": findings_block(findings, staged),
            "DETAILS": details_block(rows, findings),
            "NEXT_ACTIONS": next_actions(rows, findings),
        },
    )
    return content, rows, findings


def write_report(
    workspace: Path,
    tree: dict | None = None,
    staged: dict[str, str] | None = None,
    findings: list[dict] | None = None,
) -> tuple[Path | None, list[dict]]:
    tree = tree or refresh(workspace)
    if tree.get("role") != ROLE_MAIN or not tree.get("enabled"):
        return None, []
    content, _rows, findings = build_report(workspace, tree, staged, findings)
    path = workspace / SUBPRODUCTS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path, findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll sub-product workspaces up into plan/SUBPRODUCTS.md.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--print", action="store_true", help="Print instead of writing.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    tree = refresh(workspace)
    if tree.get("role") != ROLE_MAIN or not tree.get("enabled"):
        print("Not a main product workspace - no sub-products to roll up.")
        print(f"role={tree.get('role')}")
        return 0

    if args.print:
        content, _rows, findings = build_report(workspace, tree)
        print(content)
        print(f"findings={drift.summarize(findings)}")
        return 0

    path, findings = write_report(workspace, tree)
    print(f"Wrote {path}")
    counts = drift.summarize(findings)
    print(f"sub-products={len(tree.get('children') or [])} findings={counts['total']} errors={counts['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
