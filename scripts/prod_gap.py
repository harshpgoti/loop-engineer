#!/usr/bin/env python3
"""Create a structured product gap analysis draft in plan/PROD-GAP.md."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from source_tree_scan import scan_source_tree
from workspace_utils import ROOT, resolve_workspace


STATE_FILES = [
    "main_plan.md",
    "plan",
    "MEMORY.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "CURRENT_STATE.md",
    "DECISIONS.md",
    "EVIDENCE_LOG.md",
    "HANDOFF.md",
    "COMPACT.md",
]


def read_text(path: Path, max_chars: int = 2500) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n_...truncated_"


def extract_line(text: str, prefix: str, default: str = "TBD") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def load_template() -> str:
    path = ROOT / "templates" / "prod_gap.template.md"
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def bullet(items: list[str]) -> str:
    if not items:
        return "- None identified yet."
    return "\n".join(f"- {item}" for item in items)


def has_initialized_product(main_plan: str) -> bool:
    return "Status: **UNINITIALIZED**" not in main_plan


def analyze(workspace: Path) -> str:
    from memory_paths import main_plan_file

    main_plan = read_text(main_plan_file(workspace))
    current_state = read_text(workspace / "CURRENT_STATE.md")
    doubts = read_text(workspace / "DOUBTS.md")
    tasks = read_text(workspace / "TASKS.yml")
    gates = read_text(workspace / "GATES.yml")
    evidence = read_text(workspace / "EVIDENCE_LOG.md")
    decisions = read_text(workspace / "DECISIONS.md")

    p0: list[str] = []
    p1: list[str] = []
    p2: list[str] = []
    technical: list[str] = []
    non_technical: list[str] = []
    agent_solvable: list[str] = []
    human_required: list[str] = []
    gate_impact: list[str] = []
    production_readiness: list[str] = []
    recommended: list[str] = []
    open_questions: list[str] = []

    if not has_initialized_product(main_plan):
        p0.append("Product is not initialized in `main_plan.md`.")
        non_technical.append("Product name, target user, problem, first step, and constraints are still missing.")
        human_required.append("User must provide product initialization inputs or approve defaults.")
        recommended.append("Run `/plan` to initialize the product plan.")

    if "open" in doubts.lower():
        p1.append("There are unresolved questions in `DOUBTS.md`.")
        non_technical.append("Resolve or explicitly defer open doubts before major build work.")
        human_required.append("User must answer or explicitly defer open questions in `DOUBTS.md`.")
        open_questions.append("Review `DOUBTS.md`.")

    if "No product evidence yet" in evidence or "Define product before research" in evidence:
        p1.append("Product-critical evidence is missing or not yet collected.")
        non_technical.append("Add sourced evidence to `EVIDENCE_LOG.md` for major product assumptions.")
        agent_solvable.append("Agent can research and draft evidence entries if sources are available.")
        recommended.append("Run `/plan` product research / fact-check pass.")

    if "No product decisions yet" in decisions:
        p1.append("No product or architecture decisions are recorded.")
        non_technical.append("Record durable decisions in `DECISIONS.md` as soon as product direction is chosen.")
        human_required.append("User must approve product/architecture decisions when they change scope, cost, or risk.")

    if "blocked" in gates.lower():
        gate_impact.append("One or more gates are blocked in `GATES.yml`.")
        production_readiness.append("Release is blocked until required gates pass.")
        recommended.append("Use `/loop-engine` to route to the next blocked gate.")

    if "status: blocked" in tasks.lower():
        p1.append("Some tasks are blocked in `TASKS.yml`.")
        agent_solvable.append("Agent can work on unblocked technical tasks from `TASKS.yml`.")
        recommended.append("Review blocked tasks and unblock the next P0/P1 item.")

    step_files = sorted((workspace / "plan").glob("step_*.md"))
    if has_initialized_product(main_plan) and not step_files:
        p0.append("Product is initialized but no `plan/step_*.md` file exists.")
        technical.append("The first product step needs a step plan before development can proceed.")
        agent_solvable.append("Agent can create the first step plan from `main_plan.md` if product direction is clear.")
        recommended.append("Run `/plan` to create the first step plan.")

    if not (workspace / "docs" / "TEST_PLAN.md").exists():
        p1.append("Test plan document is missing.")
        technical.append("Create `docs/TEST_PLAN.md` from the active product step.")
        agent_solvable.append("Agent can draft `docs/TEST_PLAN.md` from the active step plan.")

    if not (workspace / "docs" / "ACCEPTANCE_CRITERIA.md").exists():
        p1.append("Acceptance criteria document is missing.")
        non_technical.append("Create `docs/ACCEPTANCE_CRITERIA.md` from the PRD and step plan.")
        agent_solvable.append("Agent can draft `docs/ACCEPTANCE_CRITERIA.md` from the PRD and step plan.")

    if "G-RELEASE-01" in gates and "status: blocked" in gates.lower():
        production_readiness.append("Release gate appears blocked; verify CI, staging, smoke tests, and rollback.")
        technical.append("Production release readiness needs CI/staging/smoke/rollback verification.")

    if "G-SECURITY-01" in gates and "status: blocked" in gates.lower():
        production_readiness.append("Security gate appears blocked; verify scans, dependency audit, access control, and secrets handling.")
        technical.append("Security readiness needs scan results and mitigation of high-risk findings.")

    if "G-COMPLIANCE-01" in gates and "status: blocked" in gates.lower():
        production_readiness.append("Risk/compliance gate appears blocked; product-specific risk packet may be missing.")
        human_required.append("User may need to provide legal/compliance decisions, vendor approvals, or business risk acceptance.")

    product_name = extract_line(main_plan, "- **Name", "Uninitialized")
    phase = extract_line(current_state, "**Phase", "Unknown")
    active_gate = extract_line(current_state, "**Active gate", "Unknown")
    active_task = "See `TASKS.yml`."

    source_files = "\n".join(f"- `{item}`" for item in STATE_FILES)

    source_findings = scan_source_tree(workspace)
    if source_findings.source_root:
        source_files += f"\n- Source root: `{source_findings.source_root}` ({source_findings.scanned_files} files scanned)"
    else:
        p2.append("No product source tree detected for deeper implementation checks.")

    p0.extend(source_findings.p0)
    p1.extend(source_findings.p1)
    p2.extend(source_findings.p2)
    technical.extend(source_findings.technical)
    production_readiness.extend(source_findings.release)
    if source_findings.security:
        for item in source_findings.security:
            if "secret" in item.lower():
                p0.append("Possible secret-like content found in source tree.")
                human_required.append("User must verify no real secrets are committed and rotate any exposed credentials.")
                break
        technical.extend(source_findings.security)
    if source_findings.todo_count:
        p2.append(f"Source tree contains {source_findings.todo_count} TODO marker(s).")
    if source_findings.fixme_count:
        p1.append(f"Source tree contains {source_findings.fixme_count} FIXME marker(s).")
        agent_solvable.append("Agent can triage FIXME markers and convert urgent ones into tasks.")

    template = load_template()
    return render(
        template,
        {
            "UPDATED_DATE": date.today().isoformat(),
            "EXECUTIVE_SUMMARY": "Generated structured draft. Agent should refine with deeper product and code analysis.",
            "PRODUCT_NAME": product_name,
            "PHASE": phase,
            "ACTIVE_GATE": active_gate,
            "ACTIVE_TASK": active_task,
            "P0_GAPS": bullet(p0),
            "P1_GAPS": bullet(p1),
            "P2_GAPS": bullet(p2),
            "TECHNICAL_GAPS": bullet(technical),
            "NON_TECHNICAL_GAPS": bullet(non_technical),
            "AGENT_SOLVABLE_BLOCKERS": bullet(agent_solvable),
            "HUMAN_REQUIRED_BLOCKERS": bullet(human_required),
            "GATE_IMPACT": bullet(gate_impact),
            "PRODUCTION_READINESS": bullet(production_readiness),
            "RECOMMENDED_TASKS": bullet(recommended),
            "OPEN_QUESTIONS": bullet(open_questions),
            "SOURCE_FILES": source_files,
        },
    )


def append_session_log(workspace: Path, output: Path) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} — Product gap analysis\n\n"
            f"- Updated `{output.relative_to(workspace)}`.\n"
        )


def append_human_blockers(workspace: Path) -> None:
    doubts_path = workspace / "DOUBTS.md"
    handoff_path = workspace / "HANDOFF.md"

    doubts_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.parent.mkdir(parents=True, exist_ok=True)

    note = (
        "\n"
        f"## {date.today().isoformat()} — Human-required production blockers\n\n"
        "- Review `plan/PROD-GAP.md` section **Human-Required Blockers**.\n"
        "- Resolve or explicitly defer P0/P1 human-required blockers before production launch.\n"
    )

    with doubts_path.open("a", encoding="utf-8") as handle:
        handle.write(note)

    with handoff_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} — Production gap follow-up\n\n"
            "- `plan/PROD-GAP.md` was updated.\n"
            "- Ask the user to resolve human-required blockers listed there.\n"
            "- Agent may continue with safe P0/P1 technical blockers.\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write plan/PROD-GAP.md for a product workspace.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Product workspace. Defaults to registered current workspace or current directory.",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    output = workspace / "plan" / "PROD-GAP.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(analyze(workspace), encoding="utf-8")
    append_session_log(workspace, output)
    append_human_blockers(workspace)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
