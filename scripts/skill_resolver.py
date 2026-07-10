"""Resolve canonical vs user skills with product-workspace priority."""

from __future__ import annotations

from pathlib import Path

from memory_paths import user_skills_dir
from workspace_utils import ROOT


def canonical_skills_dir() -> Path:
    return ROOT / "skills"


def list_skills(workspace: Path | None = None) -> list[dict]:
    entries: dict[str, dict] = {}

    for skill_path in sorted(canonical_skills_dir().glob("*/SKILL.md")):
        name = skill_path.parent.name
        entries[name] = {
            "name": name,
            "source": "canonical",
            "path": str(skill_path.relative_to(ROOT)),
        }

    if workspace is not None:
        for skill_path in sorted(user_skills_dir(workspace).glob("**/SKILL.md")):
            name = skill_path.parent.name
            try:
                rel = skill_path.relative_to(workspace).as_posix()
            except ValueError:
                rel = str(skill_path)
            entries[name] = {
                "name": name,
                "source": "user",
                "path": rel,
            }

    return sorted(entries.values(), key=lambda item: item["name"])


def resolve_skill(name: str, workspace: Path | None = None) -> Path | None:
    if workspace is not None:
        for skill_path in user_skills_dir(workspace).glob(f"**/{name}/SKILL.md"):
            return skill_path
    canonical = canonical_skills_dir() / name / "SKILL.md"
    if canonical.exists():
        return canonical
    return None


def validate_user_skills(workspace: Path) -> list[str]:
    issues: list[str] = []
    for skill_path in sorted(user_skills_dir(workspace).glob("**/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8", errors="ignore")
        rel = skill_path.relative_to(workspace)
        if not text.startswith("---\n"):
            issues.append(f"User skill missing YAML frontmatter: `{rel}`")
            continue
        frontmatter = text.split("---", 2)[1]
        if "name:" not in frontmatter or "description:" not in frontmatter:
            issues.append(f"User skill frontmatter needs name and description: `{rel}`")
    return issues


def bootstrap_skill_paths(workspace: Path) -> list[str]:
    lines = ["## Skill Resolution Order", "", "1. Product workspace `skills/` (highest priority)", "2. Tool canonical `loop-engineer/skills/`", ""]
    for item in list_skills(workspace):
        lines.append(f"- `{item['name']}` — {item['source']} — `{item['path']}`")
    auto = workspace / "plan" / "AUTO_SKILLS.md"
    if auto.exists():
        lines.extend(["", "## Auto-selected frontend skills", "", f"Read `{auto.relative_to(workspace).as_posix()}` (from `frontend_skill_router.py`)."])
    return lines
