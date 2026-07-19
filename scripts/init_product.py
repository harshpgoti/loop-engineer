#!/usr/bin/env python3
"""Initialize product-specific planning files from templates.

Agents can call this during `/plan-loop` after gathering the user's product inputs.
It is intentionally conservative: it refuses to overwrite initialized files
unless `--force` is supplied.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from deployment_topics import TOPICS, append_decisions, template_values
from workspace_utils import resolve_workspace


ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "product-step"


def read_template(name: str) -> str:
    return (ROOT / "templates" / name).read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        existing = path.read_text(encoding="utf-8", errors="ignore")
        if "UNINITIALIZED" not in existing and "TBD" not in existing:
            raise SystemExit(f"Refusing to overwrite initialized file without --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_session_log(workspace: Path, product_name: str, step_file: Path) -> None:
    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} - Product initialized\n\n"
            f"- Product: {product_name}\n"
            f"- Created/updated: `{step_file.relative_to(workspace)}`\n"
            "- Next: run `/plan-loop` to validate assumptions or `/product-develop` after gates pass.\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize Loop Engineering OS product files.")
    parser.add_argument("--name", required=True, help="Product name")
    parser.add_argument("--description", default="TBD", help="One-line product description")
    parser.add_argument("--target-user", default="TBD", help="Target user")
    parser.add_argument("--buyer", default="TBD", help="Buyer or decision-maker")
    parser.add_argument("--problem", default="TBD", help="Problem being solved")
    parser.add_argument("--first-step", required=True, help="First product step/module")
    parser.add_argument("--constraints", default="TBD", help="Known constraints")
    parser.add_argument("--sensitive-data", default="TBD", help="Sensitive data/compliance notes")
    parser.add_argument("--stack", default="TBD", help="Preferred stack")
    parser.add_argument("--cloud-provider", default="TBD", help="Cloud provider")
    parser.add_argument("--cloud-strategy", default="TBD", help="Single-cloud or multi-cloud")
    parser.add_argument("--regions", default="TBD", help="Primary region(s)")
    parser.add_argument("--compute-model", default="TBD", help="Compute model")
    parser.add_argument("--database-hosting", default="TBD", help="Database hosting")
    parser.add_argument("--llm-provider", default="TBD", help="LLM provider")
    parser.add_argument("--llm-models", default="TBD", help="LLM model(s)")
    parser.add_argument("--embedding-model", default="TBD", help="Embedding provider/model")
    parser.add_argument("--agent-runtime", default="TBD", help="Agent runtime")
    parser.add_argument("--cicd-platform", default="TBD", help="CI/CD platform")
    parser.add_argument("--secrets-management", default="TBD", help="Secrets management")
    parser.add_argument("--repo-strategy", default="TBD", help="Product repo strategy")
    parser.add_argument("--evidence-status", default="None yet", help="Evidence status")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Product workspace where main_plan.md and plan/ live. Defaults to registered current workspace or current directory.",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite initialized files")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    step_slug = slugify(args.first_step)
    step_file = workspace / "plan" / f"step_01_{step_slug}.md"

    deployment_overrides = {
        "cloud_provider": args.cloud_provider,
        "cloud_strategy": args.cloud_strategy,
        "regions": args.regions,
        "compute_model": args.compute_model,
        "database_hosting": args.database_hosting,
        "llm_provider": args.llm_provider,
        "llm_models": args.llm_models,
        "embedding_model": args.embedding_model,
        "agent_runtime": args.agent_runtime,
        "cicd_platform": args.cicd_platform,
        "secrets_management": args.secrets_management,
    }

    values = {
        "PRODUCT_NAME": args.name,
        "ONE_LINE_DESCRIPTION": args.description,
        "TARGET_USER": args.target_user,
        "BUYER": args.buyer,
        "PROBLEM": args.problem,
        "FIRST_STEP": args.first_step,
        "STEP_NUMBER": "01",
        "STEP_NAME": args.first_step,
        "STEP_SLUG": step_slug,
        "STEP_PURPOSE": args.problem,
        "CONSTRAINTS": args.constraints,
        "SENSITIVE_DATA": args.sensitive_data,
        "PREFERRED_STACK": args.stack,
        "PRODUCT_THESIS": args.description,
        "PRODUCT_REPO_STRATEGY": args.repo_strategy,
        "EVIDENCE_STATUS": args.evidence_status,
        "SENSITIVE_DATA_POLICY": args.sensitive_data,
    }
    values.update(template_values(deployment_overrides))

    main_plan = render(read_template("main_plan.template.md"), values)
    step_plan = render(read_template("step_plan.template.md"), values)

    main_plan_path = workspace / "plan" / "main_plan.md"
    main_plan_path.parent.mkdir(parents=True, exist_ok=True)
    write_file(main_plan_path, main_plan, args.force)
    write_file(step_file, step_plan, args.force)

    recorded = {
        topic.label: deployment_overrides[topic.key]
        for topic in TOPICS
        if deployment_overrides.get(topic.key, "TBD") not in ("", "TBD")
    }
    append_decisions(workspace, recorded)
    append_session_log(workspace, args.name, step_file)

    print(f"Initialized product plan for {args.name}")
    print(f"Workspace: {workspace}")
    print(f"Created/updated {step_file.relative_to(workspace)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
