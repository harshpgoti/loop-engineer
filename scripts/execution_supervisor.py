"""Persistent local supervisor lifecycle for durable queued worker dispatch."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from execution_runtime import ExecutionError, ExecutionRuntime

_SUPERVISOR_PROCESSES: dict[str, subprocess.Popen] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True); handle.write("\n")
        Path(raw).replace(path)
    finally:
        Path(raw).unlink(missing_ok=True)


class SupervisorController:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.root = self.workspace / "workers"
        self.state_path = self.root / "supervisor.json"
        self.stop_path = self.root / "supervisor.stop"

    @staticmethod
    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0); return pid > 0
        except OSError:
            return False

    def status(self) -> dict:
        if not self.state_path.exists():
            return {"state": "stopped", "pid": 0}
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if state.get("state") == "running" and not self._alive(int(state.get("pid", 0))):
            state["state"] = "crashed"; state["observed_at"] = _now(); _write(self.state_path, state)
        return state

    def start(self) -> dict:
        start_lock = self.root / "supervisor-start.lock"
        start_lock.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(start_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ExecutionError("local supervisor start is already in progress") from exc
        os.close(fd)
        try:
            current = self.status()
            if current.get("state") == "running":
                raise ExecutionError("local supervisor is already running")
            self.stop_path.unlink(missing_ok=True)
            generation = int(current.get("generation", 0)) + 1
            token = uuid.uuid4().hex
            script = Path(__file__).with_name("supervisor_process.py")
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            process = subprocess.Popen([os.sys.executable, str(script), "--workspace", str(self.workspace), "--generation", str(generation), "--token", token], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, start_new_session=os.name != "nt")
            _SUPERVISOR_PROCESSES[str(self.workspace)] = process
            state = {"schema_version": 1, "state": "running", "pid": process.pid, "generation": generation, "token": token, "started_at": _now(), "workspace": str(self.workspace)}
            _write(self.state_path, state)
            return state
        finally:
            start_lock.unlink(missing_ok=True)

    def stop(self, timeout: float = 10) -> dict:
        state = self.status()
        if state.get("state") not in {"running", "crashed"}:
            return state
        self.stop_path.write_text(f"token={state.get('token', '')}\n", encoding="utf-8")
        process = _SUPERVISOR_PROCESSES.pop(str(self.workspace), None)
        def still_running() -> bool:
            return process.poll() is None if process is not None else self._alive(int(state.get("pid", 0)))
        deadline = time.monotonic() + timeout
        while still_running() and time.monotonic() < deadline:
            time.sleep(0.1)
        if process is not None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=2)
        if still_running():
            raise ExecutionError("local supervisor did not acknowledge stop request")
        state["state"] = "stopped"; state["stopped_at"] = _now(); _write(self.state_path, state)
        return state

    def tick(self) -> dict:
        return ExecutionRuntime(self.workspace).supervisor_tick()
