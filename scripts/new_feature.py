#!/usr/bin/env python3
"""Create a numbered feature spec folder and set it as active."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from feature_paths import (
    feature_artifact_paths,
    feature_dir_name,
    features_dir,
    next_feature_id,
    set_active_feature,
    slugify,
)
from workspace_utils import ROOT, resolve_workspace


TEMPLATES = {
    "spec": "feature_spec.template.md",
    "clarifications": "feature_clarifications.template.md",
    "feature_plan": "feature_plan.template.md",
    "tasks": "feature_tasks.template.md",
    "research": "feature_research.template.md",
    "checklist": "feature_spec_checklist.template.md",
}


def load_template(name: str) -> str:
    path = ROOT / "templates" / name
    if not path.exists():
        return f"# {name}\n\n"
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def create_feature(workspace: Path, title: str, feature_id: str | None, step: str, force: bool) -> Path:
    fid = feature_id or next_feature_id(workspace)
    if not re.match(r"^\d{3}$", fid):
        raise SystemExit("feature id must be three digits, e.g. 001")
    name = feature_dir_name(fid, title)
    feat = features_dir(workspace) / name
    if feat.exists() and not force:
        raise SystemExit(f"Feature folder already exists: {feat}. Use --force to refresh templates.")
    feat.mkdir(parents=True, exist_ok=True)
    (feat / "contracts").mkdir(exist_ok=True)

    today = date.today().isoformat()
    values = {
        "FEATURE_ID": fid,
        "FEATURE_TITLE": title,
        "FEATURE_SLUG": slugify(title),
        "STEP_REF": step or "link to plan/step_XX when known",
        "DATE": today,
    }

    for key, tmpl in TEMPLATES.items():
        dest = feature_artifact_paths(feat)[key if key != "feature_plan" else "feature_plan"]
        if key == "checklist":
            dest = feature_artifact_paths(feat)["checklist"]
        if dest.exists() and not force:
            continue
        dest.write_text(render(load_template(tmpl), values), encoding="utf-8")

    rel = feat.relative_to(workspace).as_posix()
    set_active_feature(workspace, rel, title, fid)

    readme = features_dir(workspace) / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Feature specs\n\n"
            "Each folder is one buildable feature: spec → clarify → feature-plan → tasks → develop.\n\n"
            "Active feature: `.loop/active-feature.json`\n",
            encoding="utf-8",
        )
    return feat


def main() -> int:
    parser = argparse.ArgumentParser(description="Create plan/features/NNN-slug/ and set active.")
    parser.add_argument("title", nargs="?", default=None, help='Feature title e.g. "auth login"')
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--id", default=None, help="Feature id e.g. 001")
    parser.add_argument("--step", default="", help="Related plan/step_XX file reference")
    parser.add_argument("--force", action="store_true", help="Overwrite template files")
    parser.add_argument("--list", action="store_true", help="List features")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)

    if args.list:
        from feature_paths import list_features

        for item in list_features(workspace):
            mark = " *" if item["active"] else ""
            print(f"{item['name']}{mark}\t{item['path']}")
        return 0

    if not args.title:
        raise SystemExit("title required unless --list")

    feat = create_feature(workspace, args.title, args.id, args.step, args.force)
    rel = feat.relative_to(workspace)
    print(f"Created {rel}")
    print(f"Active feature: {workspace / '.loop' / 'active-feature.json'}")
    print("Next: fill spec.md -> /spec-clarify -> /spec-checklist -> feature-plan.md -> /product-develop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
