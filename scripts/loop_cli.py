#!/usr/bin/env python3
"""Unified loop CLI for Loop Engineering OS."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(script: str, args: list[str]) -> int:
    """Run a loop script, with a console that can print what a product actually says.

    Windows consoles default to cp1252, so any product text containing a character
    outside it - a `>=`, an em dash, an accented name - raised UnicodeEncodeError and
    took the whole command down mid-output. `loop findings ask` died on a single
    U+2265 in a real workspace. This is the one chokepoint every script goes through.
    """
    import os

    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8:replace")
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    result = subprocess.run(cmd, check=False, env=env)
    return int(result.returncode)


def cmd_setup(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if getattr(args, "name", None):
        extra.extend(["--name", args.name])
    if getattr(args, "memory_mode", None):
        extra.extend(["--memory-mode", args.memory_mode])
    if getattr(args, "role", None):
        extra.extend(["--role", args.role])
    if getattr(args, "parent", None):
        extra.extend(["--parent", args.parent])
    if getattr(args, "interactive", False):
        extra.append("--interactive")
    if getattr(args, "use_cwd", False):
        extra.append("--use-cwd")
    if getattr(args, "source", None):
        extra.extend(["--source", args.source])
    if getattr(args, "dry_run", False):
        extra.append("--dry-run")
    if getattr(args, "overwrite", False):
        extra.append("--overwrite")
    if getattr(args, "scan", False):
        extra.append("--scan")
    if getattr(args, "skip_native_commands", False):
        extra.append("--skip-native-commands")
    return run_script("setup_loop_engine.py", extra)


def cmd_update(args: argparse.Namespace) -> int:
    extra: list[str] = []
    if getattr(args, "skip_validate", False):
        extra.append("--skip-validate")
    if getattr(args, "skip_native_commands", False):
        extra.append("--skip-native-commands")
    return run_script("loop_update.py", extra)


def cmd_doctor(args: argparse.Namespace) -> int:
    return run_script("doctor.py", _workspace_args(args))


def cmd_status(args: argparse.Namespace) -> int:
    return run_script("status.py", _workspace_args(args))


def cmd_sync(args: argparse.Namespace) -> int:
    return run_script("sync_loop_state.py", _workspace_args(args))


def cmd_release_check(args: argparse.Namespace) -> int:
    return run_script("release_check.py", _workspace_args(args))


def cmd_deployment_plan(args: argparse.Namespace) -> int:
    extra = []
    if getattr(args, "source", None):
        extra.extend(["--source", args.source])
    return run_script("deployment_plan.py", _workspace_args(args) + extra)


def cmd_compact(args: argparse.Namespace) -> int:
    return run_script("compact_context.py", _workspace_args(args))


def cmd_prod_gap(args: argparse.Namespace) -> int:
    return run_script("prod_gap.py", _workspace_args(args))


def cmd_team_init(args: argparse.Namespace) -> int:
    extra: list[str] = [args.mode]
    if getattr(args, "workspace", None):
        extra.extend(["--workspace", args.workspace])
    if getattr(args, "commit", False):
        extra.append("--commit")
    if getattr(args, "dry_run", False):
        extra.append("--dry-run")
    return run_script("team_init.py", extra)


def cmd_home(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from loop_home import describe_layout, ensure_loop_home, loop_home

    ensure_loop_home()
    print(describe_layout())
    print(f"Resolved home: {loop_home()}")
    return 0


def cmd_session(args: argparse.Namespace) -> int:
    extra: list[str] = _workspace_args(args)
    if args.query:
        extra.extend(["--query", args.query])
    if args.recent:
        extra.extend(["--recent", str(args.recent)])
    return run_script("session_search.py", extra)


def cmd_recall(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if args.query:
        extra.extend(["--query", args.query])
    if args.limit:
        extra.extend(["--limit", str(args.limit)])
    return run_script("session_recall.py", extra)


def cmd_memory(args: argparse.Namespace) -> int:
    if args.memory_cmd == "review":
        extra = _workspace_args(args)
        if args.apply:
            extra.append("--apply")
        if args.stage:
            extra.append("--stage")
        return run_script("memory_curator.py", extra)
    print(f"unknown memory subcommand: {args.memory_cmd}", file=sys.stderr)
    return 2


def cmd_migrate(args: argparse.Namespace) -> int:
    if args.target == "workspace":
        extra = _workspace_args(args)
        if args.dry_run:
            extra.append("--dry-run")
        if args.list:
            extra.append("--list")
        return run_script("migrate_workspace.py", extra)
    if args.target == "import":
        extra = _workspace_args(args)
        if args.dry_run:
            extra.append("--dry-run")
        if args.source:
            extra.extend(["--source", args.source])
        if not args.source:
            print("--source is required for migrate import", file=sys.stderr)
            return 2
        if getattr(args, "scan", False):
            extra.append("--scan")
        return run_script("migrate_import.py", extra)
    if args.target == "legacy-layout":
        extra = _workspace_args(args)
        if args.apply:
            extra.append("--apply")
        return run_script("migrate_legacy_layout.py", extra)
    print(f"unknown migrate target: {args.target}", file=sys.stderr)
    return 2


def cmd_pending(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from pending_writes import approve_pending, dedupe_pending, list_pending, reject_pending
    from workspace_utils import resolve_workspace

    workspace = resolve_workspace(args.workspace)
    if args.pending_cmd == "list":
        items = list_pending(workspace)
        if not items:
            print("No pending writes.")
            return 0
        for item in items:
            print(f"{item['kind']} {item['id']} -> {item.get('target') or item.get('relative_path')}")
            print(f"  reason: {item.get('reason', '')}")
        return 0
    if args.pending_cmd == "dedupe":
        results = dedupe_pending(workspace, dry_run=args.dry_run)
        for line in results:
            print(line)
        print(f"{len(results)} duplicate(s); {len(list_pending(workspace))} write(s) remain.")
        return 0
    if args.pending_cmd == "approve":
        results = approve_pending(workspace, write_id=args.id, approve_all=args.all, kind=args.kind)
        for line in results:
            print(line)
        return 0 if results else 1
    if args.pending_cmd == "reject":
        results = reject_pending(workspace, write_id=args.id, reject_all=args.all, kind=args.kind)
        for line in results:
            print(line)
        return 0 if results else 1
    return 2


def cmd_skills(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from skill_resolver import list_skills, resolve_skill
    from workspace_utils import resolve_workspace

    if args.skills_cmd in ("install", "uninstall", "installed"):
        extra: list[str] = _workspace_args(args)
        if getattr(args, "user", False):
            extra.append("--user")
        if getattr(args, "project", False):
            extra.append("--project")
        for host in getattr(args, "hosts", None) or []:
            extra.extend(["--host", host])
        if getattr(args, "detected_only", False):
            extra.append("--detected-only")
        if getattr(args, "dry_run", False):
            extra.append("--dry-run")
        if args.skills_cmd == "uninstall":
            extra.append("--uninstall")
        elif args.skills_cmd == "installed":
            extra.append("--list")
        return run_script("install_skills.py", extra)

    workspace = resolve_workspace(args.workspace)
    if args.skills_cmd == "list":
        for item in list_skills(workspace):
            print(f"{item['name']}\t{item['source']}\t{item['path']}")
        return 0
    if args.skills_cmd == "resolve":
        if not args.name:
            print("skill name required")
            return 2
        path = resolve_skill(args.name, workspace)
        if path is None:
            print(f"Skill not found: {args.name}")
            return 1
        print(path)
        return 0
    return 2


def cmd_auto_skills(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from frontend_skill_router import run_router
    from workspace_utils import resolve_workspace

    workspace = resolve_workspace(args.workspace)
    picks = run_router(workspace, extra=getattr(args, "text", "") or "", write=args.write)
    if not picks:
        print("No frontend motion/3D signals detected.")
        return 0
    for name, reason in picks:
        print(f"{name}: {reason}")
    if args.write:
        print(f"Wrote {workspace / 'plan' / 'AUTO_SKILLS.md'}")
    return 0


def cmd_auto_agent_skills(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from agent_skill_router import run_router
    from workspace_utils import resolve_workspace

    workspace = resolve_workspace(args.workspace)
    picks = run_router(workspace, extra=getattr(args, "text", "") or "", write=args.write)
    if not picks:
        print("No AI-agent-development signals detected.")
        return 0
    for name, reason in picks:
        print(f"{name}: {reason}")
    if args.write:
        print(f"Wrote {workspace / 'plan' / 'AUTO_AGENT_SKILLS.md'}")
    return 0


def cmd_session_lifecycle(args: argparse.Namespace) -> int:
    extra: list[str] = [args.phase]
    extra.extend(_workspace_args(args))
    if getattr(args, "command", None):
        extra.extend(["--command", args.command])
    if getattr(args, "tool", None):
        extra.extend(["--tool", args.tool])
    if getattr(args, "text", None):
        extra.extend(["--text", args.text])
    if getattr(args, "skip_recall", False):
        extra.append("--skip-recall")
    if getattr(args, "apply", False):
        extra.append("--apply")
    if getattr(args, "summary", None):
        extra.extend(["--summary", args.summary])
    return run_script("session_lifecycle.py", extra)


def cmd_eval(args: argparse.Namespace) -> int:
    cmd = getattr(args, 'eval_cmd', None) or 'status'
    extra = _workspace_args(args)
    if getattr(args, 'threshold', None) is not None:
        extra.extend(['--threshold', str(args.threshold)])
    if cmd == 'record':
        tail = ['record', args.results]
        if args.model:
            tail.extend(['--model', args.model])
        if args.notes:
            tail.extend(['--notes', args.notes])
    else:
        tail = [cmd]
    return run_script('eval_suite.py', extra + tail)


def cmd_subproduct(args: argparse.Namespace) -> int:
    cmd = getattr(args, "subproduct_cmd", None) or "list"
    tail = [cmd]
    if cmd == "new":
        tail += list(args.rows)
        if args.dry_run:
            tail.append("--dry-run")
    return run_script("subproduct_new.py", _workspace_args(args) + tail)


def cmd_fog(args: argparse.Namespace) -> int:
    cmd = getattr(args, "fog_cmd", None) or "list"
    tail = [cmd]
    if cmd == "promote":
        tail.append(str(args.index))
        if args.non_blocking:
            tail.append("--non-blocking")
    return run_script("fog.py", _workspace_args(args) + tail)


def cmd_glossary(args: argparse.Namespace) -> int:
    cmd = getattr(args, "glossary_cmd", None) or "list"
    return run_script("glossary.py", _workspace_args(args) + [cmd])


def cmd_evidence(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if getattr(args, 'verbose', False):
        extra.append('--verbose')
    if getattr(args, 'today', None):
        extra.extend(['--today', args.today])
    return run_script('evidence_review.py', extra)


def cmd_fresh(args: argparse.Namespace) -> int:
    return run_script("freshness.py", _workspace_args(args) + (["--all"] if args.all else []))


def cmd_graph(args: argparse.Namespace) -> int:
    cmd = getattr(args, "graph_cmd", None) or "stats"
    workspace = _workspace_args(args)
    if cmd == "check":
        return run_script("graph_schema.py", workspace + (["--verbose"] if getattr(args, "verbose", False) else []))
    if cmd == "show":
        tail = ["show", args.node_id, "--depth", str(args.depth)]
    elif cmd == "as-of":
        tail = ["as-of", args.date]
    else:
        tail = [cmd]
    # `--workspace` is a top-level option in graph_index, so it has to precede the
    # subcommand. Appending it put the flag where argparse could not see it and every
    # `loop graph <cmd> --workspace ...` failed.
    return run_script("graph_index.py", workspace + tail)


def cmd_archive(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if args.search:
        extra = ["--search", args.search] + extra
    elif args.dry_run:
        extra = ["--dry-run"] + extra
    return run_script("state_archive.py", extra)


def cmd_findings(args: argparse.Namespace) -> int:
    cmd = getattr(args, "findings_cmd", None) or "list"
    extra = _workspace_args(args)
    if cmd == "resolve":
        extra = ["resolve", args.finding_id, args.decision] + (["--note", args.note] if args.note else []) + extra
    elif cmd == "ask":
        extra = ["ask"] + extra
    else:
        extra = ["list"] + (["--verbose"] if getattr(args, "verbose", False) else []) + extra
    return run_script("parent_inbox.py", extra)


def cmd_doubts(args: argparse.Namespace) -> int:
    cmd = getattr(args, "doubts_cmd", None) or "list"
    # `--workspace` is a top-level option on doubts.py, so it has to precede the
    # subcommand. Appending it produced "unrecognized arguments: --workspace" for every
    # doubts call that named a workspace - the same ordering bug `loop graph` had.
    tail: list[str] = [cmd]
    if cmd == "resolve":
        tail += [args.doubt_id, args.answer] + (["--decision", args.decision] if args.decision else [])
    elif cmd == "defer":
        tail += [args.doubt_id, args.reason]
    elif cmd == "list":
        tail += ["--verbose"] if getattr(args, "verbose", False) else []
    elif cmd == "add":
        tail += [args.title, args.question]
        for flag, value in (
            ("--why", args.why),
            ("--default", args.default_answer),
            ("--depends-on", args.depends_on),
            ("--ask", args.ask),
        ):
            if value:
                tail += [flag, value]
        if args.non_blocking:
            tail.append("--non-blocking")
    elif cmd == "questionnaire":
        tail += [args.recipient] if getattr(args, "recipient", "") else []
    return run_script("doubts.py", _workspace_args(args) + tail)


def cmd_workspace(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from workspace_tree import ROLES, describe_tree, link, refresh, set_role, unlink
    from workspace_utils import resolve_workspace

    workspace = resolve_workspace(getattr(args, "workspace", None))

    if args.workspace_cmd == "tree":
        print(describe_tree(workspace))
        return 0

    if args.workspace_cmd == "refresh":
        return run_script("hierarchy_sync.py", _workspace_args(args) + (["--no-stage"] if args.no_stage else []))

    if args.workspace_cmd == "sync":
        return run_script("tree_sync.py", _workspace_args(args) + (["--no-stage"] if args.no_stage else []))

    if args.workspace_cmd == "link":
        entry = link(workspace, args.path, name=args.name, map_id=args.map_id)
        print(f"Linked sub-product '{entry['name']}' -> {entry['path']}")
        if entry.get("map_id"):
            print(f"Product map row: {entry['map_id']}")
        else:
            print("No PRODUCT_MAP.md row matched - add one so the master plan accounts for it.")
        print(describe_tree(workspace))
        return 0

    if args.workspace_cmd == "unlink":
        if not unlink(workspace, args.name):
            print(f"No linked sub-product named '{args.name}'.", file=sys.stderr)
            return 1
        print(f"Unlinked '{args.name}'. Its own workspace is untouched.")
        return 0

    if args.workspace_cmd == "role":
        if not args.role:
            tree = refresh(workspace)
            if not tree.get("enabled"):
                print(f"hierarchy disabled: {tree.get('reason')}")
                return 0
            print(f"role={tree.get('role')} pinned={tree.get('pinned', False)}")
            return 0
        if args.role not in ROLES:
            print(f"Unknown role: {args.role} (expected {', '.join(ROLES)})", file=sys.stderr)
            return 2
        set_role(workspace, args.role, pinned=True)
        print(f"Role pinned to '{args.role}' for {workspace}")
        print(describe_tree(workspace))
        return 0

    return 2


def cmd_feature(args: argparse.Namespace) -> int:
    extra: list[str] = []
    if args.feature_cmd == "new":
        extra.append(args.title)
        extra.extend(_workspace_args(args))
        if args.id:
            extra.extend(["--id", args.id])
        if args.step:
            extra.extend(["--step", args.step])
        if args.force:
            extra.append("--force")
        return run_script("new_feature.py", extra)
    if args.feature_cmd == "list":
        return run_script("new_feature.py", ["--list", *_workspace_args(args)])
    if args.feature_cmd == "converge":
        return run_script("feature_converge.py", _workspace_args(args))
    print(f"unknown feature subcommand: {args.feature_cmd}", file=sys.stderr)
    return 2


PLAN_SUBCMDS = frozenset({"scale", "modules", "decompose", "ultraplan"})


def cmd_research(args: argparse.Namespace) -> int:
    extra = [args.query]
    for source in args.sources or []:
        extra.extend(["--source", source])
    if args.limit:
        extra.extend(["--limit", str(args.limit)])
    return run_script("research_search.py", extra)


def cmd_agent_scaffold(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if args.force:
        extra.append("--force")
    return run_script("agent_scaffold.py", extra)


def cmd_plan(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    tokens: list[str] = getattr(args, "tokens", None) or []

    if not tokens:
        print('Usage: loop plan-loop "<product idea>"', file=sys.stderr)
        print("   or: loop plan-loop scale|modules|decompose|ultraplan ...", file=sys.stderr)
        return 2

    head = tokens[0]
    if head not in PLAN_SUBCMDS:
        idea = " ".join(tokens).strip()
        return run_script("plan_idea.py", ["--text", idea, *extra])

    if head == "scale":
        scale_extra = list(extra)
        i = 1
        while i < len(tokens):
            if tokens[i] == "--text" and i + 1 < len(tokens):
                scale_extra.extend(["--text", tokens[i + 1]])
                i += 2
            elif tokens[i] == "--set" and i + 1 < len(tokens):
                scale_extra.extend(["--set", tokens[i + 1]])
                i += 2
            elif tokens[i] == "--write":
                scale_extra.append("--write")
                i += 1
            else:
                i += 1
        return run_script("plan_scale.py", scale_extra)

    if head == "modules":
        rest = tokens[1:]
        types: list[str] = []
        titles: list[str] = []
        i = 0
        while i < len(rest):
            if rest[i] == "--types":
                i += 1
                while i < len(rest) and not rest[i].startswith("--"):
                    types.append(rest[i])
                    i += 1
            else:
                titles.append(rest[i])
                i += 1
        return run_script("ultraplan_harness.py", ["modules", *titles, *(["--types", *types] if types else []), *extra])

    if head == "decompose":
        decomp = ["decompose"]
        if "--force" in tokens:
            decomp.append("--force")
        decomp.extend(extra)
        return run_script("ultraplan_harness.py", decomp)

    if head == "ultraplan":
        if len(tokens) < 2 or tokens[1] not in ("status", "next"):
            print("usage: loop plan-loop ultraplan status|next", file=sys.stderr)
            return 2
        return run_script("ultraplan_harness.py", [tokens[1], *extra])

    return 2


def cmd_bootstrap(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(SCRIPTS))
    from memory_paths import ensure_memory_layout, session_bootstrap_paths
    from skill_resolver import bootstrap_skill_paths
    from workspace_resolver import describe_resolution, resolve_effective_workspace
    from workspace_utils import resolve_workspace

    workspace = resolve_workspace(args.workspace)
    ensure_memory_layout(workspace)
    auto_path, mode = resolve_effective_workspace(getattr(args, "workspace", None))
    print(describe_resolution(auto_path, mode))
    print()
    print("Session bootstrap read order:")
    for path in session_bootstrap_paths(workspace):
        try:
            rel = path.relative_to(workspace)
        except ValueError:
            rel = path
        print(f"  - {rel}")
    print()
    for line in bootstrap_skill_paths(workspace):
        print(line)
    return 0


def _workspace_args(args: argparse.Namespace) -> list[str]:
    if getattr(args, "workspace", None):
        return ["--workspace", args.workspace]
    return []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loop",
        description="Unified CLI for Loop Engineering OS.",
    )
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup", help="First-time setup and workspace registration.")
    setup.add_argument("--name", default=None)
    setup.add_argument("--memory-mode", choices=("local", "global"), default=None)
    setup.add_argument(
        "--role",
        choices=("main", "sub", "standalone"),
        default=None,
        help="Product hierarchy role (default: auto-detect).",
    )
    setup.add_argument("--parent", default=None, help="With --role sub: the main product folder.")
    setup.add_argument("--interactive", action="store_true")
    setup.add_argument("--use-cwd", action="store_true", help="Use current directory as local product workspace.")
    setup.add_argument(
        "--source", default=None, help="Import memory/skills from this external tool's workspace during setup."
    )
    setup.add_argument("--dry-run", action="store_true", help="Preview --source import without writing.")
    setup.add_argument("--overwrite", action="store_true", help="Overwrite existing imported files from --source.")
    setup.add_argument("--scan", action="store_true", help="With --source: classify arbitrary files by content and route them.")
    setup.add_argument("--skip-native-commands", action="store_true", help="Do not install the skills pack into .agents/skills.")
    setup.set_defaults(func=cmd_setup)
    update = sub.add_parser("update", help="Update loop-engineer runtime safely (also refreshes the .agents/skills pack).")
    update.add_argument("--skip-validate", action="store_true", help="Skip template validation after pull.")
    update.add_argument("--skip-native-commands", action="store_true", help="Do not refresh the skills pack in .agents/skills.")
    update.set_defaults(func=cmd_update)
    sub.add_parser("doctor", help="Health-check runtime and product workspace.").set_defaults(func=cmd_doctor)
    sub.add_parser("status", help="Quick workspace snapshot.").set_defaults(func=cmd_status)
    sub.add_parser("sync", help="Reconcile memory/handoff/task drift.").set_defaults(func=cmd_sync)
    sub.add_parser("home", help="Show ~/.loop-engineer layout.").set_defaults(func=cmd_home)
    sub.add_parser("bootstrap", help="Show session bootstrap paths and skill resolution.").set_defaults(func=cmd_bootstrap)

    auto_skills = sub.add_parser("auto-skills", help="Auto-select frontend motion/3D skills from plan context.")
    auto_skills.add_argument("--text", default="", help="Extra context (e.g. user message).")
    auto_skills.add_argument("--write", action="store_true", help="Write plan/AUTO_SKILLS.md.")
    auto_skills.set_defaults(func=cmd_auto_skills)

    sub.add_parser("compact", help="Write COMPACT.md summary.").set_defaults(func=cmd_compact)
    sub.add_parser("prod-gap", help="Analyze production readiness gaps.").set_defaults(func=cmd_prod_gap)

    team = sub.add_parser("team-init", help="Commit a bootstrap so teammates auto-get Loop when they open any agent.")
    team.add_argument("mode", nargs="?", choices=("required", "optional"), default="required")
    team.add_argument("--workspace", default=None, help="Repo root (default: cwd).")
    team.add_argument("--commit", action="store_true", help="git add + commit the bootstrap.")
    team.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    team.set_defaults(func=cmd_team_init)

    release = sub.add_parser("release-check", help="Pre-production release readiness check.")
    release.set_defaults(func=cmd_release_check)

    deploy = sub.add_parser("deployment-plan", help="Write or refresh DEPLOYMENT_PLAN.md.")
    deploy.add_argument("--source", default=None, choices=["plan", "develop", "auto"])
    deploy.set_defaults(func=cmd_deployment_plan)

    session = sub.add_parser("session", help="Search past sessions in state.db.")
    session.add_argument("query", nargs="?", default=None, help="FTS5 query.")
    session.add_argument("--recent", type=int, default=10)
    session.set_defaults(func=cmd_session)

    recall = sub.add_parser("recall", help="Recall past sessions into plan/SESSION_RECALL.md.")
    recall.add_argument("--query", default=None)
    recall.add_argument("--limit", type=int, default=5)
    recall.set_defaults(func=cmd_recall)

    for phase in ("session-start", "session-end"):
        p = sub.add_parser(phase, help=f"Always-on memory lifecycle ({phase.split('-')[1]}).")
        p.add_argument("--workspace", default=None, help="Product workspace path.")
        p.add_argument("--command", default=None, help="Active loop command e.g. /product-develop")
        p.add_argument("--tool", default=None, help="Tool hint: cursor, claude, codex, opencode, grok, api")
        p.add_argument("--text", default="", help="Extra context (user message).")
        if phase == "session-start":
            p.add_argument("--skip-recall", action="store_true")
        if phase == "session-end":
            p.add_argument("--apply", action="store_true", help="Apply memory directly (default: stage).")
            p.add_argument("--summary", default="", help="Closeout summary for state.db")
        p.set_defaults(func=cmd_session_lifecycle, phase="start" if phase == "session-start" else "end")

    memory = sub.add_parser("memory", help="Memory curation commands.")
    memory_sub = memory.add_subparsers(dest="memory_cmd", required=True)
    review = memory_sub.add_parser("review", help="Curate bounded memory and write plan/MEMORY_REVIEW.md.")
    review.add_argument("--apply", action="store_true", help="Apply curation directly.")
    review.add_argument("--stage", action="store_true", help="Stage writes for approval.")
    review.set_defaults(func=cmd_memory)

    migrate = sub.add_parser("migrate", help="Run workspace, external memory, or legacy-layout migration.")
    migrate.add_argument("target", choices=["workspace", "import", "legacy-layout"])
    migrate.add_argument("--dry-run", action="store_true")
    migrate.add_argument("--list", action="store_true")
    migrate.add_argument("--source", default=None, help="Source directory for migrate import.")
    migrate.add_argument("--apply", action="store_true", help="Actually move files for legacy-layout (default: dry-run).")
    migrate.add_argument("--scan", action="store_true", help="With import: classify arbitrary files by content and route them.")
    migrate.set_defaults(func=cmd_migrate)

    pending = sub.add_parser("pending", help="Manage staged memory/skill writes.")
    pending_sub = pending.add_subparsers(dest="pending_cmd", required=True)
    pending_sub.add_parser("list", help="List pending writes.").set_defaults(func=cmd_pending)
    approve = pending_sub.add_parser("approve", help="Approve a pending write.")
    approve.add_argument("id", nargs="?", default=None)
    approve.add_argument("--all", action="store_true")
    approve.add_argument("--kind", choices=("memory", "file", "skill"), default=None, help="Limit to one class, e.g. --kind memory.")
    approve.set_defaults(func=cmd_pending)
    reject = pending_sub.add_parser("reject", help="Reject a pending write.")
    reject.add_argument("id", nargs="?", default=None)
    reject.add_argument("--all", action="store_true")
    reject.add_argument("--kind", choices=("memory", "file", "skill"), default=None, help="Limit to one class.")
    reject.set_defaults(func=cmd_pending)
    dedupe = pending_sub.add_parser("dedupe", help="Drop queued writes proposing identical content.")
    dedupe.add_argument("--dry-run", action="store_true", help="Show what would be dropped.")
    dedupe.set_defaults(func=cmd_pending)

    skills = sub.add_parser("skills", help="List, resolve, or install skills for coding agents.")
    skills_sub = skills.add_subparsers(dest="skills_cmd", required=True)
    skills_sub.add_parser("list", help="List resolved skills.").set_defaults(func=cmd_skills)
    resolve = skills_sub.add_parser("resolve", help="Resolve one skill path.")
    resolve.add_argument("name")
    resolve.set_defaults(func=cmd_skills)
    skill_install = skills_sub.add_parser(
        "install",
        help="Install router skills into every coding agent (Claude, Codex, Cursor, Gemini, OpenCode, ...), pointing at the installed app.",
    )
    skill_install.add_argument("--workspace", default=None, help="Project root for --project (default: cwd).")
    skill_install.add_argument("--user", action="store_true", help="Global scope: each agent's ~/... skills dir (default).")
    skill_install.add_argument("--project", action="store_true", help="Project scope: per-repo skills dirs under the workspace.")
    skill_install.add_argument("--host", action="append", dest="hosts", help="Limit to one agent (repeatable). Default: all.")
    skill_install.add_argument("--detected-only", action="store_true", help="Only agents whose config dir exists (plus universal).")
    skill_install.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    skill_install.set_defaults(func=cmd_skills)
    skill_uninstall = skills_sub.add_parser("uninstall", help="Remove Loop-installed routers from all agents.")
    skill_uninstall.add_argument("--workspace", default=None)
    skill_uninstall.add_argument("--user", action="store_true")
    skill_uninstall.add_argument("--project", action="store_true")
    skill_uninstall.add_argument("--host", action="append", dest="hosts")
    skill_uninstall.add_argument("--dry-run", action="store_true")
    skill_uninstall.set_defaults(func=cmd_skills)
    skill_installed = skills_sub.add_parser("installed", help="Show which routers Loop installed, per agent.")
    skill_installed.add_argument("--workspace", default=None)
    skill_installed.add_argument("--user", action="store_true")
    skill_installed.add_argument("--project", action="store_true")
    skill_installed.add_argument("--host", action="append", dest="hosts")
    skill_installed.set_defaults(func=cmd_skills)

    workspace_p = sub.add_parser(
        "workspace",
        help="Product hierarchy: main product workspace and its sub-product workspaces.",
    )
    workspace_sub = workspace_p.add_subparsers(dest="workspace_cmd", required=True)
    ws_tree = workspace_sub.add_parser("tree", help="Show this workspace's role, parent, and sub-products.")
    ws_tree.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_tree.set_defaults(func=cmd_workspace)
    ws_refresh = workspace_sub.add_parser(
        "refresh", help="Re-scan links and rewrite plan/SUBPRODUCTS.md or plan/PARENT_CONTEXT.md."
    )
    ws_refresh.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_refresh.add_argument("--no-stage", action="store_true", help="Report drift without staging notes into sub-products.")
    ws_refresh.set_defaults(func=cmd_workspace)
    ws_sync = workspace_sub.add_parser(
        "sync", help="Sync main product and sub-products from either folder (backs /product-tree-sync)."
    )
    ws_sync.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_sync.add_argument("--no-stage", action="store_true", help="Report drift without staging notes into sub-products.")
    ws_sync.set_defaults(func=cmd_workspace)
    ws_link = workspace_sub.add_parser("link", help="Link a sub-product workspace (use for folders outside this one).")
    ws_link.add_argument("path", help="Path to the sub-product folder.")
    ws_link.add_argument("--name", default=None, help="Name in the roll-up (default: folder name).")
    ws_link.add_argument("--map-id", default=None, help="PRODUCT_MAP.md row id, e.g. 02.")
    ws_link.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_link.set_defaults(func=cmd_workspace)
    ws_unlink = workspace_sub.add_parser("unlink", help="Forget a linked sub-product (its workspace is untouched).")
    ws_unlink.add_argument("name")
    ws_unlink.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_unlink.set_defaults(func=cmd_workspace)
    ws_role = workspace_sub.add_parser("role", help="Show or pin this workspace's role (main, sub, standalone).")
    ws_role.add_argument("role", nargs="?", default=None, choices=["main", "sub", "standalone"])
    ws_role.add_argument("--workspace", default=argparse.SUPPRESS)
    ws_role.set_defaults(func=cmd_workspace)

    sp = sub.add_parser(
        "subproduct", help="Carve a product-map row out of the main product into its own workspace."
    )
    sp.add_argument("--workspace", default=argparse.SUPPRESS)
    sp_sub = sp.add_subparsers(dest="subproduct_cmd")
    sp_list = sp_sub.add_parser("list", help="Rows typed `sub-product`, and which are ready to carve out.")
    sp_list.add_argument("--workspace", default=argparse.SUPPRESS)
    sp_list.set_defaults(func=cmd_subproduct)
    sp_new = sp_sub.add_parser("new", help="Create a workspace for each map row given.")
    sp_new.add_argument("rows", nargs="+")
    sp_new.add_argument("--dry-run", action="store_true")
    sp_new.add_argument("--workspace", default=argparse.SUPPRESS)
    sp_new.set_defaults(func=cmd_subproduct)
    sp.set_defaults(func=cmd_subproduct)

    fg = sub.add_parser("fog", help="Decisions the plan can see coming but cannot yet state.")
    fg.add_argument("--workspace", default=argparse.SUPPRESS)
    fg_sub = fg.add_subparsers(dest="fog_cmd")
    fg_list = fg_sub.add_parser("list", help="Fog and out-of-scope items, with how long each has sat.")
    fg_list.add_argument("--workspace", default=argparse.SUPPRESS)
    fg_list.set_defaults(func=cmd_fog)
    fg_promote = fg_sub.add_parser("promote", help="State a patch of fog as a doubt and clear it.")
    fg_promote.add_argument("index", type=int)
    fg_promote.add_argument("--non-blocking", action="store_true")
    fg_promote.add_argument("--workspace", default=argparse.SUPPRESS)
    fg_promote.set_defaults(func=cmd_fog)
    fg.set_defaults(func=cmd_fog)

    gl = sub.add_parser("glossary", help="The product's own words, and where the plan drifts from them.")
    gl.add_argument("--workspace", default=argparse.SUPPRESS)
    gl_sub = gl.add_subparsers(dest="glossary_cmd")
    for name, helptext in (
        ("list", "Defined terms and any displaced synonyms still in use."),
        ("lint", "Non-zero exit when a displaced synonym is still in use."),
    ):
        gl_obj = gl_sub.add_parser(name, help=helptext)
        gl_obj.add_argument("--workspace", default=argparse.SUPPRESS)
        gl_obj.set_defaults(func=cmd_glossary)
    gl.set_defaults(func=cmd_glossary)

    ev = sub.add_parser("eval", help="Eval cases, recorded runs, regressions, error analysis.")
    ev.add_argument("--workspace", default=argparse.SUPPRESS)
    ev.add_argument("--threshold", type=float, default=None)
    ev_sub = ev.add_subparsers(dest="eval_cmd")
    for name, helptext in (("status", "Cases, last score, gate, regressions."),
                           ("cases", "Discovered case ids by suite."),
                           ("analyse", "Write plan/EVAL_ANALYSIS.md from the last run.")):
        obj = ev_sub.add_parser(name, help=helptext)
        obj.add_argument("--workspace", default=argparse.SUPPRESS)
        obj.add_argument("--threshold", type=float, default=None)
        obj.set_defaults(func=cmd_eval)
    ev_rec = ev_sub.add_parser("record", help="Persist a scored run from a JSON results file.")
    ev_rec.add_argument("results")
    ev_rec.add_argument("--model", default="")
    ev_rec.add_argument("--notes", default="")
    ev_rec.add_argument("--workspace", default=argparse.SUPPRESS)
    ev_rec.set_defaults(func=cmd_eval)
    ev.set_defaults(func=cmd_eval)

    evidence = sub.add_parser("evidence", help="Evidence past its validity window - uncertain, not disproved.")
    evidence.add_argument("--workspace", default=argparse.SUPPRESS)
    evidence.add_argument("--verbose", action="store_true", help="Include undated entries.")
    evidence.add_argument("--today", default=None, help="Evaluate as of a date (YYYY-MM-DD).")
    evidence.set_defaults(func=cmd_evidence)

    fresh = sub.add_parser("fresh", help="Which generated files no longer match their sources.")
    fresh.add_argument("--workspace", default=argparse.SUPPRESS)
    fresh.add_argument("--all", action="store_true", help="List fresh views too.")
    fresh.set_defaults(func=cmd_fresh)

    graph = sub.add_parser("graph", help="How this workspace's records reference each other.")
    graph_sub = graph.add_subparsers(dest="graph_cmd")
    g_check = graph_sub.add_parser("check", help="Validate the graph against the reference model.")
    g_check.add_argument("--verbose", action="store_true")
    g_check.add_argument("--workspace", default=argparse.SUPPRESS)
    g_check.set_defaults(func=cmd_graph)
    for name, helptext in (
        ("stats", "Node and edge counts."),
        ("build", "Rebuild .loop/graph.json and fold this parse into the edge log."),
        ("orphans", "Records nothing references - compaction candidates."),
        ("dangling", "References to IDs no file anywhere defines."),
        ("closed", "Edges no longer asserted, and how they closed."),
    ):
        obj = graph_sub.add_parser(name, help=helptext)
        obj.add_argument("--workspace", default=argparse.SUPPRESS)
        obj.set_defaults(func=cmd_graph)
    g_show = graph_sub.add_parser("show", help="One record and what it links to.")
    g_show.add_argument("node_id")
    g_show.add_argument("--depth", type=int, default=1)
    g_show.add_argument("--workspace", default=argparse.SUPPRESS)
    g_show.set_defaults(func=cmd_graph)
    g_asof = graph_sub.add_parser("as-of", help="What this plan believed on a date (YYYY-MM-DD).")
    g_asof.add_argument("date")
    g_asof.add_argument("--workspace", default=argparse.SUPPRESS)
    g_asof.set_defaults(func=cmd_graph)

    archive = sub.add_parser(
        "archive", help="Compact finished tasks/doubts in place; full detail to plan/archive/."
    )
    archive.add_argument("--workspace", default=argparse.SUPPRESS)
    archive.add_argument("--dry-run", action="store_true", help="Report what would compact.")
    archive.add_argument("--search", default=None, help="Find an archived answer without loading the file.")
    archive.set_defaults(func=cmd_archive)

    findings = sub.add_parser(
        "findings", help="Findings from the parent product this workspace has not answered."
    )
    findings_sub = findings.add_subparsers(dest="findings_cmd")
    f_list = findings_sub.add_parser("list", help="Open findings from the parent product.")
    f_list.add_argument("--verbose", action="store_true", help="Include the recommended answer.")
    f_list.add_argument("--workspace", default=argparse.SUPPRESS)
    f_list.set_defaults(func=cmd_findings)
    f_ask = findings_sub.add_parser("ask", help="Open findings as questions with recommended answers.")
    f_ask.add_argument("--workspace", default=argparse.SUPPRESS)
    f_ask.set_defaults(func=cmd_findings)
    f_resolve = findings_sub.add_parser("resolve", help="Record a decision about one finding.")
    f_resolve.add_argument("finding_id")
    f_resolve.add_argument("decision", choices=("accepted", "declined", "deferred"))
    f_resolve.add_argument("--note", default="")
    f_resolve.add_argument("--workspace", default=argparse.SUPPRESS)
    f_resolve.set_defaults(func=cmd_findings)

    doubts_p = sub.add_parser("doubts", help="Read and update DOUBTS.md deterministically.")
    doubts_sub = doubts_p.add_subparsers(dest="doubts_cmd")
    d_list = doubts_sub.add_parser("list", help="Open doubts, blocking first.")
    d_list.add_argument("--verbose", action="store_true")
    d_list.add_argument("--workspace", default=argparse.SUPPRESS)
    d_list.set_defaults(func=cmd_doubts)
    for name, helptext in (
        ("ask", "This round of questions: the ones whose prerequisites are settled."),
        ("lint", "Entries whose status contradicts their content."),
        ("counts", "One authoritative count for every command to use."),
    ):
        parser_obj = doubts_sub.add_parser(name, help=helptext)
        parser_obj.add_argument("--workspace", default=argparse.SUPPRESS)
        parser_obj.set_defaults(func=cmd_doubts)
    d_quest = doubts_sub.add_parser(
        "questionnaire", help="Write out questions somebody other than the user must answer."
    )
    d_quest.add_argument("recipient", nargs="?", default="")
    d_quest.add_argument("--workspace", default=argparse.SUPPRESS)
    d_quest.set_defaults(func=cmd_doubts)
    d_resolve = doubts_sub.add_parser("resolve", help="Mark a doubt resolved, recording the answer.")
    d_resolve.add_argument("doubt_id")
    d_resolve.add_argument("answer")
    d_resolve.add_argument("--decision", default="", help="DECISIONS.md id to cross-link, e.g. D-014")
    d_resolve.add_argument("--workspace", default=argparse.SUPPRESS)
    d_resolve.set_defaults(func=cmd_doubts)
    d_add = doubts_sub.add_parser("add", help="Record a new question so the next session inherits it.")
    d_add.add_argument("title")
    d_add.add_argument("question")
    d_add.add_argument("--why", default="")
    d_add.add_argument("--default", dest="default_answer", default="")
    d_add.add_argument("--depends-on", default="")
    d_add.add_argument("--ask", default="")
    d_add.add_argument("--non-blocking", action="store_true")
    d_add.add_argument("--workspace", default=argparse.SUPPRESS)
    d_add.set_defaults(func=cmd_doubts)
    d_defer = doubts_sub.add_parser("defer", help="Mark a doubt deferred, recording why.")
    d_defer.add_argument("doubt_id")
    d_defer.add_argument("reason")
    d_defer.add_argument("--workspace", default=argparse.SUPPRESS)
    d_defer.set_defaults(func=cmd_doubts)

    feature = sub.add_parser("feature", help="Feature spec folders under plan/features/.")
    feature_sub = feature.add_subparsers(dest="feature_cmd", required=True)
    feat_new = feature_sub.add_parser("new", help="Create numbered feature folder and set active.")
    feat_new.add_argument("title", help='Feature title e.g. "auth login"')
    feat_new.add_argument("--id", default=None)
    feat_new.add_argument("--step", default=None)
    feat_new.add_argument("--force", action="store_true")
    feat_new.set_defaults(func=cmd_feature)
    feature_sub.add_parser("list", help="List feature folders.").set_defaults(func=cmd_feature)
    feature_sub.add_parser("converge", help="Drift check for active feature.").set_defaults(func=cmd_feature)

    plan = sub.add_parser(
        "plan-loop",
        help='Auto-plan from idea: loop plan-loop "your product idea" (scale + ultraplan automatic).',
    )
    plan.add_argument(
        "tokens",
        nargs="*",
        help='Product idea text, or subcommand: scale, modules, decompose, ultraplan status|next',
    )
    plan.set_defaults(func=cmd_plan)


    research = sub.add_parser("research", help="Search arXiv, Research Square, and SSRN.")
    research.add_argument("query", help="Search terms")
    research.add_argument(
        "--source", action="append", dest="sources", choices=("arxiv", "researchsquare", "ssrn")
    )
    research.add_argument("--limit", type=int, default=None)
    research.set_defaults(func=cmd_research)

    auto_agent = sub.add_parser(
        "auto-agent-skills", help="Auto-detect AI-agent-development signals from plan context."
    )
    auto_agent.add_argument("--text", default="", help="Extra context (e.g. user message).")
    auto_agent.add_argument("--write", action="store_true", help="Write plan/AUTO_AGENT_SKILLS.md.")
    auto_agent.set_defaults(func=cmd_auto_agent_skills)

    agent = sub.add_parser("agent", help="AI agent development scaffolding.")
    agent_sub = agent.add_subparsers(dest="agent_cmd", required=True)
    scaffold = agent_sub.add_parser("scaffold", help="Scaffold agent/ skill+tool+eval structure in the workspace.")
    scaffold.add_argument("--force", action="store_true", help="Overwrite existing scaffold files.")
    scaffold.set_defaults(func=cmd_agent_scaffold)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
