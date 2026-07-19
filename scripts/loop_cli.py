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
    cmd = [sys.executable, str(SCRIPTS / script), *args]
    result = subprocess.run(cmd, check=False)
    return int(result.returncode)


def cmd_setup(args: argparse.Namespace) -> int:
    extra = _workspace_args(args)
    if getattr(args, "name", None):
        extra.extend(["--name", args.name])
    if getattr(args, "memory_mode", None):
        extra.extend(["--memory-mode", args.memory_mode])
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
    if getattr(args, "legacy_commands", False):
        extra.append("--legacy-commands")
    return run_script("setup_loop_engine.py", extra)


def cmd_update(args: argparse.Namespace) -> int:
    extra: list[str] = []
    if getattr(args, "skip_validate", False):
        extra.append("--skip-validate")
    if getattr(args, "skip_native_commands", False):
        extra.append("--skip-native-commands")
    if getattr(args, "legacy_commands", False):
        extra.append("--legacy-commands")
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
    from pending_writes import approve_pending, list_pending, reject_pending
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
    if args.pending_cmd == "approve":
        results = approve_pending(workspace, write_id=args.id, approve_all=args.all)
        for line in results:
            print(line)
        return 0 if results else 1
    if args.pending_cmd == "reject":
        results = reject_pending(workspace, write_id=args.id, reject_all=args.all)
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


def cmd_commands(args: argparse.Namespace) -> int:
    if args.commands_cmd != "install":
        print(f"unknown commands subcommand: {args.commands_cmd}", file=sys.stderr)
        return 2
    extra: list[str] = ["--tool", args.tool, "--scope", args.scope]
    if getattr(args, "workspace", None):
        extra.extend(["--workspace", args.workspace])
    if getattr(args, "app_root", None):
        extra.extend(["--app-root", args.app_root])
    if getattr(args, "dry_run", False):
        extra.append("--dry-run")
    if getattr(args, "force", False):
        extra.append("--force")
    return run_script("generate_agent_commands.py", extra)


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
    setup.add_argument("--interactive", action="store_true")
    setup.add_argument("--use-cwd", action="store_true", help="Use current directory as local product workspace.")
    setup.add_argument(
        "--source", default=None, help="Import memory/skills from this external tool's workspace during setup."
    )
    setup.add_argument("--dry-run", action="store_true", help="Preview --source import without writing.")
    setup.add_argument("--overwrite", action="store_true", help="Overwrite existing imported files from --source.")
    setup.add_argument("--scan", action="store_true", help="With --source: classify arbitrary files by content and route them.")
    setup.add_argument("--skip-native-commands", action="store_true", help="Do not install the skills pack into .agents/skills.")
    setup.add_argument("--legacy-commands", action="store_true", help="Also generate the deprecated per-tool command wrappers.")
    setup.set_defaults(func=cmd_setup)
    update = sub.add_parser("update", help="Update loop-engineer runtime safely (also refreshes the .agents/skills pack).")
    update.add_argument("--skip-validate", action="store_true", help="Skip template validation after pull.")
    update.add_argument("--skip-native-commands", action="store_true", help="Do not refresh the skills pack in .agents/skills.")
    update.add_argument("--legacy-commands", action="store_true", help="Also refresh the deprecated per-tool command wrappers.")
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
    approve.set_defaults(func=cmd_pending)
    reject = pending_sub.add_parser("reject", help="Reject a pending write.")
    reject.add_argument("id", nargs="?", default=None)
    reject.add_argument("--all", action="store_true")
    reject.set_defaults(func=cmd_pending)

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

    commands = sub.add_parser("commands", help="Generate native slash-command wrappers for supported agent CLIs.")
    commands_sub = commands.add_subparsers(dest="commands_cmd", required=True)
    install = commands_sub.add_parser(
        "install",
        help="Write native /command wrappers into each tool's command dir (claude, cursor, codex, opencode).",
    )
    install.add_argument("--tool", choices=["claude", "cursor", "codex", "opencode", "all"], default="all")
    install.add_argument("--scope", choices=["user", "project"], default="user")
    install.add_argument("--app-root", default=None, help="Loop Engineer app dir the wrappers point at (default: this app).")
    install.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    install.add_argument("--force", action="store_true", help="Overwrite files without the generated marker.")
    install.set_defaults(func=cmd_commands)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
