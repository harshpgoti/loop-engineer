#!/usr/bin/env python3
"""Apply safe product-workspace migrations as Loop Engineering OS evolves."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import date
from pathlib import Path

from workspace_utils import ROOT, resolve_workspace


VERSION_FILE = ".loop-workspace-version"
MIGRATIONS_DIR = ROOT / "migrations"


def load_version(workspace: Path) -> int:
    path = workspace / VERSION_FILE
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return int(data.get("version", 0))


def save_version(workspace: Path, version: int) -> None:
    path = workspace / VERSION_FILE
    path.write_text(json.dumps({"version": version, "updated": date.today().isoformat()}, indent=2) + "\n", encoding="utf-8")


def load_migration_modules() -> list[tuple[int, str, object]]:
    modules: list[tuple[int, str, object]] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        migration_id = int(getattr(module, "MIGRATION_ID"))
        name = str(getattr(module, "NAME"))
        modules.append((migration_id, name, module))
    return sorted(modules, key=lambda item: item[0])


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

    migrations = load_migration_modules()
    if args.list:
        for migration_id, name, _ in migrations:
            print(f"{migration_id:03d} {name}")
        return 0

    workspace = resolve_workspace(args.workspace)
    current = load_version(workspace)
    pending = [(mid, name, module) for mid, name, module in migrations if mid > current]

    if not pending:
        print(f"Workspace `{workspace}` is up to date (version {current}).")
        return 0

    print(f"Workspace `{workspace}` version {current}; pending migrations: {len(pending)}")
    applied: list[str] = []

    for migration_id, name, module in pending:
        print(f"Applying {migration_id:03d} {name}...")
        if args.dry_run:
            applied.append(f"would apply {migration_id:03d} {name}")
            continue
        results = module.apply(workspace, seed_file_if_missing)
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
            f"## {date.today().isoformat()} — Workspace migration\n\n"
            f"- Updated `{VERSION_FILE}` to version {load_version(workspace)}.\n"
        )

    print(f"Migration complete. Workspace version {load_version(workspace)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
