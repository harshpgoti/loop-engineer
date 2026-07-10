#!/usr/bin/env python3
"""Register and switch product workspaces."""

from __future__ import annotations

import argparse
from pathlib import Path

from workspace_utils import ROOT, load_config, save_config


def normalize_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path.resolve().as_posix()
    return path.as_posix()


def cmd_register(args: argparse.Namespace) -> int:
    config = load_config()
    workspaces = config.setdefault("workspaces", {})
    entry: dict[str, str] = {"path": normalize_path(args.path)}
    if args.memory_mode:
        entry["memory_mode"] = args.memory_mode
    workspaces[args.name] = entry
    if args.set_current or not config.get("current"):
        config["current"] = args.name
    save_config(config)
    print(f"Registered workspace '{args.name}' -> {workspaces[args.name]['path']}")
    if entry.get("memory_mode"):
        print(f"Memory mode: {entry['memory_mode']}")
    if config.get("current") == args.name:
        print(f"Current workspace: {args.name}")
    return 0


def cmd_use(args: argparse.Namespace) -> int:
    config = load_config()
    if args.name not in config.get("workspaces", {}):
        raise SystemExit(f"Unknown workspace: {args.name}")
    config["current"] = args.name
    save_config(config)
    print(f"Current workspace: {args.name}")
    return 0


def cmd_current(_: argparse.Namespace) -> int:
    config = load_config()
    current = config.get("current")
    if not current:
        print("No current workspace registered.")
        return 1
    workspace = config.get("workspaces", {}).get(current, {})
    print(f"{current}: {workspace.get('path')}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    config = load_config()
    current = config.get("current")
    workspaces = config.get("workspaces", {})
    if not workspaces:
        print("No workspaces registered.")
        return 0
    for name, data in sorted(workspaces.items()):
        marker = "*" if name == current else " "
        mode = data.get("memory_mode", "local")
        print(f"{marker} {name} [{mode}]: {data.get('path')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Loop Engineering OS product workspaces.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="Register a product workspace")
    register.add_argument("--name", required=True, help="Workspace name")
    register.add_argument("--path", required=True, help="Path to product workspace")
    register.add_argument(
        "--memory-mode",
        choices=("local", "global"),
        default=None,
        help="local = product folder; global = ~/.loop-engineer/",
    )
    register.add_argument("--set-current", action="store_true", help="Set as current workspace")
    register.set_defaults(func=cmd_register)

    use = subparsers.add_parser("use", help="Set current workspace")
    use.add_argument("name", help="Workspace name")
    use.set_defaults(func=cmd_use)

    current = subparsers.add_parser("current", help="Show current workspace")
    current.set_defaults(func=cmd_current)

    list_cmd = subparsers.add_parser("list", help="List registered workspaces")
    list_cmd.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
