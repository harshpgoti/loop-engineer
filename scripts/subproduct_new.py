#!/usr/bin/env python3
"""Carve a product-map row out of the main product into its own workspace.

Doing this by hand is five steps, two of which quietly fail:

    mkdir "<title>"                                  <- the folder name is load-bearing
    loop setup --use-cwd --role sub --parent ..
    copy main's plan/step_NN_*.md into plan/         <- forget it and the row re-plans
    loop workspace refresh                              from nothing
    /loop-engine

`map_id` binds by exact slug match of folder name to the row's title, so a folder
named `patient-engagement` instead of `Patient Engagement And Rebooking Agent` binds
to nothing and the row stays silently unbuilt. Deriving the folder from the row
removes that failure mode entirely.

What this does not do is move the main product's tasks. Which of them belong to a
row is not reliably derivable - gates are not one-to-one with rows, and the step
grouping lives in `#` comments no parser should trust. Guessing wrong deletes real
work. They are reported instead, and the new workspace compiles its own tasks from
the plan it inherits, which is the normal path anyway.
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DELEGATED_TYPES = {"sub-product", "subproduct"}


@dataclass
class Plan:
    """What carving one row out would do. Computed before anything is written."""

    row_id: str
    title: str = ""
    folder: Path | None = None
    workspace: Path | None = None
    step_plan: Path | None = None
    dormant: bool = False
    gates: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers


def _rows(main_ws: Path) -> list[dict]:
    from ultraplan_harness import parse_product_map

    return parse_product_map(main_ws)


def main_folder(main_ws: Path) -> Path:
    from workspace_tree import product_folder

    return product_folder(main_ws) or main_ws


def step_plan_for(main_ws: Path, row_id: str) -> Path | None:
    """The main product's plan file for this row - the new workspace's starting point."""
    matches = sorted((main_ws / "plan").glob(f"step_{row_id}_*.md"))
    if matches:
        return matches[0]
    folder = main_ws / "plan" / "steps"
    if folder.is_dir():
        for child in sorted(folder.glob(f"{row_id}-*")):
            if child.is_dir():
                return child
    return None


GATE_ID = re.compile(r"\bG-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")


def declared_gates(main_ws: Path, row_id: str) -> list[str]:
    """The gate(s) this row owns, taken from what the plan states rather than inferred.

    Three signals were tried against the real main product and two of them lie:

    A `# ===== STEP 18 =====` banner has nothing that closes it, so the last one ran to
    end of file and claimed five tasks belonging to other rows. A step plan *mentions*
    every gate it depends on - step 17's names AUTHZ, DATA and SCALE, none of which it
    owns - so mentions over-attribute in the other direction.

    What is left is declaration. The map row's own Status/Scope names the gate it is
    held behind (`gated on G-M-ENGAGE-01`). When it names none, a step plan that names
    exactly one gate nobody else names is unambiguous enough to use. Otherwise: nothing,
    reported as nothing. Under-reporting an advisory list is the safe direction.
    """
    rows = _rows(main_ws)
    row = next((r for r in rows if str(r.get("id")) == row_id), None)
    if row is None:
        return []

    def gates_in(text: str) -> set[str]:
        return set(GATE_ID.findall(text or ""))

    own = gates_in(" ".join(str(row.get(k) or "") for k in ("status", "scope", "code")))
    if own:
        return sorted(own)

    step = step_plan_for(main_ws, row_id)
    if step is None or step.is_dir():
        return []
    mine = gates_in(step.read_text(encoding="utf-8", errors="ignore"))
    for other in rows:
        other_id = str(other.get("id") or "")
        if other_id == row_id:
            continue
        mine -= gates_in(" ".join(str(other.get(k) or "") for k in ("status", "scope", "code")))
        other_step = step_plan_for(main_ws, other_id)
        if other_step is not None and other_step.is_file():
            mine -= gates_in(other_step.read_text(encoding="utf-8", errors="ignore"))
    return sorted(mine) if len(mine) == 1 else []


def task_candidates(main_ws: Path, row_id: str, title: str) -> list[str]:
    """Main-product task ids carrying a gate this row declares. Reported, never moved."""
    path = main_ws / "TASKS.yml"
    gates = declared_gates(main_ws, row_id)
    if not gates or not path.is_file():
        return []
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="ignore")) or {}
    except Exception:  # noqa: BLE001 - a malformed backlog must not stop the carve
        return []
    tasks = data.get("tasks") or []
    return [str(t.get("id")) for t in tasks if isinstance(t, dict) and str(t.get("gate")) in gates]


def normalize_row(raw: str) -> str:
    """`16,` `#16` ` 16 ` and `16` all mean row 16.

    People type the list the way they say it. Rejecting `16,` with "no row 16," is a
    parser complaining about punctuation while pretending the row does not exist.
    """
    cleaned = str(raw).strip().strip(",;").lstrip("#").strip()
    if cleaned.isdigit() and len(cleaned) == 1:
        return f"0{cleaned}"
    return cleaned


def expand_rows(raw: list[str]) -> list[str]:
    """Row ids from however they were typed, including `16,17,18` as one argument."""
    out: list[str] = []
    for item in raw:
        for part in str(item).replace(";", ",").split(","):
            row = normalize_row(part)
            if row and row not in out:
                out.append(row)
    return out


def plan_row(main_ws: Path, row_id: str, *, force: bool = False) -> Plan:
    """Everything that would happen for one row, including why it cannot."""
    from plan_paths import slugify
    from workspace_tree import has_local_loop_data, local_data_dir, read_meta

    row_id = normalize_row(row_id)

    plan = Plan(row_id=row_id)
    row = next((r for r in _rows(main_ws) if str(r.get("id")) == row_id), None)
    if row is None:
        plan.blockers.append(f"`plan/PRODUCT_MAP.md` has no row {row_id}.")
        return plan

    plan.title = str(row.get("title") or "").strip()
    row_type = str(row.get("type") or "").strip().lower()
    if row_type not in DELEGATED_TYPES:
        plan.blockers.append(
            f"Row {row_id} is typed `{row_type or 'nothing'}`, not `sub-product`. "
            "A module is planned and built inside the main product - retype the row first "
            "if it should have its own workspace."
        )
        return plan
    if not plan.title:
        plan.blockers.append(f"Row {row_id} has no title, so there is no name to give the folder.")
        return plan

    bound = read_meta(main_ws).get("children") or []
    if any(str(c.get("map_id")) == row_id for c in bound if isinstance(c, dict)):
        plan.blockers.append(f"Row {row_id} already has a workspace - nothing to create.")
        return plan

    folder = main_folder(main_ws) / plan.title
    plan.folder = folder
    # Always the nested layout. `data_dir_for` answers "where is this workspace" and
    # falls back to the folder itself when `.loop-engineer/` does not exist yet - which
    # is always true here, so asking it would seed the product folder with loose
    # DOUBTS.md and TASKS.yml instead of creating the workspace.
    plan.workspace = local_data_dir(folder)
    if has_local_loop_data(folder):
        plan.blockers.append(f"`{folder}` is already a loop workspace - link it instead.")
        return plan
    if slugify(folder.name) != slugify(plan.title):
        plan.blockers.append(
            f"`{folder.name}` does not slug-match the row title, so `map_id` would not bind."
        )
        return plan

    from hierarchy_drift import row_is_dormant

    plan.dormant = row_is_dormant(row)
    if plan.dormant and not force:
        # `list` marks these `later`; without the same guard here, one typed row id
        # creates an empty workspace for work the plan has already parked.
        plan.blockers.append(
            f"Row {row_id} is `{str(row.get('status') or 'dormant').strip()}` - the plan says it has "
            "not started. Carving it out now creates an empty workspace to keep in sync. "
            "Check DECISIONS.md, then pass --force if you really mean it."
        )
        return plan

    plan.step_plan = step_plan_for(main_ws, row_id)
    plan.gates = declared_gates(main_ws, row_id)
    plan.tasks = task_candidates(main_ws, row_id, plan.title)
    return plan


# `- **Name:**` is not decoration: `loop status` reads it, and without it a workspace
# carrying a full inherited plan still reported "Product: Uninitialized". Every identity
# field the harness reads has to be written here, not left for the first session to guess.
HANDOVER_HEADER = """# {title}

- **Name:** {title}
- **Role:** sub-product of {parent}, map row {row_id}
- **Carved out:** {today} from the main product's `{source}`

> Inherited platform decisions live in `plan/PARENT_CONTEXT.md` - read that first.
> Sharpen this plan here, not in the main product.

"""


def _hand_over_plan(plan: Plan, parent_name: str) -> str:
    """Seed the new workspace's plan from the row's step plan in the main product."""
    from datetime import date

    assert plan.workspace is not None
    target = plan.workspace / "plan" / "main_plan.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    if plan.step_plan is None:
        return "no step plan in the main product - the new workspace starts from the template"

    header = HANDOVER_HEADER.format(
        title=plan.title,
        row_id=plan.row_id,
        parent=parent_name,
        today=date.today().isoformat(),
        source=plan.step_plan.name,
    )
    if plan.step_plan.is_dir():
        pack = plan.workspace / "plan" / "steps" / plan.step_plan.name
        pack.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plan.step_plan, pack, dirs_exist_ok=True)
        body = f"The full step pack was copied to `plan/steps/{plan.step_plan.name}/`.\n"
    else:
        body = plan.step_plan.read_text(encoding="utf-8", errors="ignore")
    target.write_text(header + body, encoding="utf-8")
    return f"plan seeded from `{plan.step_plan.name}`"


def _register(name: str, workspace: Path) -> None:
    """Add the new workspace to the global registry, without making it the current one.

    `setup`'s own register sets `config["current"]`, which is right when a human runs
    setup and wrong here: carving out three rows would leave the last one as the global
    default. Skipping registration entirely was worse - `loop status` then reported some
    other product's name beside this workspace's path.
    """
    from workspace_utils import load_config, save_config

    try:
        config = load_config()
        config.setdefault("workspaces", {})[name] = {
            "path": str(workspace.resolve()),
            "memory_mode": "local",
        }
        save_config(config)
    except Exception:  # noqa: BLE001 - a registry problem must not fail the carve
        pass


def create(main_ws: Path, row_id: str, *, dry_run: bool = False, force: bool = False) -> dict:
    """Create one sub-product workspace from a map row. Idempotent by refusal."""
    import setup_loop_engine as setup
    from workspace_tree import link

    plan = plan_row(main_ws, row_id, force=force)
    result: dict = {
        "row": plan.row_id,
        "title": plan.title,
        "folder": str(plan.folder) if plan.folder else "",
        "workspace": str(plan.workspace) if plan.workspace else "",
        "step_plan": plan.step_plan.name if plan.step_plan else "",
        "gates": plan.gates,
        "tasks": plan.tasks,
        "blockers": plan.blockers,
        "steps": [],
        "created": False,
    }
    if not plan.ok or plan.workspace is None or plan.folder is None:
        return result
    if dry_run:
        result["steps"].append("would create the workspace, seed it, link it, and hand over the plan")
        return result

    from memory_paths import ensure_memory_layout, state_db
    from session_store import init_db

    plan.workspace.mkdir(parents=True, exist_ok=True)
    # `memories/` and `state.db` come first: a folder is only a loop workspace once it
    # carries a marker file, and `link` refuses one that does not. Seeding the starter
    # files alone left a directory full of plan documents that nothing recognised.
    ensure_memory_layout(plan.workspace)
    init_db(state_db(plan.workspace))

    seeded = 0
    for relative in setup.STARTER_FILES:
        if setup.copy_missing_file(relative, plan.workspace) == "created":
            seeded += 1
    result["steps"].append(f"seeded {seeded} starter file(s), memory layout and state.db")
    result["steps"].append(_hand_over_plan(plan, main_folder(main_ws).name))

    _register(plan.title, plan.workspace)
    link(main_ws, plan.folder, name=plan.title, map_id=plan.row_id)
    result["steps"].append(f"linked to the main product as map row {plan.row_id}")

    # `refresh` resolves the tree but writes no reports, and the seeded plan points at
    # `plan/PARENT_CONTEXT.md` - a dangling pointer is worse than no pointer.
    import hierarchy_sync

    hierarchy_sync.run(plan.workspace)
    hierarchy_sync.run(main_ws, stage=False)
    result["steps"].append("wrote plan/PARENT_CONTEXT.md and refreshed the main roll-up")
    result["created"] = True
    return result


def describe(result: dict) -> str:
    lines: list[str] = []
    label = f"row {result['row']}" + (f" - {result['title']}" if result["title"] else "")
    if result["blockers"]:
        lines.append(f"{label}: not created")
        for blocker in result["blockers"]:
            lines.append(f"  ! {blocker}")
        return "\n".join(lines)

    lines.append(f"{label}: {result['folder']}")
    for step in result["steps"]:
        lines.append(f"  - {step}")
    if result["tasks"]:
        lines.append("")
        gates = ", ".join(result.get("gates") or []) or "-"
        lines.append(
            f"  {len(result['tasks'])} main-product task(s) carry the gate this row declares ({gates}):"
        )
        lines.append("    " + ", ".join(result["tasks"]))
        lines.append("    They were NOT moved. The new workspace compiles its own tasks from the")
        lines.append("    plan it inherited; remove or retarget these in the main product when")
        lines.append("    that is done, so the same work is not tracked twice.")
    if result["created"]:
        lines.append("")
        lines.append(f'  Next:  cd "{result["folder"]}"  then  /loop-engine')
    return "\n".join(lines)


def carveable(main_ws: Path) -> list[dict]:
    """Rows that could be carved out, and whether anything stops each one."""
    out = []
    for row in _rows(main_ws):
        row_id = str(row.get("id") or "")
        if not row_id or str(row.get("type") or "").lower() not in DELEGATED_TYPES:
            continue
        from hierarchy_drift import row_is_dormant

        plan = plan_row(main_ws, row_id)
        out.append(
            {
                "row": row_id,
                "title": plan.title or str(row.get("title") or ""),
                "status": str(row.get("status") or "").strip(),
                # Carving out a row the plan says has not started is how a founder ends
                # up with twelve empty workspaces to keep in sync. Possible, not advised.
                "dormant": row_is_dormant(row),
                "ready": plan.ok,
                "why": plan.blockers[0] if plan.blockers else "",
                "step_plan": plan.step_plan.name if plan.step_plan else "",
            }
        )
    return out



def _is_unified(main_ws) -> bool:
    try:
        import scope_paths

        return scope_paths.workspace_mode(main_ws) == "unified"
    except Exception:  # noqa: BLE001 - never let this stop a federated carve
        return False


def _slug(title: str) -> str:
    from plan_paths import slugify

    return slugify(title)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(
        description="Carve product-map rows out of the main product into their own workspaces."
    )
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")

    new_p = sub.add_parser("new", help="Create a workspace for each map row given.")
    new_p.add_argument("rows", nargs="+", help="Map row ids, e.g. 17 18")
    new_p.add_argument("--dry-run", action="store_true")
    new_p.add_argument("--force", action="store_true", help="Carve out a row the plan says is dormant.")

    sub.add_parser("list", help="Rows typed `sub-product`, and which are ready to carve out.")

    args = parser.parse_args()
    main_ws = resolve_workspace(args.workspace)

    if (args.cmd or "list") == "new" and _is_unified(main_ws):
        # A unified workspace plans sub-products as scopes. Carving a *workspace* out of
        # one would re-create the boundary it was absorbed to remove, and the two copies
        # would then have to be kept in sync by the machinery this layout retires.
        print(
            "This workspace plans sub-products as scopes (`plan/products/`).\n"
            "Create one there instead - it needs no separate workspace:\n"
        )
        for row_id in args.rows:
            row_id = normalize_row(row_id)
            title = next(
                (str(r.get("title") or "") for r in _rows(main_ws) if str(r.get("id")) == row_id), ""
            )
            slug = _slug(title) if title else f"row-{row_id}"
            print(f'  loop scope new {slug} --name "{title or row_id}" --map-id {row_id}')
        print("\nTo split a scope back out into its own workspace: `loop scope eject <slug>`.")
        return 1

    if (args.cmd or "list") == "list":
        rows = carveable(main_ws)
        if not rows:
            print("No row in `plan/PRODUCT_MAP.md` is typed `sub-product`.")
            return 0
        print(f"{len(rows)} row(s) typed `sub-product`:")
        for row in rows:
            if not row["ready"]:
                mark = "      "
            elif row["dormant"]:
                mark = "later "
            else:
                mark = "READY "
            print(f"  {mark} {row['row']}  {row['title']}")
            print(f"           status: {row['status'] or '-'}")
            if row["step_plan"]:
                print(f"           plan:   {row['step_plan']}")
            if not row["ready"]:
                print(f"           ! {row['why']}")
        print()
        print("READY - active, and nothing stops it. `loop subproduct new <row>`.")
        print("later - the plan says this one has not started; carving it out now just")
        print("        creates an empty workspace to keep in sync.")
        return 0

    failures = 0
    for row_id in expand_rows(args.rows):
        result = create(main_ws, row_id, dry_run=args.dry_run, force=args.force)
        print(describe(result))
        print()
        if result["blockers"]:
            failures += 1
    if args.dry_run:
        print("Dry run only - re-run without --dry-run to apply.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
