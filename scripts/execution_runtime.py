#!/usr/bin/env python3
"""Durable, worktree-isolated execution runs for compiled Loop tasks."""

from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from contextlib import contextmanager
from execution_backends import LocalSubprocessBackend
from execution_schemas import validate_dispatch, validate_event, validate_research, validate_review, validate_worker

EVENTS = {"created", "launched", "working", "waiting_external", "blocked", "checkpoint", "tests_passed", "review_ready", "pr_ready", "report_ready", "failed", "stopped", "torn_down"}
KINDS = {"delivery", "research", "validation"}
DELIVERY_MODES = {"local-only", "direct-pr", "gated-pipeline", "manual"}
ACTIONABLE_EVENTS = {"blocked", "failed", "review_ready", "pr_ready", "report_ready", "waiting_external"}
TERMINAL_STATES = {"failed", "stopped", "torn_down", "report_ready"}
_LOCAL_PROCESSES: dict[str, subprocess.Popen] = {}


class ExecutionError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise ExecutionError((result.stderr or result.stdout).strip())
    return result


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        Path(raw).replace(path)
    finally:
        Path(raw).unlink(missing_ok=True)


def _atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(value)
        Path(raw).replace(path)
    finally:
        Path(raw).unlink(missing_ok=True)


class NativeGitWorktreeProvider:
    """Native Git isolation boundary; never treats the primary checkout as a worker."""

    def allocate(self, repository: Path, worktree: Path, branch: str, base: str) -> None:
        repository = repository.resolve()
        top = Path(_git(repository, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
        if worktree.resolve() == top:
            raise ExecutionError("primary checkout cannot be used as a worker worktree")
        if _git(repository, "status", "--porcelain").stdout.strip():
            raise ExecutionError("primary checkout is dirty; worktree allocation refused")
        _git(repository, "rev-parse", "--verify", f"{base}^{{commit}}")
        worktree.parent.mkdir(parents=True, exist_ok=True)
        _git(repository, "worktree", "add", "-b", branch, str(worktree), base)
        actual = Path(_git(worktree, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
        if actual != worktree.resolve():
            raise ExecutionError("allocated worktree identity does not match its registry path")

    def release(self, repository: Path, worktree: Path, branch: str) -> None:
        _git(repository, "worktree", "remove", str(worktree))
        _git(repository, "branch", "-D", branch)


class ExecutionRuntime:
    """One interface for run creation, observation, execution, validation and cleanup."""

    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        self.root = self.workspace / "workers"
        self.registry_path = self.root / "registry.json"
        self.worktrees = NativeGitWorktreeProvider()
        self.backend = LocalSubprocessBackend()

    def _registry(self) -> dict:
        if not self.registry_path.exists():
            return {"schema_version": 1, "runs": {}}
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("runs"), dict):
            raise ExecutionError("worker registry schema is invalid")
        return data

    def _save(self, registry: dict) -> None:
        _atomic_json(self.registry_path, registry)
        for run in registry.get("runs", {}).values():
            if run.get("run_dir"):
                validate_worker(run)
                _atomic_json(Path(run["run_dir"]) / "meta.json", run)

    def _run(self, run_id: str) -> dict:
        run = self._registry()["runs"].get(run_id)
        if not run:
            raise ExecutionError(f"unknown run: {run_id}")
        return run

    def prepare(self, task_id: str, kind: str, repository: Path, title: str, acceptance: list[str], *, scope: str = "", delivery_mode: str = "manual", executor: str = "unassigned") -> dict:
        if kind not in KINDS:
            raise ExecutionError(f"invalid run kind: {kind}")
        if kind == "validation":
            raise ExecutionError("validation runs must be created from an existing delivery candidate")
        if delivery_mode not in DELIVERY_MODES:
            raise ExecutionError(f"invalid delivery mode: {delivery_mode}")
        repository = repository.resolve()
        _git(repository, "rev-parse", "--show-toplevel")
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        safe_task = re.sub(r"[^a-zA-Z0-9-]+", "-", task_id).strip("-").lower() or "task"
        lease = self.workspace / "locks" / f"task-{safe_task}.lock"
        lease.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise ExecutionError(f"task {task_id} already has an active run") from exc
        os.write(fd, f"run_id={run_id}\ncreated={_now()}\n".encode())
        os.close(fd)
        delivery_lease = self.workspace / "locks" / "delivery.lock" if kind == "delivery" else None
        if delivery_lease:
            try:
                delivery_fd = os.open(delivery_lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                lease.unlink(missing_ok=True)
                raise ExecutionError("workspace already has an active delivery run") from exc
            os.write(delivery_fd, f"run_id={run_id}\ncreated={_now()}\n".encode())
            os.close(delivery_fd)
        registry = self._registry()
        if kind == "delivery" and any(r["kind"] == "delivery" and r.get("state") != "torn_down" for r in registry["runs"].values()):
            lease.unlink(missing_ok=True)
            delivery_lease.unlink(missing_ok=True)
            raise ExecutionError("workspace already has an active delivery run")
        if any(r["task_id"] == task_id and r.get("state") != "torn_down" for r in registry["runs"].values()):
            lease.unlink(missing_ok=True)
            raise ExecutionError(f"task {task_id} already has an active run")
        worktree = self.root / "worktrees" / run_id
        branch = f"loop/{safe_task}-{run_id[-6:]}"
        run_dir = self.root / run_id
        try:
            base = _git(repository, "rev-parse", "HEAD").stdout.strip()
            run_dir.mkdir(parents=True)
            (run_dir / "inbox").mkdir()
            (run_dir / "handled").mkdir()
            run = {"schema_version": 1, "run_id": run_id, "task_id": task_id, "scope": scope, "kind": kind, "executor": executor, "repository": str(repository), "worktree": str(worktree), "branch": branch, "base_commit": base, "generation": 1, "delivery_mode": delivery_mode, "created_at": _now(), "state": "preparing", "run_dir": str(run_dir), "lease": str(lease), "delivery_lease": str(delivery_lease) if delivery_lease else ""}
            registry["runs"][run_id] = run
            self._save(registry)
            self.worktrees.allocate(repository, worktree, branch, base)
            brief = [f"# Execution brief: {task_id}", "", f"Run kind: {kind}", f"Scope: {scope or '-'}", f"Delivery mode: {delivery_mode}", f"Base commit: {base}", "", f"## {title}", "", "## Acceptance criteria", ""]
            brief.extend(f"- {item}" for item in acceptance)
            brief.extend(["", "Work only inside the recorded worktree. Do not merge or approve this run.", ""])
            (run_dir / "brief.md").write_text("\n".join(brief), encoding="utf-8")
            run["state"] = "created"
            registry["runs"][run_id] = run
            self._save(registry)
            self.append_event(run_id, "created", "run prepared", 1)
            return self._run(run_id)
        except Exception:
            if worktree.exists():
                _git(repository, "worktree", "remove", "--force", str(worktree), check=False)
            _git(repository, "branch", "-D", branch, check=False)
            lease.unlink(missing_ok=True)
            if delivery_lease:
                delivery_lease.unlink(missing_ok=True)
            registry = self._registry()
            registry["runs"].pop(run_id, None)
            self._save(registry)
            raise

    def append_event(self, run_id: str, event: str, summary: str, generation: int, *, event_id: str = "") -> dict:
        if event not in EVENTS:
            raise ExecutionError(f"invalid event: {event}")
        registry = self._registry()
        run = registry["runs"].get(run_id)
        if not run:
            raise ExecutionError(f"unknown run: {run_id}")
        if generation != run["generation"]:
            raise ExecutionError("event generation does not match current run generation")
        events_path = Path(run["run_dir"]) / "events.jsonl"
        existing = self.events(run_id)
        if event_id:
            for row in existing:
                if row.get("event_id") == event_id:
                    return row
        sequence = 1
        if existing:
            sequence = max(int(row["sequence"]) for row in existing) + 1
        row = {"schema_version": 1, "run_id": run_id, "generation": generation, "sequence": sequence, "timestamp": _now(), "event": event, "summary": summary[:500], "event_id": event_id or f"{run_id}:{generation}:{sequence}"}
        validate_event(row)
        with events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
        run["state"] = event
        registry["runs"][run_id] = run
        self._save(registry)
        if event in ACTIONABLE_EVENTS:
            self._enqueue_action(row)
        return row

    def _enqueue_action(self, event: dict) -> None:
        path = self.root / "actions.jsonl"
        action_id = event["event_id"]
        if path.exists() and any(json.loads(line).get("action_id") == action_id for line in path.read_text(encoding="utf-8").splitlines() if line.strip()):
            return
        row = {"action_id": action_id, "run_id": event["run_id"], "generation": event["generation"], "event": event["event"], "summary": event["summary"], "created_at": event["timestamp"]}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    def actions(self, *, include_acknowledged: bool = False) -> list[dict]:
        path, ack_path = self.root / "actions.jsonl", self.root / "action-acks.json"
        known = {json.loads(line)["action_id"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()} if path.exists() else set()
        for run in self._registry()["runs"].values():
            for event in self.events(run["run_id"]):
                if event["event"] in ACTIONABLE_EVENTS and event["event_id"] not in known:
                    self._enqueue_action(event)
                    known.add(event["event_id"])
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
        acknowledged = set(json.loads(ack_path.read_text(encoding="utf-8"))) if ack_path.exists() else set()
        return rows if include_acknowledged else [row for row in rows if row["action_id"] not in acknowledged]

    def acknowledge_action(self, action_id: str) -> None:
        if not any(row["action_id"] == action_id for row in self.actions(include_acknowledged=True)):
            raise ExecutionError(f"unknown action: {action_id}")
        path = self.root / "action-acks.json"
        values = set(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else set()
        values.add(action_id)
        _atomic_json(path, sorted(values))

    def fold_state(self, run_id: str) -> dict:
        run = self._run(run_id)
        current = dict(run)
        rows = [row for row in self.events(run_id) if row["generation"] == run["generation"]]
        if rows:
            current["state"] = rows[-1]["event"]
            current["last_event_at"] = rows[-1]["timestamp"]
        current["pending_messages"] = len(list((Path(run["run_dir"]) / "inbox").glob("*.msg")))
        return current

    def send(self, run_id: str, message: str, *, generation: int | None = None) -> Path:
        run = self._run(run_id)
        generation = run["generation"] if generation is None else generation
        if generation != run["generation"]:
            raise ExecutionError("message generation does not match current run generation")
        inbox = Path(run["run_dir"]) / "inbox"
        numbers = [int(path.stem) for path in inbox.glob("*.msg") if path.stem.isdigit()]
        handled = Path(run["run_dir"]) / "handled"
        numbers += [int(path.stem) for path in handled.glob("*.msg") if path.stem.isdigit()]
        path = inbox / f"{(max(numbers, default=0) + 1):06d}.msg"
        path.write_text(json.dumps({"generation": generation, "created_at": _now(), "message": message[:8000]}, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def acknowledge_message(self, run_id: str, name: str, *, generation: int) -> Path:
        run = self._run(run_id)
        if generation != run["generation"]:
            raise ExecutionError("message generation does not match current run generation")
        if not re.fullmatch(r"\d{6}\.msg", name):
            raise ExecutionError("invalid inbox message name")
        source = Path(run["run_dir"]) / "inbox" / name
        if not source.is_file():
            target = Path(run["run_dir"]) / "handled" / name
            if target.is_file():
                return target
            raise ExecutionError(f"unknown inbox message: {name}")
        target = Path(run["run_dir"]) / "handled" / name
        source.replace(target)
        return target

    def heartbeat(self, run_id: str, *, generation: int, summary: str = "alive") -> dict:
        row = self.append_event(run_id, "checkpoint", summary, generation, event_id=f"heartbeat:{run_id}:{generation}:{int(time.time())}")
        registry = self._registry(); registry["runs"][run_id]["heartbeat_at"] = row["timestamp"]; self._save(registry)
        return row

    def semantic_liveness(self, run_id: str, *, wedge_after_seconds: int = 900) -> str:
        run = self.fold_state(run_id)
        if run["state"] in {"blocked", "failed", "stopped", "torn_down", "review_ready", "report_ready", "pr_ready"}:
            return run["state"]
        if not self._pid_alive(int(run.get("pid", 0))):
            return "dead"
        stamp = run.get("heartbeat_at") or run.get("last_event_at") or run["created_at"]
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(stamp)).total_seconds()
        return "wedged" if age > wedge_after_seconds else "working"

    def relaunch(self, run_id: str) -> dict:
        run = self._run(run_id)
        if self._pid_alive(int(run.get("pid", 0))):
            self.stop(run_id)
        launch = run.get("launch_command")
        if not launch:
            raise ExecutionError("run has no durable launch command")
        run_dir = Path(run["run_dir"])
        if hashlib.sha256((run_dir / "brief.md").read_bytes()).hexdigest() != run.get("brief_sha256"):
            raise ExecutionError("execution brief changed after launch; relaunch refused")
        for name in ("stop.request", "exit.json", "child.json"):
            (run_dir / name).unlink(missing_ok=True)
        registry = self._registry()
        current = registry["runs"][run_id]
        current["generation"] = int(current["generation"]) + 1
        current["state"] = "launching"
        registry["runs"][run_id] = current
        self._save(registry)
        process = self.backend.create_endpoint(current, launch)
        registry = self._registry(); current = registry["runs"][run_id]; current.update({"pid": process.pid, "state": "launched", "launched_at": _now()}); registry["runs"][run_id] = current; self._save(registry)
        _LOCAL_PROCESSES[run_id] = process
        self.append_event(run_id, "launched", f"generation {current['generation']} relaunched", current["generation"])
        return self._run(run_id)

    def status(self, run_id: str) -> dict:
        return self._run(run_id)

    def list_runs(self) -> dict:
        return self._registry()

    def _dispatch_queue(self) -> dict:
        path = self.root / "dispatch.json"
        if not path.exists():
            return {"schema_version": 1, "requests": []}
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema_version") != 1 or not isinstance(value.get("requests"), list):
            raise ExecutionError("dispatch queue schema is invalid")
        return value

    @contextmanager
    def _dispatch_guard(self, timeout: float = 5):
        path = self.root / "dispatch.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout
        while True:
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"pid={os.getpid()}\ncreated={_now()}\n".encode()); os.close(fd)
                break
            except FileExistsError as exc:
                if time.monotonic() >= deadline:
                    raise ExecutionError("dispatch queue is busy; retry safely") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            path.unlink(missing_ok=True)

    def enqueue_dispatch(self, task_id: str, repository: Path, command: list[str], *, kind: str = "delivery", title: str = "", acceptance: list[str] | None = None, scope: str = "", delivery_mode: str = "local-only", executor: str = "unassigned", priority: int = 100, depends_on: list[str] | None = None) -> dict:
        if kind not in {"delivery", "research"} or not command:
            raise ExecutionError("dispatch requires a delivery/research kind and command argv")
        with self._dispatch_guard():
            queue = self._dispatch_queue()
            if any(row["task_id"] == task_id and row["state"] in {"queued", "dispatched"} for row in queue["requests"]):
                raise ExecutionError(f"task {task_id} is already queued or dispatched")
            if any(row["task_id"] == task_id and row.get("state") not in TERMINAL_STATES for row in self._registry()["runs"].values()):
                raise ExecutionError(f"task {task_id} already has an active run")
            request = {"request_id": f"dispatch-{uuid.uuid4().hex[:12]}", "task_id": task_id, "repository": str(repository.resolve()), "command": command, "kind": kind, "title": title or task_id, "acceptance": acceptance or [], "scope": scope, "delivery_mode": delivery_mode, "executor": executor, "priority": int(priority), "depends_on": depends_on or [], "state": "queued", "created_at": _now(), "attempts": 0}
            validate_dispatch(request)
            queue["requests"].append(request)
            _atomic_json(self.root / "dispatch.json", queue)
            return request

    def dispatch_queue(self) -> list[dict]:
        return self._dispatch_queue()["requests"]

    def _reconcile_dispatch_queue_unlocked(self) -> list[str]:
        queue, runs = self._dispatch_queue(), self._registry()["runs"]
        findings: list[str] = []
        for request in queue["requests"]:
            if request["state"] != "queued":
                continue
            matches = [run for run in runs.values() if run["task_id"] == request["task_id"] and run.get("state") not in TERMINAL_STATES]
            if len(matches) == 1:
                request.update({"state": "dispatched", "run_id": matches[0]["run_id"], "reconciled_at": _now()})
                findings.append(f"{request['request_id']}: recovered dispatch {matches[0]['run_id']}")
            elif len(matches) > 1:
                raise ExecutionError(f"ambiguous active runs for queued task {request['task_id']}")
        if findings:
            _atomic_json(self.root / "dispatch.json", queue)
        return findings

    def reconcile_dispatch_queue(self) -> list[str]:
        with self._dispatch_guard():
            return self._reconcile_dispatch_queue_unlocked()

    def _quota_policy(self) -> dict:
        path = self.root / "policy.json"
        defaults = {"schema_version": 1, "max_active": 3, "max_delivery": 1, "max_research": 2, "wedge_after_seconds": 900, "poll_seconds": 2}
        if not path.exists():
            return defaults
        value = json.loads(path.read_text(encoding="utf-8"))
        for key in ("max_active", "max_delivery", "max_research"):
            if int(value.get(key, 0)) < 1:
                raise ExecutionError(f"supervisor policy {key} must be positive")
        return {**defaults, **value}

    def dispatch_once(self) -> list[dict]:
        self.reconcile()
        with self._dispatch_guard():
            self._reconcile_dispatch_queue_unlocked()
            return self._dispatch_once_unlocked()

    def _dispatch_once_unlocked(self) -> list[dict]:
        queue, policy = self._dispatch_queue(), self._quota_policy()
        runs = self._registry()["runs"]
        active = [row for row in runs.values() if row["kind"] in {"delivery", "research"} and row.get("state") not in TERMINAL_STATES]
        active_by_kind = {kind: sum(1 for row in active if row["kind"] == kind) for kind in ("delivery", "research")}
        satisfied = {row["task_id"] for row in runs.values() if row.get("state") in {"torn_down", "report_ready"}}
        dispatched: list[dict] = []
        for request in sorted(queue["requests"], key=lambda row: (int(row["priority"]), row["created_at"], row["request_id"])):
            if request["state"] != "queued" or not set(request["depends_on"]).issubset(satisfied):
                continue
            if len(active) >= int(policy["max_active"]) or active_by_kind[request["kind"]] >= int(policy[f"max_{request['kind']}"]):
                continue
            request["attempts"] += 1
            try:
                run = self.spawn(request["task_id"], request["kind"], Path(request["repository"]), request["title"], request["acceptance"], request["command"], scope=request["scope"], delivery_mode=request["delivery_mode"], executor=request["executor"])
            except ExecutionError as exc:
                request["last_error"] = str(exc)[:500]
                request["last_attempt_at"] = _now()
                continue
            request.update({"state": "dispatched", "run_id": run["run_id"], "dispatched_at": _now()})
            dispatched.append(run)
            active.append(run); active_by_kind[run["kind"]] += 1
        _atomic_json(self.root / "dispatch.json", queue)
        return dispatched

    def supervisor_tick(self) -> dict:
        findings = self.reconcile()
        policy = self._quota_policy()
        wedged: list[str] = []
        for run in self._registry()["runs"].values():
            if run["kind"] in {"delivery", "research"} and run.get("state") not in TERMINAL_STATES and self.semantic_liveness(run["run_id"], wedge_after_seconds=int(policy["wedge_after_seconds"])) == "wedged":
                self.append_event(run["run_id"], "blocked", "worker heartbeat exceeded wedge threshold", run["generation"], event_id=f"wedged:{run['run_id']}:{run['generation']}")
                wedged.append(run["run_id"])
        return {"findings": findings, "wedged": wedged, "dispatched": [run["run_id"] for run in self.dispatch_once()], "actions": len(self.actions())}

    def events(self, run_id: str) -> list[dict]:
        run = self._run(run_id)
        path = Path(run["run_dir"]) / "events.jsonl"
        if not path.exists():
            return []
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows: list[dict] = []
        for index, line in enumerate(lines):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                if index != len(lines) - 1:
                    raise ExecutionError("event log is corrupt before its final row") from exc
                (path.with_suffix(".corrupt-tail")).write_text(line + "\n", encoding="utf-8")
        return rows

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def reconcile(self) -> list[str]:
        registry = self._registry()
        findings: list[str] = []
        for run_id, run in list(registry["runs"].items()):
            state = run.get("state")
            if state in {"preparing", "launching"}:
                run["state"] = "blocked"
                registry["runs"][run_id] = run
                findings.append(f"{run_id}: interrupted {state} preserved for inspection")
            elif state in {"launched", "working"} and not self._pid_alive(int(run.get("pid", 0))):
                run["state"] = "stopped"
                registry["runs"][run_id] = run
                findings.append(f"{run_id}: recorded process is no longer running")
        if findings:
            self._save(registry)
            for finding in findings:
                run_id = finding.split(":", 1)[0]
                run = self._run(run_id)
                self.append_event(run_id, run["state"], finding, run["generation"])
        return findings

    def spawn(self, task_id: str, kind: str, repository: Path, title: str, acceptance: list[str], command: list[str], *, scope: str = "", delivery_mode: str = "manual", executor: str = "unassigned", brief_sections: list[tuple[str, str]] | None = None) -> dict:
        if not command:
            raise ExecutionError("launch command is required")
        run = self.prepare(task_id, kind, repository, title, acceptance, scope=scope, delivery_mode=delivery_mode, executor=executor)
        brief = Path(run["run_dir"]) / "brief.md"
        if brief_sections:
            with brief.open("a", encoding="utf-8") as handle:
                for heading, body in brief_sections:
                    if body.strip():
                        handle.write(f"\n## {heading}\n\n{body.strip()}\n")
        brief_hash = hashlib.sha256(brief.read_bytes()).hexdigest()
        pointer = f"Read the execution brief at {brief.resolve()} and follow it exactly."
        launch = [part.replace("{brief}", str(brief.resolve())).replace("{pointer}", pointer) for part in command]
        if not any("{brief}" in part or "{pointer}" in part for part in command):
            launch.append(pointer)
        registry = self._registry()
        current = registry["runs"][run["run_id"]]
        current["state"] = "launching"
        current["launch_command"] = launch
        current["brief_sha256"] = brief_hash
        registry["runs"][run["run_id"]] = current
        self._save(registry)
        try:
            process = self.backend.create_endpoint(run, launch)
        except Exception:
            registry = self._registry(); registry["runs"][run["run_id"]]["state"] = "blocked"; self._save(registry)
            raise
        registry = self._registry()
        current = registry["runs"][run["run_id"]]
        current.update({"pid": process.pid, "state": "launched", "launched_at": _now(), "backend": self.backend.name})
        registry["runs"][run["run_id"]] = current
        self._save(registry)
        self.append_event(run["run_id"], "launched", f"local process {process.pid} launched", run["generation"])
        _LOCAL_PROCESSES[run["run_id"]] = process
        return self._run(run["run_id"])

    def stop(self, run_id: str) -> dict:
        run = self._run(run_id)
        pid = int(run.get("pid", 0))
        process = _LOCAL_PROCESSES.pop(run_id, None)
        run_dir = Path(run["run_dir"])
        (run_dir / "stop.request").write_text(_now() + "\n", encoding="utf-8")
        deadline = time.monotonic() + 10
        while not (run_dir / "exit.json").exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        if process is not None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if not (run_dir / "exit.json").exists() and self._pid_alive(pid):
            raise ExecutionError(f"process {pid} did not acknowledge the durable stop request")
        self.append_event(run_id, "stopped", f"local process {pid} stopped", run["generation"], event_id=f"stopped:{run_id}:{run['generation']}")
        return self._run(run_id)

    def verify_validation(self, run_id: str) -> dict:
        run = self._run(run_id)
        path = Path(run["run_dir"]) / "review.json"
        if not path.exists():
            raise ExecutionError("validation record is missing")
        review = json.loads(path.read_text(encoding="utf-8"))
        head = _git(Path(run["worktree"]), "rev-parse", "HEAD").stdout.strip()
        if review["head_commit"] != head:
            raise ExecutionError("validation is stale for the current head")
        if review.get("base_commit") and review["base_commit"] != run["base_commit"]:
            raise ExecutionError("validation is stale for the current base")
        if review["verdict"] != "pass":
            raise ExecutionError("validation did not pass")
        return review

    def start_validation(self, delivery_run_id: str, validator: str) -> dict:
        delivery = self._run(delivery_run_id)
        if delivery["kind"] != "delivery":
            raise ExecutionError("validation candidate must be a delivery run")
        if validator == delivery.get("executor"):
            raise ExecutionError("a delivery run cannot validate itself")
        head = _git(Path(delivery["worktree"]), "rev-parse", "HEAD").stdout.strip()
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        run_dir = self.root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "inbox").mkdir(); (run_dir / "handled").mkdir()
        run = {"schema_version": 1, "run_id": run_id, "task_id": delivery["task_id"], "scope": delivery.get("scope", ""), "kind": "validation", "executor": validator, "repository": delivery["repository"], "worktree": "", "candidate_run_id": delivery_run_id, "base_commit": delivery["base_commit"], "head_commit": head, "generation": 1, "delivery_mode": delivery["delivery_mode"], "created_at": _now(), "state": "created", "run_dir": str(run_dir), "readonly": True}
        registry = self._registry(); registry["runs"][run_id] = run; self._save(registry)
        diff = _git(Path(delivery["worktree"]), "diff", "--binary", f"{delivery['base_commit']}..{head}").stdout
        (run_dir / "candidate.diff").write_text(diff, encoding="utf-8")
        (run_dir / "brief.md").write_text(f"# Validation brief\n\nCandidate: {delivery_run_id}\nBase: {delivery['base_commit']}\nHead: {head}\nArtifact: {run_dir / 'candidate.diff'}\n\nRead-only review of the detached artifact. Report Spec and Standards separately.\n", encoding="utf-8")
        self.append_event(run_id, "created", "read-only validation run prepared", 1)
        return self._run(run_id)

    def submit_validation(self, validation_run_id: str, verdict: str, spec: str, standards: str) -> dict:
        validation = self._run(validation_run_id)
        if validation["kind"] != "validation" or verdict not in {"pass", "fail"}:
            raise ExecutionError("invalid validation submission")
        candidate = self._run(validation["candidate_run_id"])
        head = _git(Path(candidate["worktree"]), "rev-parse", "HEAD").stdout.strip()
        if head != validation["head_commit"] or candidate["base_commit"] != validation["base_commit"]:
            raise ExecutionError("validation is stale for the current base/head")
        review = {"schema_version": 1, "validation_run_id": validation_run_id, "run_id": candidate["run_id"], "validator": validation["executor"], "base_commit": validation["base_commit"], "head_commit": head, "verdict": verdict, "spec": spec[:8000], "standards": standards[:8000], "recorded_at": _now()}
        validate_review(review)
        _atomic_json(Path(validation["run_dir"]) / "review.json", review)
        _atomic_json(Path(candidate["run_dir"]) / "review.json", review)
        self.append_event(validation_run_id, "review_ready", f"validation verdict: {verdict}", validation["generation"])
        return review

    def record_research(self, run_id: str, report: str, citations: list[str], decisions: list[str]) -> dict:
        run = self._run(run_id)
        if run["kind"] != "research" or not report.strip() or not citations:
            raise ExecutionError("research requires a non-empty report and at least one citation")
        payload = {"schema_version": 1, "run_id": run_id, "report": report.strip(), "citations": citations, "decision_inventory": decisions, "recorded_at": _now()}
        validate_research(payload)
        run_dir = Path(run["run_dir"])
        _atomic_json(run_dir / "report.json", payload)
        lines = ["# Research report", "", report.strip(), "", "## Citations", "", *[f"- {value}" for value in citations], "", "## Decision inventory", "", *[f"- {value}" for value in decisions], ""]
        (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
        self.append_event(run_id, "report_ready", "cited research report ready", run["generation"])
        return payload

    def reconcile_research(self, run_id: str, evidence_log: Path) -> dict:
        run = self._run(run_id)
        path = Path(run["run_dir"]) / "report.json"
        if run["kind"] != "research" or not path.is_file():
            raise ExecutionError("research report is missing")
        payload = json.loads(path.read_text(encoding="utf-8"))
        marker = f"loop-worker:{run_id}"
        existing = evidence_log.read_text(encoding="utf-8") if evidence_log.exists() else "# Evidence Log\n"
        if marker not in existing:
            block = ["", f"## Research run {run_id}", "", f"- Marker: `{marker}`", f"- Date checked: {datetime.now(timezone.utc).date().isoformat()}", f"- Finding: {payload['report']}", "- Sources:", *[f"  - {source}" for source in payload["citations"]], "- Decisions requiring authority:", *[f"  - {decision}" for decision in payload["decision_inventory"]], ""]
            evidence_log.parent.mkdir(parents=True, exist_ok=True)
            _atomic_text(evidence_log, existing.rstrip() + "\n" + "\n".join(block))
        return {"run_id": run_id, "evidence_log": str(evidence_log), "marker": marker}

    def _record_delivery_evidence(self, run_id: str, *, source: str, head: str, pr_state: str = "", pipeline_state: str = "", url: str = "") -> dict:
        run = self._run(run_id)
        current = _git(Path(run["worktree"]), "rev-parse", "HEAD").stdout.strip()
        if head != current:
            raise ExecutionError("delivery evidence head does not match the current worker head")
        evidence = {"schema_version": 1, "run_id": run_id, "source": source, "head_commit": head, "pr_state": pr_state, "pipeline_state": pipeline_state, "url": url, "verified_at": _now()}
        _atomic_json(Path(run["run_dir"]) / "delivery-evidence.json", evidence)
        return evidence

    def refresh_github_evidence(self, run_id: str, pr: str, *, gh: str | list[str] = "gh") -> dict:
        run = self._run(run_id)
        prefix = [gh] if isinstance(gh, str) else gh
        result = subprocess.run([*prefix, "pr", "view", pr, "--json", "headRefOid,state,url,statusCheckRollup"], cwd=run["repository"], text=True, capture_output=True, check=False)
        if result.returncode:
            raise ExecutionError(f"GitHub PR verification failed: {(result.stderr or result.stdout).strip()}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ExecutionError("GitHub PR verification returned invalid JSON") from exc
        checks = payload.get("statusCheckRollup") or []
        conclusions = [str(check.get("conclusion") or check.get("state") or "").upper() for check in checks]
        pipeline = "passed" if checks and all(value in {"SUCCESS", "NEUTRAL", "SKIPPED"} for value in conclusions) else "pending"
        return self._record_delivery_evidence(run_id, source="github-cli", head=str(payload.get("headRefOid", "")), pr_state=str(payload.get("state", "")).lower(), pipeline_state=pipeline, url=str(payload.get("url", "")))

    def merge_github(self, run_id: str, pr: str, *, approval: str, gh: str | list[str] = "gh") -> str:
        run = self._run(run_id)
        if run["delivery_mode"] not in {"direct-pr", "gated-pipeline"}:
            raise ExecutionError("GitHub merge requires direct-pr or gated-pipeline delivery mode")
        if approval != f"approve:{run_id}":
            raise ExecutionError(f"explicit approval token approve:{run_id} is required")
        self.refresh_github_evidence(run_id, pr, gh=gh)
        ready = self.verify_merge_ready(run_id)
        prefix = [gh] if isinstance(gh, str) else gh
        result = subprocess.run([*prefix, "pr", "merge", pr, "--merge", "--match-head-commit", ready["head"]], cwd=run["repository"], text=True, capture_output=True, check=False)
        if result.returncode:
            raise ExecutionError(f"GitHub merge failed: {(result.stderr or result.stdout).strip()}")
        registry = self._registry(); registry["runs"][run_id]["landed_target"] = f"github-pr:{pr}"; registry["runs"][run_id]["landed_head"] = ready["head"]; self._save(registry)
        return ready["head"]

    def verify_merge_ready(self, run_id: str) -> dict:
        run = self._run(run_id)
        if run["kind"] != "delivery":
            raise ExecutionError("only delivery runs become merge-ready")
        review = self.verify_validation(run_id)
        head = _git(Path(run["worktree"]), "rev-parse", "HEAD").stdout.strip()
        mode = run["delivery_mode"]
        evidence_path = Path(run["run_dir"]) / "delivery-evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8")) if evidence_path.exists() else {}
        if mode == "gated-pipeline" and not (evidence.get("head_commit") == head and evidence.get("pipeline_state") == "passed"):
            raise ExecutionError("gated-pipeline delivery requires passing pipeline evidence")
        if mode == "direct-pr" and not (evidence.get("head_commit") == head and evidence.get("pr_state") == "open"):
            raise ExecutionError("remote PR head does not match the current worker head")
        if mode == "manual":
            raise ExecutionError("manual delivery mode must be resolved before merge-ready")
        registry = self._registry(); registry["runs"][run_id]["merge_ready_head"] = head; registry["runs"][run_id]["merge_ready_at"] = _now(); self._save(registry)
        self.append_event(run_id, "pr_ready" if mode != "local-only" else "review_ready", f"{mode} delivery verified at {head[:12]}", run["generation"], event_id=f"merge-ready:{run_id}:{run['generation']}:{head}")
        return {"run_id": run_id, "head": head, "mode": mode, "review": review}

    def merge_local(self, run_id: str, target: str, *, approval: str) -> str:
        run = self._run(run_id)
        if run["delivery_mode"] != "local-only":
            raise ExecutionError("local merge applies only to local-only delivery mode")
        if approval != f"approve:{run_id}":
            raise ExecutionError(f"explicit approval token approve:{run_id} is required")
        ready = self.verify_merge_ready(run_id)
        repository = Path(run["repository"])
        if _git(repository, "status", "--porcelain").stdout.strip():
            raise ExecutionError("target checkout is dirty; merge refused")
        _git(repository, "checkout", target)
        _git(repository, "merge", "--ff-only", ready["head"])
        registry = self._registry(); registry["runs"][run_id]["landed_target"] = target; registry["runs"][run_id]["landed_head"] = ready["head"]; self._save(registry)
        return ready["head"]

    def reconcile_product_truth(self, run_id: str, tasks_path: Path, gates_path: Path) -> Path:
        run = self._run(run_id)
        if run["kind"] != "delivery" or not run.get("landed_head"):
            raise ExecutionError("only landed delivery work can reconcile product truth")
        journal = Path(run["run_dir"]) / "reconcile.json"
        if journal.exists() and json.loads(journal.read_text(encoding="utf-8")).get("state") == "applied":
            return journal
        task_text = tasks_path.read_text(encoding="utf-8")
        pattern = re.compile(rf"(^\s*-\s+id:\s*{re.escape(run['task_id'])}\s*$.*?^\s+status:\s*)\S+", re.MULTILINE | re.DOTALL)
        updated, count = pattern.subn(r"\g<1>completed", task_text, count=1)
        if count != 1:
            raise ExecutionError("task status could not be reconciled deterministically")
        intent = {"schema_version": 1, "run_id": run_id, "task_id": run["task_id"], "head": run["landed_head"], "state": "intent", "created_at": _now()}
        _atomic_json(journal, intent)
        gate_match = re.search(rf"^\s*-\s+id:\s*{re.escape(run['task_id'])}\s*$.*?^\s+gate:\s*(\S+)", task_text, re.MULTILINE | re.DOTALL)
        gate_id = gate_match.group(1).strip("\"'") if gate_match else ""
        gate_text = gates_path.read_text(encoding="utf-8") if gates_path.exists() else ""
        gate_updated = gate_text
        if gate_id:
            gate_pattern = re.compile(rf"(^\s*{re.escape(gate_id)}:\s*$.*?^\s+status:\s*)\S+", re.MULTILINE | re.DOTALL)
            gate_updated, gate_count = gate_pattern.subn(r"\g<1>passed", gate_text, count=1)
            if gate_count != 1:
                raise ExecutionError("gate status could not be reconciled deterministically")
        _atomic_text(tasks_path, updated)
        if gate_id:
            _atomic_text(gates_path, gate_updated)
        intent["state"] = "applied"; intent["applied_at"] = _now(); _atomic_json(journal, intent)
        return journal

    def cleanup(self, run_id: str) -> None:
        run = self._run(run_id)
        if run["kind"] == "validation":
            self.append_event(run_id, "torn_down", "validation evidence retained", run["generation"])
            return
        repository, worktree = Path(run["repository"]), Path(run["worktree"])
        if self._pid_alive(int(run.get("pid", 0))):
            raise ExecutionError("run process is still active; stop it before teardown")
        if _git(worktree, "status", "--porcelain").stdout.strip():
            raise ExecutionError("worktree is dirty; cleanup refused")
        if run["kind"] == "delivery":
            head = _git(worktree, "rev-parse", "HEAD").stdout.strip()
            landed = _git(repository, "merge-base", "--is-ancestor", head, "HEAD", check=False)
            remote_landed = run.get("landed_head") == head and str(run.get("landed_target", "")).startswith("github-pr:")
            if landed.returncode != 0 and not remote_landed:
                raise ExecutionError("delivery commits are not landed; cleanup refused")
        elif run["kind"] == "research" and not (Path(run["run_dir"]) / "report.md").is_file():
            raise ExecutionError("research report is missing; cleanup refused")
        self.worktrees.release(repository, worktree, run["branch"])
        if run.get("lease"):
            Path(run["lease"]).unlink(missing_ok=True)
        if run.get("delivery_lease"):
            Path(run["delivery_lease"]).unlink(missing_ok=True)
        self.append_event(run_id, "torn_down", "worktree released", run["generation"])
