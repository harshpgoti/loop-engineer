"""Resolve product memory file paths with backward-compatible fallbacks."""

from __future__ import annotations

from pathlib import Path

from feature_paths import session_bootstrap_feature_paths


MEMORY_CHAR_LIMIT = 2200
USER_CHAR_LIMIT = 1375
SOUL_CHAR_LIMIT = 1500


def memories_dir(workspace: Path) -> Path:
    return workspace / "memories"


def user_skills_dir(workspace: Path) -> Path:
    return workspace / "skills"


def loop_meta_dir(workspace: Path) -> Path:
    return workspace / ".loop"


def soul_file(workspace: Path) -> Path:
    return memories_dir(workspace) / "SOUL.md"


def memory_file(workspace: Path) -> Path:
    canonical = memories_dir(workspace) / "MEMORY.md"
    if canonical.exists():
        return canonical
    legacy = workspace / "MEMORY.md"
    if legacy.exists():
        return legacy
    return canonical


def main_plan_file(workspace: Path) -> Path:
    """Canonical product plan: plan/main_plan.md (root main_plan.md = legacy fallback)."""
    canonical = workspace / "plan" / "main_plan.md"
    if canonical.exists():
        return canonical
    legacy = workspace / "main_plan.md"
    if legacy.exists():
        return legacy
    return canonical


def user_file(workspace: Path) -> Path:
    canonical = memories_dir(workspace) / "USER.md"
    if canonical.exists():
        return canonical
    legacy = workspace / "USER.md"
    if legacy.exists():
        return legacy
    return canonical


def context_file(workspace: Path) -> Path:
    return workspace / "CONTEXT.md"


def state_db(workspace: Path) -> Path:
    return workspace / "state.db"


def ensure_memory_layout(workspace: Path) -> dict[str, str]:
    """Create memory layout inside a product workspace."""
    actions: dict[str, str] = {}
    mem_dir = memories_dir(workspace)
    mem_dir.mkdir(parents=True, exist_ok=True)
    user_skills_dir(workspace).mkdir(parents=True, exist_ok=True)
    loop_meta_dir(workspace).mkdir(parents=True, exist_ok=True)
    (loop_meta_dir(workspace) / "pending" / "memory").mkdir(parents=True, exist_ok=True)
    (loop_meta_dir(workspace) / "pending" / "skills").mkdir(parents=True, exist_ok=True)

    root_memory = workspace / "MEMORY.md"
    canonical_memory = mem_dir / "MEMORY.md"
    if not canonical_memory.exists():
        if root_memory.exists():
            canonical_memory.write_text(root_memory.read_text(encoding="utf-8"), encoding="utf-8")
            actions["MEMORY.md"] = "copied legacy root MEMORY.md -> memories/MEMORY.md"
        else:
            starter = _load_template("MEMORY.template.md")
            if starter:
                canonical_memory.write_text(starter, encoding="utf-8")
                actions["MEMORY.md"] = "created memories/MEMORY.md from template"
            else:
                canonical_memory.write_text("# Memory\n\n", encoding="utf-8")
                actions["MEMORY.md"] = "created empty memories/MEMORY.md"
    else:
        actions["MEMORY.md"] = "exists"

    user_path = mem_dir / "USER.md"
    if not user_path.exists():
        user_path.write_text(_load_template("USER.template.md") or "# User Profile\n\n", encoding="utf-8")
        actions["USER.md"] = "created memories/USER.md"
    else:
        actions["USER.md"] = "exists"

    soul_path = soul_file(workspace)
    if not soul_path.exists():
        soul_path.write_text(_load_template("SOUL.template.md") or "# SOUL\n\n", encoding="utf-8")
        actions["SOUL.md"] = "created memories/SOUL.md"
    else:
        actions["SOUL.md"] = "exists"

    ctx_path = context_file(workspace)
    if not ctx_path.exists():
        ctx_path.write_text(_load_template("CONTEXT.template.md") or "# Product Context\n\n", encoding="utf-8")
        actions["CONTEXT.md"] = "created CONTEXT.md"
    else:
        actions["CONTEXT.md"] = "exists"

    db_path = state_db(workspace)
    if not db_path.exists():
        actions["state.db"] = "pending-init"
    else:
        actions["state.db"] = "exists"

    skills = user_skills_dir(workspace)
    readme = skills / "README.md"
    if not readme.exists():
        readme.write_text(
            "# User Skills\n\n"
            "Procedural memory for this product workspace. "
            "Tool canonical skills remain in `loop-engineer/skills/`.\n",
            encoding="utf-8",
        )
        actions["skills/"] = "created"
    else:
        actions["skills/"] = "exists"

    return actions


def _load_template(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "templates" / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def session_bootstrap_paths(workspace: Path) -> list[Path]:
    """Session start read order."""
    ordered = [
        workspace / "plan" / "SESSION_MANIFEST.md",
        soul_file(workspace),
        user_file(workspace),
        memory_file(workspace),
        context_file(workspace),
        workspace / "DOUBTS.md",
        main_plan_file(workspace),
        workspace / "HANDOFF.md",
        workspace / "TASKS.yml",
        workspace / "GATES.yml",
        workspace / "plan" / "PLAN_BOOTSTRAP.md",
        workspace / "plan" / "PLAN_SCALE.md",
        workspace / "plan" / "IDEA.md",
        workspace / "plan" / "PRODUCT_MAP.md",
        workspace / "plan" / "ULTRAPLAN_STATUS.md",
    ]
    ordered.extend(session_bootstrap_feature_paths(workspace))
    ordered.extend(
        [
        workspace / "COMPACT.md",
        workspace / "plan" / "SESSION_CLOSEOUT.md",
        workspace / "plan" / "SESSION_RECALL.md",
        workspace / "plan" / "AUTO_SKILLS.md",
        ]
    )
    return [path for path in ordered if path.exists()]


def session_read_paths(workspace: Path) -> list[Path]:
    return session_bootstrap_paths(workspace)
