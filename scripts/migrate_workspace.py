#!/usr/bin/env python3
"""Apply safe product-workspace migrations as Loop Engineering OS evolves."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Callable

from workspace_utils import ROOT, resolve_workspace


VERSION_FILE = ".loop-workspace-version"
CURRENT_WORKSPACE_VERSION = 8
SeedFile = Callable[[Path, str, str], str | None]
Migration = Callable[[Path, SeedFile], list[str]]


def load_version(workspace: Path) -> int:
    path = workspace / VERSION_FILE
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data.get("version", 0))


def save_version(workspace: Path, version: int) -> None:
    path = workspace / VERSION_FILE
    path.write_text(json.dumps({"version": version, "updated": date.today().isoformat()}, indent=2) + "\n", encoding="utf-8")


def apply_workspace_v8(
    workspace: Path, seed: SeedFile
) -> list[str]:
    """Bring any workspace at versions 0-7 to the current canonical layout."""
    results: list[str] = []
    for rel, source in (
        ("COMPACT.md", "templates/starter/COMPACT.md"),
        ("plan/PROD-GAP.md", "templates/prod_gap.template.md"),
        ("RELEASE_CHECK.md", "templates/release_check.template.md"),
        ("STATUS.md", "templates/status.template.md"),
        ("DOCTOR.md", "templates/doctor.template.md"),
        ("SYNC_REPORT.md", "templates/sync_loop_state.template.md"),
        ("DEPLOYMENT_PLAN.md", "templates/deployment_plan.template.md"),
        ("plan/SESSION_RECALL.md", "templates/session_recall.template.md"),
        ("plan/MEMORY_REVIEW.md", "templates/memory_review.template.md"),
    ):
        created = seed(workspace, rel, source)
        if created:
            results.append(created)

    from memory_paths import ensure_memory_layout, state_db
    from session_store import init_db

    results.extend(f"{key}: {value}" for key, value in ensure_memory_layout(workspace).items())
    database = state_db(workspace)
    if not database.exists():
        init_db(database)
        results.append("initialized state.db")

    pending = workspace / ".loop" / "pending"
    (pending / "memory").mkdir(parents=True, exist_ok=True)
    (pending / "skills").mkdir(parents=True, exist_ok=True)
    results.append("pending write dirs: ensured")

    main_src = workspace / "main_plan.md"
    main_dest = workspace / "plan" / "main_plan.md"
    if main_src.exists() and not main_dest.exists():
        main_dest.parent.mkdir(parents=True, exist_ok=True)
        main_src.rename(main_dest)
        results.append("moved main_plan.md -> plan/main_plan.md")
    elif main_src.exists():
        results.append("both main_plan.md and plan/main_plan.md exist - review the root copy manually")

    root_mem = workspace / "MEMORY.md"
    canonical_mem = workspace / "memories" / "MEMORY.md"
    if root_mem.exists():
        if not canonical_mem.exists():
            canonical_mem.parent.mkdir(parents=True, exist_ok=True)
            root_mem.rename(canonical_mem)
            results.append("moved root MEMORY.md -> memories/MEMORY.md")
        elif root_mem.read_text(encoding="utf-8", errors="ignore").strip() == canonical_mem.read_text(
            encoding="utf-8", errors="ignore"
        ).strip():
            root_mem.unlink()
            results.append("removed root MEMORY.md (exact duplicate of memories/MEMORY.md)")
        else:
            backup = workspace / "memories" / "MEMORY.root-legacy.md"
            if backup.exists():
                results.append("root MEMORY.md differs from canonical and backup already exists - review manually")
            else:
                root_mem.rename(backup)
                results.append("preserved divergent root MEMORY.md as memories/MEMORY.root-legacy.md")

    startup = workspace / "STARTUP_MEMORY.md"
    if startup.exists():
        destination = workspace / "memories" / "STARTUP_MEMORY.md"
        if destination.exists():
            results.append("STARTUP_MEMORY.md exists in both places - review manually")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            startup.rename(destination)
            results.append("moved legacy STARTUP_MEMORY.md -> memories/STARTUP_MEMORY.md")
    return results


def migrations() -> list[tuple[int, str, Migration]]:
    return [(CURRENT_WORKSPACE_VERSION, "organize_memory_layout", apply_workspace_v8)]


def seed_file_if_missing(workspace: Path, relative_path: str, source_relative: str) -> str | None:
    target = workspace / relative_path
    if target.exists():
        return None
    source = ROOT / source_relative
    if not source.exists():
        return f"missing source template for {relative_path}"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return f"created {relative_path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply pending product workspace migrations.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    parser.add_argument("--dry-run", action="store_true", help="Show pending migrations without applying.")
    parser.add_argument("--list", action="store_true", help="List available migrations.")
    args = parser.parse_args()

    available = migrations()
    if args.list:
        for migration_id, name, _ in available:
            print(f"{migration_id:03d} {name}")
        return 0

    workspace = resolve_workspace(args.workspace)
    current = load_version(workspace)
    pending = [(mid, name, apply) for mid, name, apply in available if mid > current]

    if not pending:
        print(f"Workspace `{workspace}` is up to date (version {current}).")
        return 0

    print(f"Workspace `{workspace}` version {current}; pending migrations: {len(pending)}")
    applied: list[str] = []

    for migration_id, name, apply in pending:
        print(f"Applying {migration_id:03d} {name}...")
        if args.dry_run:
            applied.append(f"would apply {migration_id:03d} {name}")
            continue
        results = apply(workspace, seed_file_if_missing)
        applied.extend(results)
        save_version(workspace, migration_id)

    if args.dry_run:
        for item in applied:
            print(f"- {item}")
        return 0

    for item in applied:
        print(f"- {item}")

    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} - Workspace migration\n\n"
            f"- Updated `{VERSION_FILE}` to version {load_version(workspace)}.\n"
        )

    print(f"Migration complete. Workspace version {load_version(workspace)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
