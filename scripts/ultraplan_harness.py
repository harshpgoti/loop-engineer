#!/usr/bin/env python3
"""Platform-scale ultraplan harness: decompose, init deep step packs, track status."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from plan_paths import (
    SCALE_PLATFORM,
    TEMPLATE_MAP,
    ULTRAPLAN_ARTIFACTS,
    list_step_files,
    parse_step_id,
    product_map_file,
    scale_file,
    slugify,
    step_file_name,
    step_folder_name,
    step_ultraplan_dir,
    steps_dir,
    ultraplan_status_file,
)
from workspace_utils import ROOT, resolve_workspace


def load_template(name: str) -> str:
    path = ROOT / "templates" / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"# {name}\n\n"


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def read_scale(workspace: Path) -> str:
    path = scale_file(workspace)
    if not path.exists():
        return "convenient"
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "**Scale:** `platform`" in text or "Scale:** `platform`" in text:
        return SCALE_PLATFORM
    if "scale: platform" in text.lower():
        return SCALE_PLATFORM
    return "convenient"


def parse_product_map(workspace: Path) -> list[dict]:
    path = product_map_file(workspace)
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip().startswith("|"):
            continue
        if re.match(r"^\|\s*ID\s*\|", line, re.I) or re.match(r"^\|[-:\s|]+\|$", line):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        step_id = parts[0].zfill(2) if parts[0].isdigit() else parts[0]
        rows.append(
            {
                "id": step_id,
                "type": parts[2] if len(parts) > 2 else "module",
                "title": parts[3] if len(parts) > 3 else parts[1],
                "depends": parts[4] if len(parts) > 4 else "",
                "status": parts[5] if len(parts) > 5 else "outline",
            }
        )
    return rows


def ensure_product_map_template(workspace: Path, product_name: str) -> Path:
    path = product_map_file(workspace)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmpl = load_template("product_map.template.md")
    path.write_text(
        render(
            tmpl,
            {"PRODUCT_NAME": product_name or "Product", "DATE": date.today().isoformat()},
        ),
        encoding="utf-8",
    )
    return path


def init_ultraplan_folder(workspace: Path, step_id: str, title: str, module_type: str) -> Path:
    folder = step_ultraplan_dir(workspace, step_id, title)
    folder.mkdir(parents=True, exist_ok=True)
    values = {
        "STEP_ID": step_id,
        "STEP_TITLE": title,
        "MODULE_TYPE": module_type,
        "DATE": date.today().isoformat(),
    }
    for artifact in ULTRAPLAN_ARTIFACTS:
        dest = folder / f"{artifact}.md"
        if dest.exists():
            continue
        tmpl_name = TEMPLATE_MAP.get(artifact, "ultraplan_overview.template.md")
        dest.write_text(render(load_template(tmpl_name), values), encoding="utf-8")
    return folder


def write_step_index(workspace: Path, step_id: str, title: str, module_type: str, folder: Path) -> Path:
    rel_folder = folder.relative_to(workspace).as_posix()
    step_path = workspace / "plan" / step_file_name(step_id, title)
    content = f"""# Step {step_id} - {title}

## Status

Planning (platform ultraplan).

## Module type

`{module_type}` - sub-product / module in the platform map.

## Purpose

Deep planning lives in `{rel_folder}/`. This file is the step index only.

## Ultraplan pack

| Doc | Path | Status |
|-----|------|--------|
| Overview | `{rel_folder}/overview.md` | outline |
| PRD | `{rel_folder}/prd.md` | outline |
| Architecture | `{rel_folder}/architecture.md` | outline |
| Agents | `{rel_folder}/agents.md` | outline |
| Data model | `{rel_folder}/data-model.md` | outline |
| Integrations | `{rel_folder}/integrations.md` | outline |
| Risks | `{rel_folder}/risks.md` | outline |
| Acceptance | `{rel_folder}/acceptance.md` | outline |

## Next

Run `skills/plan-loop/phases/ultraplan.md` on this step until all ultraplan docs pass checklist.
Then `loop feature new "{title}" --step plan/{step_path.name}`.
"""
    step_path.parent.mkdir(parents=True, exist_ok=True)
    if not step_path.exists():
        step_path.write_text(content, encoding="utf-8")
    return step_path


def decompose_from_map(workspace: Path, force: bool = False) -> list[dict]:
    modules = parse_product_map(workspace)
    if not modules:
        raise SystemExit("No modules in PRODUCT_MAP.md - fill the table first.")

    created: list[dict] = []
    for mod in modules:
        sid = mod["id"].zfill(2) if mod["id"].isdigit() else mod["id"]
        title = mod["title"]
        folder = init_ultraplan_folder(workspace, sid, title, mod.get("type", "module"))
        step_path = write_step_index(workspace, sid, title, mod.get("type", "module"), folder)
        created.append({"id": sid, "title": title, "step": str(step_path.relative_to(workspace)), "folder": str(folder.relative_to(workspace))})
    update_ultraplan_status(workspace, created)
    return created


def decompose_from_list(workspace: Path, modules: list[str], types: list[str] | None = None) -> list[dict]:
    """Create PRODUCT_MAP and decompose from module titles."""
    ensure_product_map_template(workspace, read_product_name(workspace))
    lines = [
        "# Product Map",
        "",
        f"**Updated:** {date.today().isoformat()}",
        "",
        "One row per sub-product, agent, or major module.",
        "",
        "| ID | Step file | Type | Title | Depends on | Ultraplan status |",
        "|----|-----------|------|-------|------------|------------------|",
    ]
    for idx, title in enumerate(modules, start=1):
        sid = f"{idx:02d}"
        mtype = (types[idx - 1] if types and idx - 1 < len(types) else "module")
        lines.append(f"| {sid} | step_{sid} | {mtype} | {title} | | outline |")
    lines.append("")
    product_map_file(workspace).write_text("\n".join(lines), encoding="utf-8")
    return decompose_from_map(workspace)


def read_product_name(workspace: Path) -> str:
    from memory_paths import main_plan_file

    main = main_plan_file(workspace)
    if not main.exists():
        return "Product"
    for line in main.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip().startswith("- **Name:**"):
            return line.split(":", 1)[-1].strip() or "Product"
    return "Product"


def artifact_complete(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    if "tbd" in lower:
        return False
    if "fill " in lower and "session" in lower:
        return False
    # Require substantive content beyond template headings
    body = re.sub(r"^#.+$", "", text, flags=re.MULTILINE)
    body = re.sub(r"^\|.+\|$", "", body, flags=re.MULTILINE)
    if len(body.strip()) < 80:
        return False
    return True


def step_ultraplan_complete(workspace: Path, step_id: str, title: str) -> tuple[bool, list[str]]:
    folder = step_ultraplan_dir(workspace, step_id, title)
    missing: list[str] = []
    for artifact in ULTRAPLAN_ARTIFACTS:
        if artifact == "agents":
            continue  # optional unless type is agent
        path = folder / f"{artifact}.md"
        if not artifact_complete(path):
            missing.append(artifact)
    return (len(missing) == 0, missing)


def update_ultraplan_status(workspace: Path, modules: list[dict] | None = None) -> Path:
    if modules is None:
        modules = []
        for step in list_step_files(workspace):
            sid = parse_step_id(step.name)
            if not sid:
                continue
            title_match = re.match(r"step_\d{2}_(.+)\.md", step.name)
            title = (title_match.group(1) if title_match else step.stem).replace("-", " ")
            folder = steps_dir(workspace) / step_folder_name(sid, title)
            if not folder.is_dir():
                alt = next((d for d in steps_dir(workspace).glob(f"{sid}-*") if d.is_dir()), None)
                folder = alt or folder
            complete, missing = step_ultraplan_complete(workspace, sid, title) if folder.is_dir() else (False, ["folder"])
            modules.append({"id": sid, "title": title, "complete": complete, "missing": missing})

    lines = [
        "# Ultraplan Status",
        "",
        f"**Updated:** {date.today().isoformat()}",
        "",
        "Platform-scale planning progress. Each step needs a full pack under `plan/steps/NN-slug/`.",
        "",
        "| Step | Title | Ultraplan | Missing artifacts |",
        "|------|-------|-----------|-------------------|",
    ]
    for mod in modules:
        sid = mod["id"]
        title = mod.get("title", sid)
        if "complete" in mod:
            status = "complete" if mod["complete"] else "in progress"
            missing = ", ".join(mod.get("missing", [])) or "-"
        else:
            complete, missing_list = step_ultraplan_complete(workspace, sid, title)
            status = "complete" if complete else "outline"
            missing = ", ".join(missing_list) if missing_list else "-"
        lines.append(f"| {sid} | {title} | {status} | {missing} |")
    lines.extend(["", "## Next step", ""])
    next_step = find_next_incomplete(workspace, modules)
    if next_step:
        lines.append(f"- Deep-plan **step {next_step['id']} - {next_step['title']}** (`skills/plan-loop/phases/ultraplan.md`)")
    else:
        lines.append("- All ultraplan packs complete - run task-compiler per step or `/product-develop`.")
    lines.append("")
    path = ultraplan_status_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def find_next_incomplete(workspace: Path, modules: list[dict] | None = None) -> dict | None:
    if modules is None:
        modules = parse_product_map(workspace)
    for mod in modules:
        sid = mod["id"].zfill(2) if str(mod["id"]).isdigit() else str(mod["id"])
        title = mod["title"]
        complete, _ = step_ultraplan_complete(workspace, sid, title)
        if not complete:
            return {"id": sid, "title": title}
    for step in list_step_files(workspace):
        sid = parse_step_id(step.name)
        if not sid:
            continue
        m = re.match(r"step_\d{2}_(.+)\.md", step.name)
        title = m.group(1).replace("-", " ") if m else step.stem
        folder = steps_dir(workspace) / step_folder_name(sid, title)
        if not folder.is_dir():
            return {"id": sid, "title": title}
        complete, _ = step_ultraplan_complete(workspace, sid, title)
        if not complete:
            return {"id": sid, "title": title}
    return None


def init_single_step(workspace: Path, step_id: str, title: str, module_type: str = "module") -> dict:
    folder = init_ultraplan_folder(workspace, step_id, title, module_type)
    step_path = write_step_index(workspace, step_id, title, module_type, folder)
    update_ultraplan_status(workspace)
    return {
        "step": step_path.relative_to(workspace).as_posix(),
        "folder": folder.relative_to(workspace).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ultraplan harness for platform-scale products.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    decompose = sub.add_parser("decompose", help="Materialize steps + ultraplan folders from PRODUCT_MAP.md")
    decompose.add_argument("--force", action="store_true")

    modules_p = sub.add_parser("modules", help="Create PRODUCT_MAP from module list and decompose")
    modules_p.add_argument("titles", nargs="+", help='Module titles e.g. "Support agent" "Admin portal"')
    modules_p.add_argument("--types", nargs="*", default=None, help="Types: agent, product, service, module")

    init_p = sub.add_parser("init", help="Init ultraplan pack for one step")
    init_p.add_argument("--id", required=True, help="Step id e.g. 01")
    init_p.add_argument("--title", required=True)
    init_p.add_argument("--type", default="module")

    sub.add_parser("status", help="Refresh plan/ULTRAPLAN_STATUS.md")
    sub.add_parser("next", help="Print next step needing ultraplan")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if args.cmd == "decompose":
        created = decompose_from_map(workspace, force=args.force)
        for item in created:
            print(f"{item['id']}\t{item['title']}\t{item['folder']}")
        print(f"Decomposed {len(created)} modules")
        return 0

    if args.cmd == "modules":
        created = decompose_from_list(workspace, args.titles, args.types)
        scale_path = scale_file(workspace)
        from plan_scale import render_scale_report

        scale_path.parent.mkdir(parents=True, exist_ok=True)
        scale_path.write_text(
            render_scale_report(workspace, {"scale": SCALE_PLATFORM, "score": 99, "reasons": ["module list bootstrap"], "step_count": len(created), "signals": 0, "bullets": 0}),
            encoding="utf-8",
        )
        for item in created:
            print(f"{item['id']}\t{item['title']}")
        return 0

    if args.cmd == "init":
        result = init_single_step(workspace, args.id.zfill(2), args.title, args.type)
        print(f"Created {result['folder']}")
        return 0

    if args.cmd == "status":
        path = update_ultraplan_status(workspace)
        print(f"Wrote {path}")
        return 0

    if args.cmd == "next":
        nxt = find_next_incomplete(workspace)
        if not nxt:
            print("All ultraplan packs complete (or no platform steps).")
            return 0
        print(f"Next: step {nxt['id']} - {nxt['title']}")
        folder = step_ultraplan_dir(workspace, nxt["id"], nxt["title"])
        print(f"Folder: {folder.relative_to(workspace)}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
