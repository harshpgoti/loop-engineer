"""Recoverably update the globally installed Loop runtime checkout."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=False)


def update_runtime(root: Path, ref: str = "main") -> tuple[int, list[str]]:
    """Update to origin/ref, preserving dirty files and divergent commits."""
    notes: list[str] = []
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dirty = _git(root, "status", "--porcelain")
    if dirty.returncode != 0:
        return dirty.returncode, [(dirty.stderr or dirty.stdout).strip()]
    if dirty.stdout.strip():
        stash = _git(root, "stash", "push", "--include-untracked", "-m", f"loop-engineer-auto-backup-{stamp}")
        if stash.returncode != 0:
            return stash.returncode, [(stash.stderr or stash.stdout).strip()]
        notes.append("Local runtime edits saved in git stash.")

    fetch = _git(root, "fetch", "origin", ref, "--tags")
    if fetch.returncode != 0:
        return fetch.returncode, notes + [(fetch.stderr or fetch.stdout).strip()]

    ahead = _git(root, "rev-list", "--count", f"origin/{ref}..HEAD")
    if ahead.returncode == 0 and ahead.stdout.strip().isdigit() and int(ahead.stdout.strip()) > 0:
        backup = f"loop-engineer/local-backup-{stamp}"
        branch = _git(root, "branch", backup, "HEAD")
        if branch.returncode != 0:
            return branch.returncode, notes + [(branch.stderr or branch.stdout).strip()]
        notes.append(f"Local runtime commits preserved on branch {backup}.")

    checkout = _git(root, "checkout", "-B", ref, f"origin/{ref}")
    if checkout.returncode != 0:
        return checkout.returncode, notes + [(checkout.stderr or checkout.stdout).strip()]
    notes.append(f"Runtime updated to origin/{ref}.")
    return 0, notes

