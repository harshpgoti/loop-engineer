"""One layout for every sub-product, checked rather than assumed.

`docs/SCOPES.md` decides where planning state lives: `TASKS.yml`, `GATES.yml` and
`DOUBTS.md` exist at the root **and** in each `plan/products/<slug>/`, unioned by
`scope_state`. Root holds platform work; a scope holds its own.

Nothing enforced that. A workspace can drift into holding one sub-product's rows in
its own file and another's in the root file, with a prose comment as the only record
of which - and every consequence of that drift is silent:

- a scope whose rows live at the root reports `0/0 done`, so `/status`, `/scope list`
  and the readiness counters describe a sub-product that is not the one on disk;
- `blocked_by` across those rows looks intra-scope, so `cross_scope_blocks` reports
  nothing to sequence;
- the root file written in a different YAML shape than the scopes parses to zero
  gates, so platform gates stop being enforced without an error anywhere.

So the layout is a checked invariant with named findings, in the same shape the
contract checks use, surfaced by `loop scope check`. Every finding here is decided
from declarations on disk - a slug, a `scope:` field, a file's YAML shape - never
from guessing which sub-product a row is "really" about.
"""

from __future__ import annotations

import re
from pathlib import Path

import scope_paths as sp
from contracts import Finding
from task_context import gate_forms, parse_tasks_file
from scope_state import parse_gates_file


#: `plan/steps/19-identity-and-access-platform/` is an ultraplan *pack* - overview, prd,
#: architecture, data-model - and a scope folder is that same pack, so holding one at the
#: root splits a sub-product's plan across two places.
#:
#: `plan/step_NN_<slug>.md` is deliberately NOT drift: the master plan keeps one row
#: summary per sub-product at the root (`AGENTS.md`: `plan/step_01_<module>.md`), and the
#: PRODUCT_MAP's `Step file` column points at it. Only the pack is checked here.
ROOT_STEP_DIR = re.compile(r"^(?P<num>\d+)-(?P<slug>.+)$")


def _declared_scopes(path: Path) -> dict[str, list[str]]:
    """`scope -> [row ids]` for rows in one file that name a scope."""
    out: dict[str, list[str]] = {}
    for task in parse_tasks_file(path):
        declared = str(task.get("scope") or "").strip()
        if declared:
            out.setdefault(declared, []).append(str(task.get("id")))
    return out


def _root_step_slugs(workspace: Path) -> dict[str, str]:
    """`slug -> the root path that holds that slug's ultraplan pack`."""
    out: dict[str, str] = {}
    plan = Path(workspace) / "plan"
    steps = plan / "steps"
    if steps.is_dir():
        for path in sorted(steps.iterdir()):
            if not path.is_dir():
                continue
            match = ROOT_STEP_DIR.match(path.name)
            if match:
                out.setdefault(sp.slugify(match.group("slug")), f"plan/steps/{path.name}")
    return out


def findings(workspace: Path) -> list[Finding]:
    """Every layout finding, most structural first."""
    workspace = Path(workspace)
    scopes = sp.list_scopes(workspace)
    if not scopes:
        return []
    known = {record.slug for record in scopes}

    out: list[Finding] = []
    root_tasks = _declared_scopes(workspace / "TASKS.yml")
    root_steps = _root_step_slugs(workspace)

    # 1. A root row that names a scope belongs in that scope's file.
    for slug, ids in sorted(root_tasks.items()):
        shown = ", ".join(ids[:6]) + (", ..." if len(ids) > 6 else "")
        if slug not in known:
            out.append(
                Finding(
                    kind="scope-unknown",
                    level="error",
                    scope=slug,
                    message=f"{len(ids)} root task(s) declare `scope: {slug}`, which is not a scope here ({shown})",
                    fix=f"create the scope (`loop scope new {slug}`) or correct the `scope:` field",
                )
            )
            continue
        out.append(
            Finding(
                kind="scope-rows-in-root",
                level="error",
                scope=slug,
                message=f"{len(ids)} task(s) for `{slug}` live in the root TASKS.yml ({shown})",
                fix=f"move them to plan/products/{slug}/TASKS.yml so every scope is read the same way",
            )
        )

    # 2. A scope file that declares nothing, while the root file carries rows for it.
    #    On its own an empty file is a scope that has not been planned yet; together
    #    with root rows it is the split this module exists to name.
    for record in scopes:
        has_rows = bool(parse_tasks_file(record.tasks_file))
        if record.tasks_file.is_file() and not has_rows and record.slug in root_tasks:
            out.append(
                Finding(
                    kind="scope-file-stub",
                    level="error",
                    scope=record.slug,
                    message=f"plan/products/{record.slug}/TASKS.yml declares no tasks while the root file holds rows for it",
                    fix="hold the scope's rows in the scope's own file; keep only platform work at the root",
                )
            )
        for name, path in (("TASKS.yml", record.tasks_file), ("GATES.yml", record.gates_file)):
            if not path.is_file():
                out.append(
                    Finding(
                        kind="scope-file-missing",
                        level="warn",
                        scope=record.slug,
                        message=f"plan/products/{record.slug}/{name} does not exist",
                        fix=f"create it, even empty (`{'tasks' if name.startswith('TASKS') else 'gates'}: []`), so every scope reads alike",
                    )
                )

    # 2b. A scope with no rows anywhere. Its work is real but unattributed - typically
    #     held in root rows that name no scope, where nothing can associate them back.
    #     Reported, not guessed at: no fuzzy title matching decides ownership here.
    for record in scopes:
        if parse_tasks_file(record.tasks_file) or record.slug in root_tasks:
            continue
        out.append(
            Finding(
                kind="scope-unplanned",
                level="warn",
                scope=record.slug,
                message="no task declares this scope, in its own file or by `scope:` at the root",
                fix=f"give its rows a home: plan/products/{record.slug}/TASKS.yml, or `scope: {record.slug}` on the root rows that are its work",
            )
        )

    # 3. One YAML shape for gates across the workspace. Two shapes parse, but a reader
    #    that knows only one silently returns nothing - which is how a root file in the
    #    minority shape stopped contributing any gate at all.
    forms: dict[str, set[str]] = {}
    root_forms = gate_forms(workspace / "GATES.yml")
    if root_forms:
        forms[sp.PLATFORM] = root_forms
    for record in scopes:
        found = gate_forms(record.gates_file)
        if found:
            forms[record.slug] = found
    all_forms = set().union(*forms.values()) if forms else set()
    if len(all_forms) > 1:
        detail = "; ".join(f"{slug}: {'+'.join(sorted(shape))}" for slug, shape in sorted(forms.items()))
        out.append(
            Finding(
                kind="gate-form-split",
                level="warn",
                scope=sp.PLATFORM,
                message=f"GATES.yml files use more than one declaration shape ({detail})",
                fix="settle on the starter's mapping form (`  G-ID-01:` with fields beneath it)",
            )
        )

    # 4. A task naming a gate that exists nowhere. A scope task gated by a *platform*
    #    gate is the documented normal case - platform work gates scope work - so the
    #    defect is the dangling id, not the file it lives in.
    declared_gates = {str(g.get("id")) for g in parse_gates_file(workspace / "GATES.yml")}
    for record in scopes:
        declared_gates |= {str(g.get("id")) for g in parse_gates_file(record.gates_file)}
    for record in scopes:
        missing = sorted(
            {str(t.get("gate")) for t in parse_tasks_file(record.tasks_file) if t.get("gate")}
            - declared_gates
        )
        if missing:
            out.append(
                Finding(
                    kind="gate-undeclared",
                    level="error",
                    scope=record.slug,
                    message=f"task(s) name gate(s) no file declares: {', '.join(missing)}",
                    fix=f"declare them in plan/products/{record.slug}/GATES.yml, or correct the `gate:` field",
                )
            )

    # 5. A scope's step plan living at the root.
    for record in scopes:
        where = root_steps.get(record.slug)
        if not where:
            continue
        out.append(
            Finding(
                kind="scope-steps-in-root",
                level="warn",
                scope=record.slug,
                message=f"`{where}` is this scope's ultraplan pack but sits at the root",
                fix=f"move its files under plan/products/{record.slug}/ so the scope folder is the whole pack",
            )
        )

    order = {"error": 0, "warn": 1, "info": 2}
    return sorted(out, key=lambda f: (order.get(f.level, 3), f.kind, f.scope))
