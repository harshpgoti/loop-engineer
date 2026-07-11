#!/usr/bin/env python3
"""First-time setup for Loop Engineering OS.

Memory layout:
  global (default) - product data in ~/.loop-engineer/data/
  local            - product data in <product-folder>/.loop-engineer/ (auto-detected on return)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from memory_paths import ensure_memory_layout, memory_file, state_db
from session_store import init_db
from setup_options import (
    MEMORY_MODES,
    describe_memory_mode,
    infer_memory_mode,
    parse_interactive_mode,
    print_memory_mode_menu,
    resolve_workspace_path,
)
from workspace_utils import ROOT, load_config, save_config


STARTER_FILES = [
    "plan/main_plan.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "HANDOFF.md",
    "CURRENT_STATE.md",
    "DECISIONS.md",
    "EVIDENCE_LOG.md",
    "COMPACT.md",
    "plan/README.md",
    ".ai/SESSION_LOG.md",
    "docs/ACCEPTANCE_CRITERIA.md",
    "docs/TEST_PLAN.md",
    "docs/interview_script.md",
]


def normalize_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path.resolve().as_posix()
    return path.as_posix()


def register_workspace(name: str, workspace: Path, memory_mode: str) -> None:
    config = load_config()
    workspaces = config.setdefault("workspaces", {})
    workspaces[name] = {
        "path": str(workspace.resolve()),
        "memory_mode": memory_mode,
    }
    config["current"] = name
    save_config(config)


def copy_missing_file(relative_path: str, workspace: Path) -> str:
    source = ROOT / "templates" / "starter" / relative_path
    target = workspace / relative_path
    if target.exists():
        return "skipped"
    if not source.exists():
        return "missing-source"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return "created"


def resolve_memory_mode(args: argparse.Namespace, workspace: Path) -> str:
    if args.memory_mode:
        if args.memory_mode not in MEMORY_MODES:
            raise SystemExit(f"Invalid --memory-mode: {args.memory_mode}")
        return args.memory_mode

    if args.use_cwd:
        return "local"

    if args.interactive and sys.stdin.isatty():
        print_memory_mode_menu()
        try:
            choice = input("Enter 1 or 2 [2]: ").strip() or "2"
            return parse_interactive_mode(choice)
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            raise SystemExit(1) from None

    return infer_memory_mode(workspace, "global")


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up Loop Engineering OS for a product workspace.")
    parser.add_argument("--workspace", default=None, help="Product folder for local mode.")
    parser.add_argument("--name", default="global", help="Registry name. Defaults to global.")
    parser.add_argument(
        "--memory-mode",
        choices=MEMORY_MODES,
        default=None,
        help="Default is global. Use local for product-folder memory.",
    )
    parser.add_argument("--interactive", action="store_true", help="Prompt for local vs global.")
    parser.add_argument(
        "--use-cwd",
        action="store_true",
        help="Use current directory as local product workspace.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Import memory/skills from this external tool's workspace during setup (e.g. its MEMORY.md, USER.md, skills/).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview --source import without writing.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing imported files from --source.")
    parser.add_argument(
        "--scan",
        action="store_true",
        help="With --source: classify arbitrary files by content and route them to the right homes.",
    )
    parser.add_argument(
        "--skip-native-commands",
        action="store_true",
        help="Do not generate native slash-command wrappers for agent CLIs (claude, cursor, codex, opencode).",
    )
    args = parser.parse_args()

    cwd = Path.cwd() if args.use_cwd else None
    if args.use_cwd and args.name == "global":
        args.name = Path.cwd().name or "product"

    memory_mode = args.memory_mode or ("local" if args.use_cwd else None)
    if memory_mode is None and not args.interactive:
        memory_mode = "global"

    provisional = resolve_workspace_path(
        memory_mode=memory_mode or "global",
        workspace=args.workspace,
        name=args.name,
        root=ROOT,
        cwd=cwd,
    )
    if memory_mode is None:
        memory_mode = resolve_memory_mode(args, provisional)

    workspace = resolve_workspace_path(
        memory_mode=memory_mode,
        workspace=args.workspace,
        name=args.name,
        root=ROOT,
        cwd=cwd,
    )
    workspace.mkdir(parents=True, exist_ok=True)
    register_workspace(args.name, workspace, memory_mode)

    memory_actions = ensure_memory_layout(workspace)
    init_db(state_db(workspace))

    created: list[str] = []
    skipped: list[str] = []
    missing_source: list[str] = []

    for relative_path in STARTER_FILES:
        status = copy_missing_file(relative_path, workspace)
        if status == "created":
            created.append(relative_path)
        elif status == "skipped":
            skipped.append(relative_path)
        else:
            missing_source.append(relative_path)

    print(f"Registered workspace '{args.name}' -> {workspace.resolve()}")
    print(f"Memory mode: {memory_mode}")
    print(describe_memory_mode(memory_mode, workspace))
    print("Memory layout:")
    for key, value in memory_actions.items():
        print(f"  {key}: {value}")
    print(f"  canonical memory: {memory_file(workspace)}")
    print(f"Created files: {len(created)}")
    for item in created:
        print(f"  created {item}")
    print(f"Skipped existing files: {len(skipped)}")
    for item in skipped:
        print(f"  skipped {item}")
    if missing_source:
        print(f"Missing source templates: {len(missing_source)}")
        for item in missing_source:
            print(f"  missing source {item}")

    if args.source:
        from migrate_import import run_import

        print(f"\nImporting memory/skills from {args.source}...")
        import_summary = run_import(
            workspace,
            args.source,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            log_command="/setup-loop-engine",
            memory_actions=memory_actions,
        )
        for line in import_summary:
            print(f"  {line}")
        if args.scan:
            from import_scanner import run_scan_import
            from migrate_import import append_handoff, find_source_root

            scan_summary = run_scan_import(
                workspace, find_source_root(args.source), dry_run=args.dry_run, exclude_known=True
            )
            for line in scan_summary:
                print(f"  {line}")
            if not args.dry_run:
                append_handoff(workspace, scan_summary)
        if args.dry_run:
            print("  Dry run only. Re-run without --dry-run to apply.")

    migrate_script = ROOT / "scripts" / "migrate_workspace.py"
    if migrate_script.exists():
        print("\nApplying workspace migrations...")
        subprocess.run(
            [sys.executable, str(migrate_script), "--workspace", str(workspace)],
            cwd=ROOT,
            check=False,
        )

    detect_script = ROOT / "scripts" / "detect_workspace.py"
    if detect_script.exists():
        print("\nWorkspace detection:")
        subprocess.run([sys.executable, str(detect_script)], cwd=ROOT, check=False)

    gen_script = ROOT / "scripts" / "generate_agent_commands.py"
    if not args.skip_native_commands and gen_script.exists():
        print("\nRegistering native slash commands for agent CLIs...")
        subprocess.run(
            [sys.executable, str(gen_script), "--tool", "all", "--scope", "user"],
            cwd=ROOT,
            check=False,
        )

    if memory_mode == "local":
        print("\nWhen you return to this folder, /plan-loop and /loop-engine auto-use local data here.")
    else:
        print("\nGlobal data lives in ~/.loop-engineer/data/. Local product folders override when detected.")

    print("\nNext command: /plan-loop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
