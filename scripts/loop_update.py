#!/usr/bin/env python3
"""Update Loop Engineer app runtime without touching product memory."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loop_home import app_path, describe_layout, ensure_loop_home
from workspace_utils import ROOT, load_config, resolve_workspace


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return result.returncode, ((result.stdout or "") + (result.stderr or "")).strip()


def workspaces_to_migrate(explicit: str | None) -> list[Path]:
    """Every workspace an update must bring to the current schema.

    `loop update` is an app-level operation, but schema migrations are per
    workspace - and nothing else applies them (`loop session-start` does not
    migrate). Migrating only the resolved workspace silently strands every other
    registered product on an older schema until someone happens to run an update
    from inside it. So update walks the whole registry.

    `--workspace` still targets exactly one, for recovering a single product.
    """
    if explicit:
        return [resolve_workspace(explicit)]

    found: list[Path] = []
    seen: set[Path] = set()
    for entry in load_config().get("workspaces", {}).values():
        raw = entry.get("path", "")
        if not raw:
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = (ROOT / raw).resolve()
        path = path.resolve()
        if path in seen or not path.exists():
            continue
        seen.add(path)
        found.append(path)

    # The active workspace may not be registered (a folder found by walking up).
    active = resolve_workspace(None)
    if active.exists() and active.resolve() not in seen:
        found.append(active.resolve())
    return found


def resolve_runtime_root() -> Path:
    installed = app_path()
    if (installed / ".git").exists():
        return installed
    return ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description="Update Loop Engineer app without touching product memory.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument(
        "--skip-native-commands",
        action="store_true",
        help="Do not refresh the skills pack in .agents/skills.",
    )
    args = parser.parse_args()

    ensure_loop_home()
    runtime = resolve_runtime_root()
    print(describe_layout())
    print(f"App root: {runtime}")

    code, out = run(["git", "pull"], runtime)
    print(out or f"git pull exit {code}")
    if code != 0:
        return code

    if not args.skip_validate:
        validate = runtime / "scripts" / "validate_template.py"
        if validate.exists():
            code, out = run([sys.executable, str(validate)], runtime)
            print(out)
            if code != 0:
                return code

    migrate = runtime / "scripts" / "migrate_workspace.py"
    if migrate.exists():
        for workspace in workspaces_to_migrate(args.workspace):
            code, out = run([sys.executable, str(migrate), "--workspace", str(workspace)], runtime)
            print(out)

    if not args.skip_native_commands:
        skills_script = runtime / "scripts" / "install_skills.py"
        if skills_script.exists():
            print("\nRefreshing router skills across all coding agents...")
            # User scope only - see the note in setup_loop_engine.py. Project-scope
            # routers would double every command in tools that list both scopes.
            code, out = run([sys.executable, str(skills_script), "--user"], runtime)
            print(out)

    print("\nProduct memory was not overwritten.")
    print("Next: loop doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
