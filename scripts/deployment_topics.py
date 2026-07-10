"""Shared deployment topic definitions and helpers for planning and release workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class DeploymentTopic:
    key: str
    label: str
    question: str
    doubt_id: str
    patterns: list[str]
    default: str = "TBD"
    main_plan_label: str = ""


def _label(label: str) -> str:
    return label


TOPICS: list[DeploymentTopic] = [
    DeploymentTopic(
        key="cloud_provider",
        label="Cloud provider",
        question="Which cloud provider will we use (AWS, GCP, Azure, Vercel, Fly.io, other)?",
        doubt_id="DQ-DEP-001",
        main_plan_label="Cloud provider",
        patterns=[
            r"\baws\b",
            r"\bamazon web services\b",
            r"\bgcp\b",
            r"\bgoogle cloud\b",
            r"\bazure\b",
            r"\bvercel\b",
            r"\bfly\.io\b",
            r"\brailway\b",
            r"\brender\b",
            r"\bdigitalocean\b",
            r"\bcloudflare\b",
            r"\bon[- ]prem(?:ises)?\b",
        ],
    ),
    DeploymentTopic(
        key="cloud_strategy",
        label="Cloud strategy",
        question="Will deployment be single-cloud or multi-cloud?",
        doubt_id="DQ-DEP-002",
        main_plan_label="Cloud strategy",
        patterns=[r"\bmulti[- ]cloud\b", r"\bsingle[- ]cloud\b", r"\bhybrid cloud\b"],
    ),
    DeploymentTopic(
        key="regions",
        label="Primary region(s)",
        question="Which region(s) should production run in?",
        doubt_id="DQ-DEP-003",
        main_plan_label="Primary region(s)",
        patterns=[
            r"\bus-east-\d\b",
            r"\bus-west-\d\b",
            r"\beu-west-\d\b",
            r"\beu-central-\d\b",
            r"\bap-south-\d\b",
            r"\bregion[: ]+[a-z0-9-]+",
        ],
    ),
    DeploymentTopic(
        key="compute_model",
        label="Compute model",
        question="What compute model should we use (containers, serverless, VMs, PaaS)?",
        doubt_id="DQ-DEP-004",
        main_plan_label="Compute model",
        patterns=[
            r"\bserverless\b",
            r"\bcontainers?\b",
            r"\bkubernetes\b",
            r"\beks\b",
            r"\bgke\b",
            r"\baks\b",
            r"\bvm\b",
            r"\bec2\b",
            r"\bcloud run\b",
            r"\blambda\b",
        ],
    ),
    DeploymentTopic(
        key="database_hosting",
        label="Database hosting",
        question="Where will the primary database be hosted (managed Postgres, RDS, Supabase, PlanetScale, other)?",
        doubt_id="DQ-DEP-005",
        main_plan_label="Database hosting",
        patterns=[
            r"\brds\b",
            r"\bcloud sql\b",
            r"\bsupabase\b",
            r"\bplanetscale\b",
            r"\bpostgres\b",
            r"\bmysql\b",
            r"\bmongodb atlas\b",
            r"\bfirestore\b",
            r"\bdynamodb\b",
        ],
    ),
    DeploymentTopic(
        key="llm_provider",
        label="LLM provider",
        question="Which LLM provider will the product use (OpenAI, Anthropic, Google, Azure OpenAI, local, other)?",
        doubt_id="DQ-DEP-006",
        main_plan_label="LLM provider",
        patterns=[
            r"\bopenai\b",
            r"\banthropic\b",
            r"\bclaude\b",
            r"\bgemini\b",
            r"\bgoogle ai\b",
            r"\bazure openai\b",
            r"\bollama\b",
            r"\blocal llm\b",
            r"\bhugging face\b",
            r"\bbedrock\b",
        ],
    ),
    DeploymentTopic(
        key="llm_models",
        label="LLM model(s)",
        question="Which LLM model(s) should production use?",
        doubt_id="DQ-DEP-007",
        main_plan_label="LLM model(s)",
        patterns=[
            r"\bgpt-[\w.-]+\b",
            r"\bclaude-[\w.-]+\b",
            r"\bgemini-[\w.-]+\b",
            r"\bllama-[\w.-]+\b",
            r"\bmistral-[\w.-]+\b",
        ],
    ),
    DeploymentTopic(
        key="embedding_model",
        label="Embedding provider/model",
        question="Which embedding provider/model should production use?",
        doubt_id="DQ-DEP-008",
        main_plan_label="Embedding provider/model",
        patterns=[
            r"\btext-embedding[-\w.]+\b",
            r"\bembedding model\b",
            r"\bvoyage\b",
            r"\bcohere embed\b",
        ],
    ),
    DeploymentTopic(
        key="agent_runtime",
        label="Agent runtime",
        question="Where will agent loops run in production (backend service, worker queue, serverless, external agent platform)?",
        doubt_id="DQ-DEP-009",
        main_plan_label="Agent runtime",
        patterns=[
            r"\bworker queue\b",
            r"\bcelery\b",
            r"\btemporal\b",
            r"\binngest\b",
            r"\bagent runtime\b",
            r"\bbackground worker\b",
        ],
    ),
    DeploymentTopic(
        key="cicd_platform",
        label="CI/CD platform",
        question="Which CI/CD platform should deploy production (GitHub Actions, GitLab CI, CircleCI, other)?",
        doubt_id="DQ-DEP-010",
        main_plan_label="CI/CD platform",
        patterns=[
            r"\bgithub actions\b",
            r"\bgitlab ci\b",
            r"\bcircleci\b",
            r"\bjenkins\b",
            r"\bazure devops\b",
        ],
    ),
    DeploymentTopic(
        key="secrets_management",
        label="Secrets management",
        question="How should production secrets be managed (env vars, AWS Secrets Manager, GCP Secret Manager, Vault, other)?",
        doubt_id="DQ-DEP-011",
        main_plan_label="Secrets management",
        patterns=[
            r"\bsecrets manager\b",
            r"\bsecret manager\b",
            r"\bhashicorp vault\b",
            r"\bvault\b",
            r"\bparameter store\b",
        ],
    ),
]

PLANNING_QUESTION_KEYS = [
    "cloud_provider",
    "cloud_strategy",
    "llm_provider",
    "llm_models",
    "compute_model",
    "database_hosting",
    "cicd_platform",
]


def topic_by_key(key: str) -> DeploymentTopic | None:
    for topic in TOPICS:
        if topic.key == key:
            return topic
    return None


def template_values(overrides: dict[str, str] | None = None) -> dict[str, str]:
    values = {topic.key.upper(): "TBD" for topic in TOPICS}
    if overrides:
        for key, value in overrides.items():
            upper = key.upper()
            if value and value.strip() and value.strip().upper() != "TBD":
                values[upper] = value.strip()
    return values


def parse_main_plan_deployment_table(text: str) -> dict[str, str]:
    section_match = re.search(
        r"## Deployment & Infrastructure(?P<body>.*?)(?:\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not section_match:
        return {}

    parsed: dict[str, str] = {}
    for line in section_match.group("body").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        label, value = cells[0], cells[1]
        if label.lower() in {"item", "------", "---"}:
            continue
        if not value or value.upper() == "TBD":
            continue
        for topic in TOPICS:
            if topic.main_plan_label.lower() == label.lower():
                parsed[topic.key] = value
    return parsed


def extract_line(text: str, prefix: str, default: str = "") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def find_topic_value(topic: DeploymentTopic, corpus: dict[str, str]) -> tuple[str, str]:
    main_plan = corpus.get("main_plan.md", "")
    table_values = parse_main_plan_deployment_table(main_plan)
    if topic.key in table_values:
        return table_values[topic.key], "main_plan.md (Deployment & Infrastructure)"

    for source, text in corpus.items():
        lower = text.lower()
        for pattern in topic.patterns:
            match = re.search(pattern, lower, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 40)
                end = min(len(text), match.end() + 80)
                snippet = " ".join(text[start:end].split())
                return snippet, source

        if topic.key == "cloud_provider":
            for provider in ("AWS", "GCP", "Azure", "Vercel", "Fly.io", "Railway", "Render"):
                if provider.lower() in lower:
                    return provider, source

        if topic.key == "cloud_strategy":
            if "multi-cloud" in lower or "multi cloud" in lower:
                return "Multi-cloud", source
            if "single-cloud" in lower or "single cloud" in lower:
                return "Single-cloud", source

        if topic.key == "llm_provider":
            for provider in ("OpenAI", "Anthropic", "Google", "Azure OpenAI", "Ollama"):
                if provider.lower() in lower:
                    return provider, source

    preferred_stack = extract_line(main_plan, "- **Preferred stack")
    if preferred_stack and preferred_stack != "TBD":
        if topic.key in {"cloud_provider", "compute_model", "database_hosting", "llm_provider"}:
            return preferred_stack, "main_plan.md (Preferred stack)"

    return "", ""


def deployment_table_markdown(values: dict[str, str]) -> str:
    lines = [
        "## Deployment & Infrastructure",
        "",
        "Captured during `/plan`. Reused by `/deployment-plan` unless the user changes it.",
        "",
        "| Item | Choice |",
        "|------|--------|",
    ]
    for topic in TOPICS:
        value = values.get(topic.key, "TBD")
        lines.append(f"| {topic.main_plan_label} | {value} |")
    return "\n".join(lines) + "\n"


def append_decisions(workspace: Path, decisions: dict[str, str]) -> None:
    if not decisions:
        return
    path = workspace / "DECISIONS.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Decision Log\n\n", encoding="utf-8")

    lines = [f"\n## {date.today().isoformat()} — Deployment decisions from /plan\n"]
    for label, value in decisions.items():
        lines.append(f"- **{label}:** {value}\n")
    with path.open("a", encoding="utf-8") as handle:
        handle.writelines(lines)


def planning_questions_markdown() -> str:
    lines = ["## Deployment Questions To Capture During /plan", ""]
    for key in PLANNING_QUESTION_KEYS:
        topic = topic_by_key(key)
        if topic:
            lines.append(f"- **{topic.label}:** {topic.question}")
    lines.append("")
    lines.append("If already answered in `DECISIONS.md` or resolved `DOUBTS.md`, reuse the same answer and inform the user.")
    return "\n".join(lines) + "\n"
