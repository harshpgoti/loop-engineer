"""Portable session backend adapters used by the Loop execution plane."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


class LocalSubprocessBackend:
    name = "local-subprocess-v1"

    def create_endpoint(self, run: dict, command: list[str]) -> subprocess.Popen:
        runner = Path(__file__).with_name("local_process_runner.py")
        argv = [os.sys.executable, str(runner), "--run-dir", run["run_dir"], "--command-json", json.dumps(command)]
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        environment = os.environ.copy()
        for marker in ("CLAUDECODE", "CURSOR_AGENT", "CURSOR_INVOKED_AS", "CODEX_HOME", "OPENCODE", "GROK_BUILD"):
            environment.pop(marker, None)
        environment["LOOP_WORKER_RUN_ID"] = run["run_id"]
        environment["LOOP_WORKER_GENERATION"] = str(run["generation"])
        return subprocess.Popen(argv, cwd=run["worktree"], env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, start_new_session=os.name != "nt")

    def send(self, run: dict, message: str) -> Path:
        inbox = Path(run["run_dir"]) / "inbox"
        path = inbox / "backend-doorbell"
        path.write_text(message[:500] + "\n", encoding="utf-8")
        return path

    def capture(self, run: dict) -> dict:
        root = Path(run["run_dir"])
        return {name: (root / name).read_text(encoding="utf-8", errors="replace") if (root / name).exists() else "" for name in ("stdout.log", "stderr.log")}

    def process_state(self, run: dict) -> str:
        return "exited" if (Path(run["run_dir"]) / "exit.json").exists() else "running"

    def destroy(self, run: dict) -> Path:
        path = Path(run["run_dir"]) / "stop.request"
        path.write_text("stop\n", encoding="utf-8")
        return path

