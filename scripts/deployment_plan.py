#!/usr/bin/env python3
"""Create or refresh DEPLOYMENT_PLAN.md from product decisions and open deployment questions."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from deployment_topics import TOPICS, find_topic_value, template_values
from workspace_utils import ROOT, resolve_workspace


STATE_FILES = [
    "main_plan.md",
    "DECISIONS.md",
    "DOUBTS.md",
    "MEMORY.md",
    "GATES.yml",
    "plan/PROD-GAP.md",
    "RELEASE_CHECK.md",
]


def read_text(path: Path, max_chars: int = 8000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n_...truncated_"


def collect_corpus(workspace: Path) -> dict[str, str]:
    from memory_paths import main_plan_file, memory_file

    corpus: dict[str, str] = {}
    corpus["main_plan.md"] = read_text(main_plan_file(workspace))
    corpus["MEMORY.md"] = read_text(memory_file(workspace))
    for rel in ("DECISIONS.md", "DOUBTS.md", "EVIDENCE_LOG.md", "HANDOFF.md"):
        corpus[rel] = read_text(workspace / rel)
    step_text: list[str] = []
    plan_dir = workspace / "plan"
    if plan_dir.exists():
        for step in sorted(plan_dir.glob("step_*.md")):
            step_text.append(read_text(step, 4000))
    corpus["plan/step_*.md"] = "\n\n".join(step_text)
    return corpus


def extract_line(text: str, prefix: str, default: str = "") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def doubt_exists(doubt_id: str, doubts_text: str) -> bool:
    return doubt_id.lower() in doubts_text.lower()


def append_open_doubts(workspace: Path, open_topics: list) -> None:
    if not open_topics:
        return
    doubts_path = workspace / "DOUBTS.md"
    existing = read_text(doubts_path)
    additions: list[str] = []
    for topic in open_topics:
        if doubt_exists(topic.doubt_id, existing):
            continue
        additions.append(
            f"\n### {topic.doubt_id}: {topic.label}\n"
            f"- **Status:** open\n"
            f"- **Question:** {topic.question}\n"
            f"- **Why it matters:** Production deployment, infrastructure, and release planning depend on it.\n"
            f"- **Default if unavailable:** Record as TBD in `main_plan.md`, `DEPLOYMENT_PLAN.md`, and do not assume a cloud or LLM vendor.\n"
        )
    if additions:
        with doubts_path.open("a", encoding="utf-8") as handle:
            handle.write("\n## Deployment Questions\n")
            handle.writelines(additions)


def append_handoff_note(workspace: Path, open_count: int, confirmed_count: int, source: str = "loop") -> None:
    handoff_path = workspace / "HANDOFF.md"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    note = (
        "\n"
        f"## {date.today().isoformat()} - Deployment plan updated ({source})\n\n"
        "- Updated `DEPLOYMENT_PLAN.md`.\n"
        f"- Reused {confirmed_count} previously discussed deployment decision(s).\n"
    )
    if open_count:
        note += (
            f"- {open_count} deployment question(s) still need user input. Review **Open Questions For User** in `DEPLOYMENT_PLAN.md` and `DOUBTS.md`.\n"
            "- Ask the user directly for unresolved cloud, LLM, and deployment choices.\n"
        )
    else:
        note += "- All tracked deployment questions are currently resolved or inferred from prior decisions.\n"
    with handoff_path.open("a", encoding="utf-8") as handle:
        handle.write(note)


def bullet(items: list[str]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def load_template() -> str:
    return (ROOT / "templates" / "deployment_plan.template.md").read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def analyze(workspace: Path, source: str = "loop") -> str:
    corpus = collect_corpus(workspace)
    main_plan = corpus.get("main_plan.md", "")

    product_name = extract_line(main_plan, "- **Name", "Uninitialized")
    confirmed: list[str] = []
    open_questions: list[str] = []
    values: dict[str, str] = {}

    for topic in TOPICS:
        value, value_source = find_topic_value(topic, corpus)
        if value:
            values[topic.key] = value
            values[f"{topic.key}_source"] = f"`{value_source}`"
            confirmed.append(f"**{topic.label}:** {value} (from `{value_source}`)")
        else:
            values[topic.key] = "TBD"
            values[f"{topic.key}_source"] = "Unresolved"
            open_questions.append(f"**{topic.label}:** {topic.question}")

    open_topics = [topic for topic in TOPICS if values[topic.key] == "TBD"]
    append_open_doubts(workspace, open_topics)

    plan_status = "READY FOR REVIEW" if not open_topics else "NEEDS USER INPUT"
    summary = (
        "Generated deployment plan draft from existing product decisions and planning files. "
        f"Reused {len(confirmed)} decision(s). "
        f"{len(open_topics)} question(s) still need user confirmation."
        if open_topics
        else "Generated deployment plan draft. All tracked deployment questions currently have a recorded answer."
    )

    user_actions = open_questions.copy()
    if confirmed:
        user_actions.insert(
            0,
            "Review reused decisions below and confirm they are still correct. Tell the agent if any should change.",
        )

    content = render(
        load_template(),
        {
            "UPDATED_DATE": date.today().isoformat(),
            "PRODUCT_NAME": product_name,
            "PLAN_STATUS": plan_status,
            "EXECUTIVE_SUMMARY": summary,
            "CONFIRMED_DECISIONS": bullet(confirmed) if confirmed else "- None yet. Ask the user for cloud, LLM, and deployment choices.",
            "CLOUD_PROVIDER": values.get("cloud_provider", "TBD"),
            "CLOUD_PROVIDER_SOURCE": values.get("cloud_provider_source", "Unresolved"),
            "CLOUD_STRATEGY": values.get("cloud_strategy", "TBD"),
            "CLOUD_STRATEGY_SOURCE": values.get("cloud_strategy_source", "Unresolved"),
            "REGIONS": values.get("regions", "TBD"),
            "REGIONS_SOURCE": values.get("regions_source", "Unresolved"),
            "COMPUTE_MODEL": values.get("compute_model", "TBD"),
            "COMPUTE_MODEL_SOURCE": values.get("compute_model_source", "Unresolved"),
            "DATABASE_HOSTING": values.get("database_hosting", "TBD"),
            "DATABASE_HOSTING_SOURCE": values.get("database_hosting_source", "Unresolved"),
            "LLM_PROVIDER": values.get("llm_provider", "TBD"),
            "LLM_PROVIDER_SOURCE": values.get("llm_provider_source", "Unresolved"),
            "LLM_MODELS": values.get("llm_models", "TBD"),
            "LLM_MODELS_SOURCE": values.get("llm_models_source", "Unresolved"),
            "EMBEDDING_MODEL": values.get("embedding_model", "TBD"),
            "EMBEDDING_MODEL_SOURCE": values.get("embedding_model_source", "Unresolved"),
            "AGENT_RUNTIME": values.get("agent_runtime", "TBD"),
            "AGENT_RUNTIME_SOURCE": values.get("agent_runtime_source", "Unresolved"),
            "ENVIRONMENTS": bullet(
                [
                    "Development: local or shared dev environment",
                    "Staging: required before production; use synthetic data until sensitive-data gates pass",
                    "Production: gated by `G-RELEASE-01` and `RELEASE_CHECK.md`",
                ]
            ),
            "CICD_PLAN": bullet(
                [
                    f"CI/CD platform: {values.get('cicd_platform', 'TBD')}",
                    "Run tests, lint, typecheck, security scans before deploy",
                    "Deploy to staging first, then production with smoke tests",
                ]
            ),
            "SECRETS_AND_CONFIG": bullet(
                [
                    f"Secrets management: {values.get('secrets_management', 'TBD')}",
                    "Use `.env.example` for non-secret config documentation",
                    "Never commit real credentials or customer secrets",
                ]
            ),
            "OBSERVABILITY": bullet(
                [
                    "Add health checks and basic request/error metrics",
                    "Log deployment version and rollback target",
                    "Define on-call or alert path before production launch",
                ]
            ),
            "ROLLBACK_PLAN": bullet(
                [
                    "Keep previous release artifact available",
                    "Document rollback command and database migration rollback rules",
                    "Run smoke tests after rollback",
                ]
            ),
            "PRE_DEPLOY_CHECKLIST": bullet(
                [
                    "`RELEASE_CHECK.md` has no unresolved blockers",
                    "`plan/PROD-GAP.md` has no unresolved P0 launch blockers",
                    "Production secrets and cloud accounts are provisioned",
                    "Monitoring and rollback steps are documented",
                ]
            ),
            "OPEN_QUESTIONS": bullet(open_questions) if open_questions else "- None. Confirm reused decisions with the user.",
            "USER_ACTIONS": bullet(user_actions),
            "SOURCE_FILES": bullet([f"`{item}`" for item in STATE_FILES]),
        },
    )

    append_handoff_note(workspace, len(open_topics), len(confirmed), source=source)
    return content


def append_session_log(workspace: Path, source: str) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} - Deployment plan updated ({source})\n\n"
            "- Updated `DEPLOYMENT_PLAN.md`.\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write DEPLOYMENT_PLAN.md for a product workspace.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    parser.add_argument("--source", default="loop", help="Source label for handoff/session notes.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    output = workspace / "DEPLOYMENT_PLAN.md"
    output.write_text(analyze(workspace, source=args.source), encoding="utf-8")
    append_session_log(workspace, args.source)
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
