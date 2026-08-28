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
    find_step_file,
    find_step_folder,
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
from scope_paths import list_scopes


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


MAP_COLUMNS = {
    "id": "id",
    "step file": "step",
    "step": "step",
    "type": "type",
    "kind": "type",
    "title": "title",
    "name": "title",
    "module": "title",
    "scope": "scope",
    "depends on": "depends",
    "depends": "depends",
    "dependencies": "depends",
    "ultraplan status": "status",
    "status": "status",
    "workspace": "workspace",
    "code folder": "code",
    "code": "code",
}

# Column order assumed for a table written without a header row.
LEGACY_MAP_COLUMNS = ("id", "step", "type", "title", "depends", "status")


def _is_separator(line: str) -> bool:
    return bool(re.match(r"^\|[-:\s|]+\|$", line.strip()))


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def map_columns(cells: list[str]) -> dict[str, int] | None:
    """Column name -> index, or None when this header is not a product-map table.

    A map table is recognized by naming both an `ID` and a `Title` column. Other
    tables in the same file - a canonical-paths index, a binding note - are then
    skipped instead of being read as rows.
    """
    mapping: dict[str, int] = {}
    for index, cell in enumerate(cells):
        name = MAP_COLUMNS.get(re.sub(r"[*_`]", "", cell).strip().lower())
        if name and name not in mapping:
            mapping[name] = index
    return mapping if "id" in mapping and "title" in mapping else None


def parse_product_map(workspace: Path) -> list[dict]:
    """Rows of `plan/PRODUCT_MAP.md`, read by column *name*.

    A real map carries extra columns (a founder ranking, a scope note) and often
    more than one table - company programs and product modules kept in a single ID
    space. Both break positional parsing, which silently shifts `title` into
    `depends`; every downstream binding then points at the wrong text, and the
    sub-product that owns the row reports as unmapped. Columns are therefore taken
    from each table's own header, and a table that does not name `ID` and `Title`
    is skipped rather than misread.
    """
    path = product_map_file(workspace)
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows: list[dict] = []
    columns: dict[str, int] | None = None
    saw_header = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or _is_separator(stripped):
            continue

        following = lines[index + 1] if index + 1 < len(lines) else ""
        if _is_separator(following):
            # A header row - it names this table's columns, or marks it as not a map.
            columns = map_columns(_split_row(stripped))
            saw_header = True
            continue

        if columns is None:
            if saw_header:
                continue  # inside a table that is not the product map
            columns = {name: i for i, name in enumerate(LEGACY_MAP_COLUMNS)}

        cells = _split_row(stripped)

        def cell(name: str) -> str:
            idx = columns.get(name)
            return cells[idx] if idx is not None and idx < len(cells) else ""

        raw_id, title = cell("id"), cell("title")
        if not raw_id or not title:
            continue
        rows.append(
            {
                "id": raw_id.zfill(2) if raw_id.isdigit() else raw_id,
                "type": cell("type") or "module",
                "title": title,
                "depends": cell("depends"),
                "status": cell("status") or "outline",
                "scope": cell("scope"),
                "workspace": cell("workspace"),
                "code": cell("code"),
            }
        )
    return rows


def root_ultraplan_modules(workspace: Path) -> list[dict]:
    """Map rows whose deep plan is owned by the root workspace.

    A row bound by `scope.json`, a `plan/products/...` plan path, or an external
    Workspace path delegates planning to that owner. Product maps also use a column
    named "Scope" for prose descriptions, so non-empty alone is not ownership.
    Deferred roadmap rows stay out of the active tracker until promoted.
    """
    try:
        from scope_paths import list_scopes

        delegated_ids = {scope.map_id for scope in list_scopes(workspace) if scope.map_id}
    except ImportError:
        delegated_ids = set()

    modules: list[dict] = []
    for row in parse_product_map(workspace):
        scope_value = str(row.get("scope") or "").strip(" `")
        workspace_value = str(row.get("workspace") or "").strip(" `")
        delegated = (
            row.get("id") in delegated_ids
            or scope_value.startswith("plan/products/")
            or bool(workspace_value)
        )
        if delegated:
            continue
        if is_deferred(row):
            continue
        modules.append(row)
    return modules


def is_deferred(module: dict) -> bool:
    """True only when the current state is deferred, not its transition history."""
    status = re.sub(r"[*_`]", "", str(module.get("status") or "")).strip().lower()
    return status.startswith("deferred")


def scope_for_module(workspace: Path, module: dict):
    """Return the scope that owns a product-map row, using explicit bindings only."""
    row_id = str(module.get("id") or "").zfill(2)
    scope_value = str(module.get("scope") or "").strip(" `").replace("\\", "/").rstrip("/")
    for scope in list_scopes(workspace):
        if scope.map_id and scope.map_id.zfill(2) == row_id:
            return scope
        if scope_value == f"plan/products/{scope.slug}":
            return scope
    return None


def module_plan_dir(workspace: Path, module: dict) -> Path:
    """Canonical deep-plan folder for a map row.

    A sub-product scope is itself the ultraplan pack. Only root-owned programs and
    capabilities use the legacy root ``plan/steps/NN-slug`` location.
    """
    scope = scope_for_module(workspace, module)
    if scope is not None:
        return scope.path
    return step_ultraplan_dir(workspace, str(module["id"]), str(module["title"]))


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
    module = _target_module(parse_product_map(workspace), step_id) or {
        "id": step_id,
        "title": title,
        "type": module_type,
    }
    folder = module_plan_dir(workspace, module)
    scope_owned = scope_for_module(workspace, module) is not None
    # Step identity is the number, not the title. If a folder for this step already
    # exists under an older title-slug, rename it to the new slug (preserving its
    # ultraplan content) instead of creating a duplicate sibling.
    existing = None if scope_owned else find_step_folder(workspace, step_id)
    if existing is not None and existing != folder and not folder.exists():
        folder.parent.mkdir(parents=True, exist_ok=True)
        existing.rename(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if scope_owned:
        (folder / "steps").mkdir(exist_ok=True)
        (folder / "features").mkdir(exist_ok=True)
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

    # Reuse the existing index for this step number instead of duplicating it.
    existing = find_step_file(workspace, step_id)
    if existing is not None and existing != step_path:
        # Preserve any edits: rename to the new slug and repoint folder refs + title.
        text = existing.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(rf"plan/steps/{re.escape(step_id)}-[a-z0-9-]+", rel_folder, text)
        text = re.sub(rf"(?m)^# Step {re.escape(step_id)} - .*$", f"# Step {step_id} - {title}", text, count=1)
        existing.unlink()
        step_path.write_text(text, encoding="utf-8")
        return step_path

    if not step_path.exists():
        step_path.write_text(content, encoding="utf-8")
    return step_path


def decompose_from_map(workspace: Path, force: bool = False) -> list[dict]:
    modules = root_ultraplan_modules(workspace)
    if not modules:
        raise SystemExit("No root-owned active modules in PRODUCT_MAP.md - fill or promote a row first.")

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
    module = _target_module(parse_product_map(workspace), step_id) or {
        "id": step_id,
        "title": title,
    }
    folder = module_plan_dir(workspace, module)
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
        has_map = product_map_file(workspace).exists()
        mapped = root_ultraplan_modules(workspace)
        modules = mapped if mapped else []
        if not has_map:
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
        "Platform-scale planning progress. Each step needs a full pack at its canonical owner folder.",
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
        lines.append("- All ultraplan packs complete - run task-compiler per step or `/develop-product`.")
    lines.append("")
    path = ultraplan_status_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _target_module(modules: list[dict], target: str) -> dict | None:
    wanted = str(target).strip()
    wanted_id = wanted.zfill(2) if wanted.isdigit() else wanted
    wanted_title = slugify(wanted)
    for mod in modules:
        sid = str(mod["id"]).zfill(2) if str(mod["id"]).isdigit() else str(mod["id"])
        if sid == wanted_id or slugify(mod["title"]) == wanted_title:
            return mod
    return None


def find_next_incomplete(
    workspace: Path,
    modules: list[dict] | None = None,
    *,
    target: str | None = None,
) -> dict | None:
    has_map = product_map_file(workspace).exists()
    if modules is None:
        modules = root_ultraplan_modules(workspace)
    if target:
        # An explicit map row may be scope-owned. The user named that scope, so route
        # to its canonical plan folder rather than excluding it as "delegated".
        selected = _target_module(parse_product_map(workspace), target)
        if selected and is_deferred(selected):
            selected = None
        modules = [selected] if selected else []
    for mod in modules:
        sid = mod["id"].zfill(2) if str(mod["id"]).isdigit() else str(mod["id"])
        title = mod["title"]
        complete, _ = step_ultraplan_complete(workspace, sid, title)
        if not complete:
            return {"id": sid, "title": title}
    if target:
        return None
    if has_map:
        return None
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
    next_p = sub.add_parser("next", help="Print next step needing ultraplan")
    next_p.add_argument("--step", default=None, help="Explicit root-owned step id or title")

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
        nxt = find_next_incomplete(workspace, target=args.step)
        if not nxt:
            if args.step:
                selected = _target_module(parse_product_map(workspace), args.step)
                if selected and not is_deferred(selected):
                    folder = module_plan_dir(workspace, selected)
                    print(f"Complete: step {selected['id']} - {selected['title']}")
                    print(f"Folder: {folder.relative_to(workspace)}")
                    return 0
                print(f"Step `{args.step}` is deferred or unknown in the product map.")
                return 1
            print("All ultraplan packs complete (or no platform steps).")
            return 0
        print(f"Next: step {nxt['id']} - {nxt['title']}")
        folder = module_plan_dir(workspace, nxt)
        print(f"Folder: {folder.relative_to(workspace)}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
