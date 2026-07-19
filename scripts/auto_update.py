#!/usr/bin/env python3
"""Silent, throttled auto-update of the installed app, run at session-start.

gstack's best idea: because the runtime lives in one place, a fast check at the
start of every session keeps every agent current with zero manual upgrades. Loop
has one app (not one clone per tool), so there is even less to keep consistent.

Behavior (all failure-safe - any error skips silently and retries next hour):
  - Mode from `LOOP_AUTO_UPDATE` env, else `<data>/auto_update.txt`, else `pull`:
      off   - never touch the app
      check - fetch and, if behind, leave a one-line notice; never modify files
      pull  - fetch and fast-forward when the app checkout is clean; else notice
  - Throttled to once per hour via `<data>/.last-update-check`.
  - Only acts on a git checkout with an upstream.
  - On a successful fast-forward, routers are refreshed (commands may have
    changed) via `install_skills.py --user`.

Stdlib only.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

THROTTLE_SECONDS = 3600
_MODES = ("off", "check", "pull")


def auto_update_mode(data_home: Path) -> str:
    env = os.environ.get("LOOP_AUTO_UPDATE", "").strip().lower()
    if env in _MODES:
        return env
    marker = data_home / "auto_update.txt"
    if marker.exists():
        try:
            val = marker.read_text(encoding="utf-8").strip().lower()
            if val in _MODES:
                return val
        except OSError:
            pass
    return "pull"


def _throttled(marker: Path) -> bool:
    try:
        last = float(marker.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return (time.time() - last) < THROTTLE_SECONDS


def _touch(marker: Path) -> None:
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(str(time.time()), encoding="utf-8")
    except OSError:
        pass


def _git(app_root: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(app_root), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _refresh_routers(app_root: Path) -> None:
    script = app_root / "scripts" / "install_skills.py"
    if not script.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(script), "--user"],
            cwd=str(app_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def maybe_auto_update(app_root: Path, data_home: Path, *, force: bool = False) -> dict:
    """Returns a small status dict. Never raises."""
    mode = auto_update_mode(data_home)
    result: dict = {"mode": mode, "ran": False}
    if mode == "off":
        return result
    if not (app_root / ".git").exists():
        result["skip"] = "not a git checkout"
        return result

    marker = data_home / ".last-update-check"
    if not force and _throttled(marker):
        result["skip"] = "throttled"
        return result
    _touch(marker)

    try:
        if _git(app_root, "fetch", "--quiet").returncode != 0:
            result["skip"] = "fetch failed"
            return result
        counts = _git(app_root, "rev-list", "--count", "--left-right", "HEAD...@{upstream}")
        if counts.returncode != 0:
            result["skip"] = "no upstream"
            return result
        parts = (counts.stdout.strip().split() + ["0", "0"])[:2]
        behind = int(parts[1]) if parts[1].isdigit() else 0
        result["behind"] = behind
        if behind == 0:
            result["ran"] = True
            return result
        if mode == "check":
            result["notice"] = f"{behind} app update(s) available - run `loop update`"
            return result
        # pull: fast-forward only when the checkout is clean
        if _git(app_root, "status", "--porcelain").stdout.strip():
            result["notice"] = f"{behind} update(s) available; app has local changes - run `loop update`"
            return result
        if _git(app_root, "merge", "--ff-only", "--quiet", "@{upstream}").returncode != 0:
            result["notice"] = "app update needs a manual merge - run `loop update`"
            return result
        result["ran"] = True
        result["updated"] = behind
        _refresh_routers(app_root)
        return result
    except (subprocess.TimeoutExpired, OSError) as exc:
        result["skip"] = f"error: {exc.__class__.__name__}"
        return result


def resolve_app_root() -> Path:
    """The git checkout to update: installed app if present, else this checkout."""
    try:
        from loop_home import app_path

        candidate = app_path()
        if (candidate / ".git").exists():
            return candidate
    except Exception:
        pass
    return Path(__file__).resolve().parents[1]


def main() -> int:
    from loop_home import global_data_home

    force = "--force" in sys.argv
    result = maybe_auto_update(resolve_app_root(), global_data_home(), force=force)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
