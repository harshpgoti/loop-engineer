#!/usr/bin/env python3
"""Safely copy Loop Engineering OS tool files into a product workspace.

Default mode is dry-run. Use --apply to make changes. Product-state files are
protected and are never copied from the source.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROTECTED_PATHS = {
    "main_plan.md",
    "plan",
    "MEMORY.md",
    "DOUBTS.md",
    "TASKS.yml",
    "GATES.yml",
    "HANDOFF.md",
    "CURRENT_STATE.md",
    "DECISIONS.md",
    "EVIDENCE_LOG.md",
    "COMPACT.md",
    "DEPLOYMENT_PLAN.md",
    "memories",
    "skills",
    "state.db",
    ".ai",
    "docs",
}

TOOL_PATHS = [
    "commands",
    "skills",
    "scripts",
    "templates",
    "migrations",
    "tools",
    "evals",
    "docs",
    "AGENTS.md",
    "CURSOR.md",
    "CLAUDE.md",
    "CODEX.md",
    "OPENCODE.md",
    "GROK.md",
    "ADAPTERS.md",
    "AGENT_BOOT_SEQUENCE.md",
    "LOOP_COMMANDS.md",
    "LOOP_SCHEDULE.md",
    "STARTUP_LOOP_ENGINEERING_PLAYBOOK.md",
    "README.md",
    "INSTALL.md",
    "CONTRIBUTING.md",
]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_protected(relative_path: str) -> bool:
    first = relative_path.split("/", 1)[0]
    return relative_path in PROTECTED_PATHS or first in PROTECTED_PATHS


def iter_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for item in TOOL_PATHS:
        path = source / item
        if not path.exists():
            continue
        if path.is_file():
            files.append(path)
            continue
        for child in path.rglob("*"):
            if child.is_file() and ".git" not in child.parts:
                files.append(child)
    return files


def same_file(source: Path, target: Path) -> bool:
    return target.exists() and filecmp.cmp(source, target, shallow=False)


def backup_existing(target_file: Path, backup_root: Path, target_root: Path) -> None:
    if not target_file.exists():
        return
    backup_file = backup_root / target_file.relative_to(target_root)
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_file, backup_file)


def copy_tool_files(source: Path, target: Path, apply: bool) -> tuple[list[str], list[str], list[str]]:
    copied: list[str] = []
    skipped: list[str] = []
    protected_hits: list[str] = []
    backup_root = target / ".loop-upgrade-backup" / datetime.now().strftime("%Y%m%d-%H%M%S")

    for source_file in iter_files(source):
        relative = rel(source_file, source)
        if is_protected(relative):
            protected_hits.append(relative)
            continue

        target_file = target / relative
        if same_file(source_file, target_file):
            skipped.append(relative)
            continue

        copied.append(relative)
        if apply:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            backup_existing(target_file, backup_root, target)
            shutil.copy2(source_file, target_file)

    if apply and copied:
        print(f"Backup written to: {backup_root}")

    return copied, skipped, protected_hits


def refresh_routers(target: Path) -> None:
    """Re-wire agents after an embedded upgrade so router skills track the new
    command set. Runs the target's own install_skills so routers point at this
    upgraded copy. Failure-safe - never aborts the upgrade."""
    script = target / "scripts" / "install_skills.py"
    if not script.exists():
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--user"],
            cwd=str(target),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("Refreshed router skills for all coding agents.")
        else:
            print("Router refresh skipped (run `loop skills install` manually).")
    except (OSError, subprocess.TimeoutExpired):
        print("Router refresh skipped (run `loop skills install` manually).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely upgrade Loop Engineering OS tool files.")
    parser.add_argument("--source", required=True, help="Path to updated loop-engineer repo")
    parser.add_argument("--target", required=True, help="Path to product workspace or embedded copy")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    parser.add_argument("--skip-native-commands", action="store_true", help="Do not refresh router skills after apply.")
    args = parser.parse_args()

    source = Path(args.source).resolve()
    target = Path(args.target).resolve()

    if not source.exists():
        raise SystemExit(f"Source does not exist: {source}")
    if not target.exists():
        raise SystemExit(f"Target does not exist: {target}")

    copied, skipped, protected_hits = copy_tool_files(source, target, args.apply)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"Mode: {mode}")
    print(f"Source: {source}")
    print(f"Target: {target}")
    print()
    print(f"Files to update: {len(copied)}")
    for item in copied:
        print(f"  update {item}")
    print()
    print(f"Unchanged tool files: {len(skipped)}")
    print(f"Protected paths ignored: {len(protected_hits)}")

    if protected_hits:
        for item in protected_hits:
            print(f"  protected {item}")

    if args.apply and not args.skip_native_commands:
        refresh_routers(target)

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to copy tool files.")
        if any(c == "commands" or c.startswith("commands/") for c in copied):
            print("On --apply, router skills for all agents are refreshed automatically.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
