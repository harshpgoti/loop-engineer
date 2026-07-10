"""Paths and constants for plan scale and ultraplan harness."""

from __future__ import annotations

import re
from pathlib import Path


PLAN_SCALE_FILE = "plan/PLAN_SCALE.md"
PRODUCT_MAP_FILE = "plan/PRODUCT_MAP.md"
ULTRAPLAN_STATUS_FILE = "plan/ULTRAPLAN_STATUS.md"
STEPS_DIR = "plan/steps"

SCALE_CONVENIENT = "convenient"
SCALE_PLATFORM = "platform"

ULTRAPLAN_ARTIFACTS = (
    "overview",
    "prd",
    "architecture",
    "agents",
    "data-model",
    "integrations",
    "risks",
    "acceptance",
)

TEMPLATE_MAP = {
    "overview": "ultraplan_overview.template.md",
    "prd": "ultraplan_prd.template.md",
    "architecture": "ultraplan_architecture.template.md",
    "agents": "ultraplan_agents.template.md",
    "data-model": "ultraplan_data.template.md",
    "integrations": "ultraplan_integrations.template.md",
    "risks": "ultraplan_risks.template.md",
    "acceptance": "ultraplan_acceptance.template.md",
}


def plan_dir(workspace: Path) -> Path:
    return workspace / "plan"


def steps_dir(workspace: Path) -> Path:
    return workspace / "plan" / "steps"


def scale_file(workspace: Path) -> Path:
    return workspace / PLAN_SCALE_FILE


def product_map_file(workspace: Path) -> Path:
    return workspace / PRODUCT_MAP_FILE


def ultraplan_status_file(workspace: Path) -> Path:
    return workspace / ULTRAPLAN_STATUS_FILE


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "module"


def step_file_name(step_id: str, title: str) -> str:
    return f"step_{step_id}_{slugify(title)}.md"


def step_folder_name(step_id: str, title: str) -> str:
    return f"{step_id}-{slugify(title)}"


def step_ultraplan_dir(workspace: Path, step_id: str, title: str) -> Path:
    return steps_dir(workspace) / step_folder_name(step_id, title)


def list_step_files(workspace: Path) -> list[Path]:
    root = plan_dir(workspace)
    if not root.is_dir():
        return []
    return sorted(root.glob("step_*.md"))


def parse_step_id(filename: str) -> str | None:
    match = re.match(r"step_(\d{2})_", filename)
    return match.group(1) if match else None
