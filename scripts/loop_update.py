#!/usr/bin/env python3
"""Update Loop Engineer app runtime without touching product memory."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from loop_home import app_path, describe_layout, ensure_loop_home
from workspace_utils import ROOT, resolve_workspace


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
    return result.returncode, ((result.stdout or "") + (result.stderr or "")).strip()


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
    parser.add_argument(
        "--legacy-commands",
        action="store_true",
        help="Also refresh the deprecated per-tool command wrappers.",
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

    workspace = resolve_workspace(args.workspace)
    migrate = runtime / "scripts" / "migrate_workspace.py"
    if migrate.exists() and workspace.exists():
        code, out = run([sys.executable, str(migrate), "--workspace", str(workspace)], runtime)
        print(out)

    if not args.skip_native_commands:
        skills_script = runtime / "scripts" / "install_skills.py"
        if skills_script.exists():
            print("\nRefreshing router skills across all coding agents...")
            code, out = run([sys.executable, str(skills_script), "--user"], runtime)
            print(out)
            # Refresh project-scope routers too when a local workspace is active.
            if workspace.exists():
                code, out = run([sys.executable, str(skills_script), "--project", "--workspace", str(workspace)], runtime)
                print(out)
        if getattr(args, "legacy_commands", False):
            gen = runtime / "scripts" / "generate_agent_commands.py"
            if gen.exists():
                print("\n[legacy] Refreshing per-tool command wrappers...")
                # app-root defaults to `runtime`, so wrappers re-point at the updated app.
                code, out = run([sys.executable, str(gen), "--tool", "all", "--scope", "user"], runtime)
                print(out)

    print("\nProduct memory was not overwritten.")
    print("Next: loop doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
