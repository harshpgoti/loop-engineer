"""Install and refresh selected external frontend packs without shell strings."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from workspace_tree import product_folder
from workspace_utils import ROOT


COMMAND_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class MaintenanceResult:
    name: str
    ok: bool
    status: str
    detail: str


Runner = Callable[[list[str], Path, int], CommandResult]


def npm_command() -> str:
    return shutil.which("npm.cmd" if os.name == "nt" else "npm") or (
        "npm.cmd" if os.name == "nt" else "npm"
    )


def npx_command() -> str:
    return shutil.which("npx.cmd" if os.name == "nt" else "npx") or (
        "npx.cmd" if os.name == "nt" else "npx"
    )


def default_runner(args: list[str], cwd: Path, timeout: int) -> CommandResult:
    env = os.environ.copy()
    env.update({"CI": "1", "NO_COLOR": "1"})
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(1, "", str(exc))
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _registry_url(label: str) -> str:
    registry = ROOT / "tools" / "registry.md"
    text = registry.read_text(encoding="utf-8")
    match = re.search(rf"\[{re.escape(label)}\]\((https://[^)]+)\)", text)
    if not match:
        raise RuntimeError(f"Missing {label!r} source in tools/registry.md")
    return match.group(1)


def awesome_checkout(workspace: Path) -> Path:
    return (workspace / "external" / "awesome-design-md").resolve()


def _product_root(workspace: Path) -> Path | None:
    return product_folder(workspace)


def _result(name: str, command: CommandResult) -> MaintenanceResult:
    if command.returncode == 0:
        return MaintenanceResult(
            name, True, "installed-or-refreshed", "provider command completed"
        )
    return MaintenanceResult(
        name,
        False,
        "update-failed",
        f"provider command failed with exit code {command.returncode}",
    )


def maintain_pack(
    name: str,
    workspace: Path,
    *,
    runner: Runner = default_runner,
) -> MaintenanceResult:
    """Install or refresh one selected pack. Safe to call before every use."""
    root = _product_root(workspace)
    if root is None:
        return MaintenanceResult(
            name,
            False,
            "no-product-root",
            "global Loop data has no active product directory",
        )
    root = root.resolve()

    if name == "ui-ux-pro-max":
        command = [
            npx_command(),
            "--yes",
            "ui-ux-pro-max-cli@latest",
            "init",
            "--ai",
            "all",
            "--force",
        ]
        return _result(name, runner(command, root, COMMAND_TIMEOUT_SECONDS))

    if name == "taste-skill":
        command = [
            npx_command(),
            "--yes",
            "skills@latest",
            "add",
            "Leonxlnx/taste-skill",
            "--skill",
            "design-taste-frontend",
            "--agent",
            "*",
            "--copy",
            "--yes",
        ]
        return _result(name, runner(command, root, COMMAND_TIMEOUT_SECONDS))

    if name == "awesome-design-md":
        checkout = awesome_checkout(workspace)
        if (checkout / ".git").is_dir():
            command = ["git", "-C", str(checkout), "pull", "--ff-only"]
        else:
            checkout.parent.mkdir(parents=True, exist_ok=True)
            command = [
                "git",
                "clone",
                "--depth",
                "1",
                _registry_url("Awesome DESIGN.md"),
                str(checkout),
            ]
        return _result(name, runner(command, root, COMMAND_TIMEOUT_SECONDS))

    if name == "threeui":
        if not (root / "package.json").is_file():
            return MaintenanceResult(
                name,
                False,
                "not-applicable",
                "ThreeUI requires a JavaScript product with package.json",
            )
        command = [
            npm_command(),
            "install",
            "@designcodeio/threeui@latest",
            "--save-exact",
        ]
        return _result(name, runner(command, root, COMMAND_TIMEOUT_SECONDS))

    return MaintenanceResult(name, False, "unsupported", "no provider adapter")


def maintain_selected(
    names: list[str],
    workspace: Path,
    *,
    runner: Runner = default_runner,
) -> dict[str, MaintenanceResult]:
    """Refresh selected packs once each, preserving router order."""
    results: dict[str, MaintenanceResult] = {}
    for name in names:
        if name not in results:
            results[name] = maintain_pack(name, workspace, runner=runner)
    return results
