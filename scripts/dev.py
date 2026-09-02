#!/usr/bin/env python3
"""Stack-agnostic developer-experience commands.

Implements the runtime half of `/lint`, `/test`, `/commit`. Each command
reads a workspace-level config (`<workspace>/.loop/dev_config.json`) to
discover the right commands to run for the current project.

Config schema (all fields optional; defaults are stack-agnostic fallbacks):

```json
{
  "lint": {
    "command": "ruff check .",
    "fix_command": "ruff check --fix .",
    "watch": false
  },
  "test": {
    "command": "pytest -q",
    "coverage_command": "pytest --cov=src --cov-report=term-missing",
    "watch": false
  },
  "format": {
    "command": "ruff format .",
    "check_command": "ruff format --check ."
  },
  "commit": {
    "template": "<type>(<scope>): <subject>\n\n<body>\n\n<footer>",
    "types": ["feat", "fix", "docs", "refactor", "test", "chore"],
    "max_subject_length": 72
  }
}
```

If the config file is absent, the commands emit a clear "no config" message
and exit non-zero. The user adds the file once per project; the chain
inherits it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_config(workspace: Path) -> dict:
    config_path = workspace / ".loop" / "dev_config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _run(cmd: str, workspace: Path, *, timeout: int = 300) -> int:
    """Run a shell command in the workspace, return its exit code."""
    print(f"$ {cmd}")
    print(f"  (in {workspace})")
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=workspace, timeout=timeout,
        )
        return result.returncode
    except subprocess.TimeoutExpired:
        print(f"  timeout after {timeout}s")
        return 124
    except (OSError, ValueError) as exc:
        print(f"  error: {exc}")
        return 1


def cmd_lint(workspace: Path, *, fix: bool = False) -> int:
    config = _read_config(workspace).get("lint", {})
    cmd = config.get("fix_command" if fix else "command")
    if not cmd:
        print("No lint config found at <workspace>/.loop/dev_config.json -> 'lint.command'.")
        print("Add a config file with at minimum a 'lint.command' key. Example:")
        print('  {"lint": {"command": "ruff check ."}}')
        return 1
    return _run(cmd, workspace)


def cmd_test(workspace: Path, *, coverage: bool = False) -> int:
    config = _read_config(workspace).get("test", {})
    cmd = config.get("coverage_command" if coverage else "command")
    if not cmd:
        print("No test config found at <workspace>/.loop/dev_config.json -> 'test.command'.")
        print("Add a config file with at minimum a 'test.command' key. Example:")
        print('  {"test": {"command": "pytest -q"}}')
        return 1
    return _run(cmd, workspace, timeout=600)


def cmd_format(workspace: Path, *, check: bool = False) -> int:
    config = _read_config(workspace).get("format", {})
    cmd = config.get("check_command" if check else "command")
    if not cmd:
        print("No format config found at <workspace>/.loop/dev_config.json -> 'format.command'.")
        return 1
    return _run(cmd, workspace)


def cmd_commit(workspace: Path, *, message: str | None = None) -> int:
    """Stage all tracked + untracked changes and commit with a structured
    message. The commit format follows the conventional-commits template
    configured in `<workspace>/.loop/dev_config.json` `commit.template`.
    """
    config = _read_config(workspace).get("commit", {})
    template = config.get("template", "<type>(<scope>): <subject>")
    allowed_types = set(config.get("types", ["feat", "fix", "docs", "refactor", "test", "chore"]))
    max_subject = int(config.get("max_subject_length", 72))

    if not message:
        # No message provided; ask git for the staged diff and prompt the
        # user to author a message. The /commit command is normally
        # invoked with a message: /commit "feat(loop): add /lint".
        print("No commit message provided. Use:")
        print('  /commit "<type>(<scope>): <subject>"')
        print(f"  Allowed types: {', '.join(sorted(allowed_types))}")
        print(f"  Subject max length: {max_subject} chars")
        return 1

    # Validate the commit message against the template and the allowed types.
    first_line = message.splitlines()[0] if message else ""
    m = re.match(r"^(\w+)\(([^)]+)\):\s*(.+)$", first_line)
    if not m:
        print(f"Commit message does not match template:\n  {template}")
        print("Expected: <type>(<scope>): <subject>")
        return 1
    commit_type, _scope, subject = m.groups()
    if commit_type not in allowed_types:
        print(f"Commit type {commit_type!r} not in allowed types: {sorted(allowed_types)}")
        return 1
    if len(subject) > max_subject:
        print(f"Subject is {len(subject)} chars, max is {max_subject}")
        return 1

    # Stage and commit.
    rc = _run("git add -A", workspace)
    if rc != 0:
        return rc
    full_message = message
    return _run(f'git commit -m "{full_message}"', workspace)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    p_lint = sub.add_parser("lint", help="Run the project's linter")
    p_lint.add_argument("--fix", action="store_true", help="Run the fix variant if configured")

    p_test = sub.add_parser("test", help="Run the project's test suite")
    p_test.add_argument("--coverage", action="store_true", help="Run with coverage if configured")

    p_format = sub.add_parser("format", help="Format the project")
    p_format.add_argument("--check", action="store_true", help="Check formatting without writing")

    p_commit = sub.add_parser("commit", help="Stage and commit with a structured message")
    p_commit.add_argument("--message", required=True, help="Commit message")

    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    if args.command == "lint":
        return cmd_lint(workspace, fix=args.fix)
    if args.command == "test":
        return cmd_test(workspace, coverage=args.coverage)
    if args.command == "format":
        return cmd_format(workspace, check=args.check)
    if args.command == "commit":
        return cmd_commit(workspace, message=args.message)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())