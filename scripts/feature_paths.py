"""Feature spec paths and active-feature resolution."""

from __future__ import annotations

import json
import re
from pathlib import Path


FEATURES_DIR = "plan/features"
ACTIVE_FILE = ".loop/active-feature.json"


def features_dir(workspace: Path) -> Path:
    return workspace / "plan" / "features"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "feature"


def next_feature_id(workspace: Path) -> str:
    root = features_dir(workspace)
    if not root.is_dir():
        return "001"
    nums: list[int] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        match = re.match(r"^(\d{3})-", child.name)
        if match:
            nums.append(int(match.group(1)))
    n = max(nums, default=0) + 1
    return f"{n:03d}"


def feature_dir_name(feature_id: str, title: str) -> str:
    return f"{feature_id}-{slugify(title)}"


def feature_path(workspace: Path, feature_id: str, title: str) -> Path:
    return features_dir(workspace) / feature_dir_name(feature_id, title)


def active_feature_meta_path(workspace: Path) -> Path:
    return workspace / ACTIVE_FILE


def read_active_feature(workspace: Path) -> dict | None:
    path = active_feature_meta_path(workspace)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    rel = data.get("path")
    if not rel:
        return None
    feat = workspace / rel.replace("/", "\\") if "\\" in str(workspace) else workspace / rel
    if not feat.is_dir():
        return None
    data["abs_path"] = str(feat)
    return data


def set_active_feature(workspace: Path, feature_rel: str, title: str, feature_id: str) -> None:
    path = active_feature_meta_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "id": feature_id,
        "title": title,
        "path": feature_rel.replace("\\", "/"),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def feature_artifact_paths(feature_root: Path) -> dict[str, Path]:
    return {
        "spec": feature_root / "spec.md",
        "clarifications": feature_root / "clarifications.md",
        "feature_plan": feature_root / "feature-plan.md",
        "tasks": feature_root / "tasks.md",
        "research": feature_root / "research.md",
        "checklist": feature_root / "spec-checklist.md",
        "converge": feature_root / "converge-report.md",
        "contracts": feature_root / "contracts",
    }


def list_features(workspace: Path) -> list[dict]:
    root = features_dir(workspace)
    if not root.is_dir():
        return []
    active = read_active_feature(workspace)
    active_path = active.get("path") if active else None
    items: list[dict] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name == "README.md":
            continue
        rel = child.relative_to(workspace).as_posix()
        items.append(
            {
                "id": child.name.split("-", 1)[0],
                "name": child.name,
                "path": rel,
                "active": rel == active_path,
                "has_spec": (child / "spec.md").exists(),
                "has_tasks": (child / "tasks.md").exists(),
            }
        )
    return items


def session_bootstrap_feature_paths(workspace: Path) -> list[Path]:
    active = read_active_feature(workspace)
    if not active:
        return []
    feat = Path(active["abs_path"])
    paths: list[Path] = []
    for key in ("spec", "clarifications", "feature_plan", "tasks", "research", "checklist"):
        p = feature_artifact_paths(feat)[key]
        if p.exists():
            paths.append(p)
    return paths
