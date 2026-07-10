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

    print("\nProduct memory was not overwritten.")
    print("Next: loop doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
