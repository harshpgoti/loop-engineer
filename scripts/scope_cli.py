#!/usr/bin/env python3
"""`loop scope ...` - the runtime every scope-aware command calls.

The decided invocation model is that the user runs everything from the main product
folder and names the sub-product in the command text (`/plan-loop start working on auth
product`). That makes scope resolution a step *inside* each command rather than a flag,
and this is the one implementation of it: skills call `loop scope resolve`, they never
re-parse the text themselves. One parser, one set of rules, one place a mis-binding
could ever come from.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import contracts as ct
import scope_paths as sp
import scope_state as st
from workspace_utils import console_utf8, resolve_workspace


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------


def cmd_list(workspace: Path, args: argparse.Namespace) -> int:
    scopes = sp.list_scopes(workspace)
    if not scopes:
        print("No sub-product scopes. `loop scope new <slug>` creates one.")
        return 0

    ordered, cycles = sp.dependency_order(workspace)
    active = (sp.read_active(workspace) or {}).get("slug")
    rows = {s.slug: s for s in st.summarize(workspace)}

    print("Sub-products, in dependency order (what others depend on first):\n")
    for scope in ordered or scopes:
        mark = "*" if scope.slug == active else " "
        summary = rows.get(scope.slug)
        print(f"{mark} {summary.line() if summary else scope.slug}")
    if cycles:
        print("\nDependency cycles - these must be resolved in the plan:")
        for cycle in cycles:
            print("  " + " -> ".join(cycle))
    return 0


def cmd_show(workspace: Path, args: argparse.Namespace) -> int:
    scope = sp.find_scope(workspace, args.slug)
    if scope is None:
        print(f"No scope named `{args.slug}`.")
        return 1
    tasks = [t for t in st.load_tasks(workspace, scope=scope.slug) if t.get("scope") == scope.slug]
    ready = {t["id"] for t in st.ready_tasks(st.load_tasks(workspace))}
    print(f"# {scope.title}  (`{scope.slug}`)\n")
    print(f"- Plan: `plan/products/{scope.slug}/`")
    print(f"- Code: `{scope.code_dir or '(not decided)'}` ({scope.code_layout})")
    print(f"- Map row: {scope.map_id or '(unbound)'}")
    print(f"- Status: {scope.status}")
    if scope.provides:
        print(f"- Provides: {', '.join(scope.provides)}")
    if scope.consumes:
        print(f"- Consumes: {', '.join(scope.consumes)}")
    print(f"- Tasks: {len(tasks)} ({len([t for t in tasks if t['id'] in ready])} ready)")
    if scope.absorbed_from:
        print(f"- Absorbed from: `{scope.absorbed_from}`")
    return 0


def cmd_match(workspace: Path, args: argparse.Namespace) -> int:
    match = sp.match_text(workspace, args.text)
    if match.ok:
        print(match.scope.slug)
        return 0
    if match.candidates:
        print("ambiguous: " + ", ".join(s.slug for s in match.candidates))
        return 2
    print("none")
    return 1


def cmd_resolve(workspace: Path, args: argparse.Namespace) -> int:
    """The full resolution a command runs, as JSON an agent can act on.

    Exit code is the instruction: 0 = go, 2 = ask the user first. A command must not
    proceed on 2 - that is the guard that keeps a forgotten word from becoming edits to
    shared CI, schema, or design-system code.
    """
    res = sp.resolve(
        workspace,
        explicit=args.scope,
        text=args.text,
        session=args.session,
        cwd=Path.cwd(),
    )
    payload = {
        "scope": res.slug if res.scope else None,
        "source": res.source,
        "needs_confirm": res.needs_confirm,
        "reason": res.reason,
        "candidates": [
            {
                "slug": s.slug,
                "name": s.title,
                "code_dir": s.code_dir,
                "status": s.status,
            }
            for s in res.candidates
        ],
    }
    if res.scope is not None:
        payload["plan_dir"] = f"plan/products/{res.scope.slug}"
        payload["code_dir"] = res.scope.code_dir
        payload["banner"] = (
            f"Scope: {res.scope.slug}"
            f" (plan/products/{res.scope.slug}"
            + (f", code {res.scope.code_dir}" if res.scope.code_dir else "")
            + ")"
        )
        if not res.needs_confirm and args.remember:
            sp.set_active(workspace, res.scope.slug, session=args.session)
    else:
        payload["banner"] = "Scope: not selected - ask which sub-product"
        payload["platform_option"] = "shared platform work (root TASKS.yml)"

    print(json.dumps(payload, indent=2))
    return 0 if (res.scope is not None and not res.needs_confirm) else 2


# ---------------------------------------------------------------------------
# writing
# ---------------------------------------------------------------------------


def cmd_use(workspace: Path, args: argparse.Namespace) -> int:
    scope = sp.find_scope(workspace, args.slug)
    if scope is None:
        print(f"No scope named `{args.slug}`.")
        return 1
    sp.set_active(workspace, scope.slug, session=args.session)
    print(f"Scope: {scope.slug} (plan/products/{scope.slug})")
    return 0


def cmd_clear(workspace: Path, args: argparse.Namespace) -> int:
    sp.clear_active(workspace)
    print("No scope remembered - the next command will ask.")
    return 0


def cmd_new(workspace: Path, args: argparse.Namespace) -> int:
    slug = sp.slugify(args.slug)
    if sp.find_scope(workspace, slug) is not None:
        print(f"Scope `{slug}` already exists.")
        return 1
    if args.code_layout not in sp.CODE_LAYOUTS:
        print(f"code-layout must be one of: {', '.join(sp.CODE_LAYOUTS)}")
        return 1
    scope = sp.create_scope(
        workspace,
        slug,
        name=args.name or slug,
        map_id=args.map_id,
        code_dir=args.code_dir,
        code_layout=args.code_layout,
        type=args.type,
    )
    print(f"Created plan/products/{scope.slug}/")
    if scope.code_dir:
        folder = scope.code_path(workspace)
        if folder is not None:
            folder.mkdir(parents=True, exist_ok=True)
            sp.write_pointer(folder, scope.slug)
            print(f"Code dir: {scope.code_dir} (pointer written)")
    else:
        print("No code dir yet - `/plan-loop` asks how this scope's code is laid out.")
    return 0


def cmd_rename(workspace: Path, args: argparse.Namespace) -> int:
    """Rename a scope folder and every reference to it, together.

    The folder name is not the binding key, so a rename is safe - but the pointer
    files, the active-scope record and the map row still name the old slug, and
    leaving any of them behind is how a scope half-disappears.
    """
    scope = sp.find_scope(workspace, args.old)
    if scope is None:
        print(f"No scope named `{args.old}`.")
        return 1
    new_slug = sp.slugify(args.new)
    if sp.find_scope(workspace, new_slug) is not None:
        print(f"Scope `{new_slug}` already exists.")
        return 1

    target = sp.scope_dir(workspace, new_slug)
    scope.path.rename(target)
    scope.path = target
    scope.slug = new_slug
    sp.write_scope(workspace, scope)

    folder = scope.code_path(workspace)
    if folder is not None and (folder / sp.POINTER_FILE).exists():
        sp.write_pointer(folder, new_slug)
    record = sp.read_active(workspace)
    if record and record.get("slug") == args.old:
        sp.set_active(workspace, new_slug, session=record.get("set_by_session"))
    print(f"Renamed `{args.old}` -> `{new_slug}`.")
    return 0


# ---------------------------------------------------------------------------
# checking
# ---------------------------------------------------------------------------


def cmd_check(workspace: Path, args: argparse.Namespace) -> int:
    """Every deterministic cross-scope check, in one place."""
    tasks = st.load_tasks(workspace)
    findings = ct.check(workspace, tasks=tasks)
    dangling = st.unresolved_blockers(tasks)
    clashes = st.duplicate_gate_ids(st.load_gates(workspace))
    _ordered, cycles = sp.dependency_order(workspace)

    errors = [f for f in findings if f.level == "error"]

    if not (findings or dangling or clashes or cycles):
        print("No cross-scope findings.")
        return 0

    for finding in findings:
        print(finding.line())
        if finding.fix:
            print(f"    fix: {finding.fix}")
    for item in dangling:
        print(f"[error] dangling-reference ({item.scope}): {item}")
    for clash in clashes:
        print(f"[error] duplicate-gate: {clash}")
    for cycle in cycles:
        print("[error] dependency-cycle: " + " -> ".join(cycle))

    return 1 if (errors or dangling or clashes or cycles) else 0


def cmd_impact(workspace: Path, args: argparse.Namespace) -> int:
    """Who a change to this contract affects - the payload for the section 5.1 question."""
    print(json.dumps(ct.impact_of(workspace, args.contract), indent=2))
    return 0


def cmd_lock(workspace: Path, args: argparse.Namespace) -> int:
    locks = ct.lock_surfaces(workspace)
    print(f"Locked {len(locks)} agreed/implemented contract surface(s).")
    return 0


# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Product scopes in a unified workspace.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="Scopes in dependency order, with task counts.")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="One scope in detail.")
    p.add_argument("slug")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("match", help="Which scope a command's text names.")
    p.add_argument("text")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("resolve", help="Full scope resolution for one command, as JSON.")
    p.add_argument("--text", default=None, help="The command text the user typed.")
    p.add_argument("--scope", default=None, help="Explicit scope, overrides the text.")
    p.add_argument("--session", default=None, help="Current session id, for staleness.")
    p.add_argument("--remember", action="store_true", help="Store the result as the active scope.")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("use", help="Remember a scope for subsequent commands.")
    p.add_argument("slug")
    p.add_argument("--session", default=None)
    p.set_defaults(func=cmd_use)

    p = sub.add_parser("clear", help="Forget the remembered scope.")
    p.set_defaults(func=cmd_clear)

    p = sub.add_parser("new", help="Create a scope folder.")
    p.add_argument("slug")
    p.add_argument("--name", default=None)
    p.add_argument("--map-id", default=None)
    p.add_argument("--code-dir", default=None)
    p.add_argument("--code-layout", default="own-dir", choices=list(sp.CODE_LAYOUTS))
    p.add_argument("--type", default="sub-product")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("rename", help="Rename a scope and every reference to it.")
    p.add_argument("old")
    p.add_argument("new")
    p.set_defaults(func=cmd_rename)

    p = sub.add_parser("check", help="Contract, dependency and gate findings across scopes.")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("impact", help="Who is affected by a change to one contract.")
    p.add_argument("contract")
    p.set_defaults(func=cmd_impact)

    p = sub.add_parser("lock", help="Record agreed contract surfaces so a later edit is visible.")
    p.set_defaults(func=cmd_lock)

    return parser


def main() -> int:
    console_utf8()
    args = build_parser().parse_args()
    workspace = resolve_workspace(args.workspace)
    return args.func(workspace, args)


if __name__ == "__main__":
    raise SystemExit(main())
