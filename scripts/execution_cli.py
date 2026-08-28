#!/usr/bin/env python3
"""Internal CLI for one durable, isolated local execution worker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from execution_runtime import ExecutionError, ExecutionRuntime
from task_context import dependencies, gate_block, parse_tasks_file
from workspace_utils import console_utf8, resolve_workspace
from harness_adapters import write_compatibility_matrix
from execution_supervisor import SupervisorController


def _tasks_path(workspace: Path, scope: str) -> Path:
    return workspace / "plan" / "products" / scope / "TASKS.yml" if scope else workspace / "TASKS.yml"


def _task(workspace: Path, task_id: str, scope: str) -> tuple[dict, list[dict]]:
    path = _tasks_path(workspace, scope)
    tasks = parse_tasks_file(path)
    for task in tasks:
        if task["id"] == task_id:
            return task, tasks
    raise ExecutionError(f"task not found: {task_id} in {path}")


def _read_bounded(path: Path, limit: int = 24000) -> str:
    if not path.is_file():
        return ""
    value = path.read_text(encoding="utf-8", errors="replace")
    return value if len(value) <= limit else value[:limit].rstrip() + "\n\n[Context truncated by deterministic brief compiler.]"


def _brief_sections(workspace: Path, task: dict, tasks: list[dict], scope: str) -> list[tuple[str, str]]:
    scope_root = workspace / "plan" / "products" / scope if scope else workspace
    task_yaml = "\n".join(task.get("raw", [])).rstrip()
    dependency_rows = dependencies(tasks, task)
    dependency_text = "\n\n".join("\n".join(row.get("raw", [])) for row in dependency_rows)
    gate = gate_block(scope_root, str(task.get("gate", "")))
    sections = [("Canonical task record", f"```yaml\n{task_yaml}\n```")]
    if dependency_text:
        sections.append(("Dependencies", f"```yaml\n{dependency_text}\n```"))
    if gate:
        sections.append(("Required gate", f"```yaml\n{gate}\n```"))
    for heading, name in (("Relevant decisions", "DECISIONS.md"), ("Product requirements", "prd.md"), ("Architecture context", "architecture.md")):
        path = scope_root / name
        if not path.is_file() and not scope:
            path = workspace / "plan" / name
        content = _read_bounded(path)
        if content:
            sections.append((heading, content))
    return sections


def main() -> int:
    console_utf8()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    spawn = sub.add_parser("spawn", help="Compile a brief, allocate a worktree, and launch one process.")
    spawn.add_argument("task_id")
    spawn.add_argument("--kind", choices=("delivery", "research"), default="delivery")
    spawn.add_argument("--repository", required=True)
    spawn.add_argument("--scope", default="")
    spawn.add_argument("--delivery-mode", default="manual")
    spawn.add_argument("--executor", default="unassigned")
    spawn.add_argument("--command-json", required=True, help="JSON array containing the exact process argv.")
    status = sub.add_parser("status", help="Reconcile and show one run or the registry.")
    status.add_argument("run_id", nargs="?")
    events = sub.add_parser("events", help="Read one run's durable event stream.")
    events.add_argument("run_id")
    stop = sub.add_parser("stop", help="Stop a run without removing its evidence or worktree.")
    stop.add_argument("run_id")
    teardown = sub.add_parser("teardown", help="Release a safely stopped and landed run.")
    teardown.add_argument("run_id")
    send = sub.add_parser("send"); send.add_argument("run_id"); send.add_argument("message"); send.add_argument("--generation", type=int)
    ack = sub.add_parser("ack"); ack.add_argument("run_id"); ack.add_argument("name"); ack.add_argument("--generation", type=int, required=True)
    sub.add_parser("actions")
    ack_action = sub.add_parser("ack-action"); ack_action.add_argument("action_id")
    heartbeat = sub.add_parser("heartbeat"); heartbeat.add_argument("run_id"); heartbeat.add_argument("--generation", type=int, required=True); heartbeat.add_argument("--summary", default="alive")
    liveness = sub.add_parser("liveness"); liveness.add_argument("run_id"); liveness.add_argument("--wedge-after", type=int, default=900)
    relaunch = sub.add_parser("relaunch"); relaunch.add_argument("run_id")
    validation_start = sub.add_parser("validation-start"); validation_start.add_argument("run_id"); validation_start.add_argument("--validator", required=True)
    validation_submit = sub.add_parser("validation-submit"); validation_submit.add_argument("run_id"); validation_submit.add_argument("--verdict", choices=("pass", "fail"), required=True); validation_submit.add_argument("--spec", required=True); validation_submit.add_argument("--standards", required=True)
    research_record = sub.add_parser("research-record"); research_record.add_argument("run_id"); research_record.add_argument("--report", required=True); research_record.add_argument("--citations-json", required=True); research_record.add_argument("--decisions-json", default="[]")
    research_reconcile = sub.add_parser("research-reconcile"); research_reconcile.add_argument("run_id"); research_reconcile.add_argument("--evidence-log", required=True)
    github_evidence = sub.add_parser("github-evidence"); github_evidence.add_argument("run_id"); github_evidence.add_argument("--pr", required=True)
    merge_ready = sub.add_parser("merge-ready"); merge_ready.add_argument("run_id")
    merge_local = sub.add_parser("merge-local"); merge_local.add_argument("run_id"); merge_local.add_argument("--target", required=True); merge_local.add_argument("--approval", required=True)
    merge_github = sub.add_parser("merge-github"); merge_github.add_argument("run_id"); merge_github.add_argument("--pr", required=True); merge_github.add_argument("--approval", required=True)
    reconcile = sub.add_parser("reconcile-product"); reconcile.add_argument("run_id"); reconcile.add_argument("--tasks", required=True); reconcile.add_argument("--gates", required=True)
    compatibility = sub.add_parser("compatibility"); compatibility.add_argument("--output", required=True)
    enqueue = sub.add_parser("enqueue"); enqueue.add_argument("task_id"); enqueue.add_argument("--repository", required=True); enqueue.add_argument("--command-json", required=True); enqueue.add_argument("--kind", choices=("delivery", "research"), default="delivery"); enqueue.add_argument("--title", default=""); enqueue.add_argument("--acceptance-json", default="[]"); enqueue.add_argument("--scope", default=""); enqueue.add_argument("--delivery-mode", default="local-only"); enqueue.add_argument("--executor", default="unassigned"); enqueue.add_argument("--priority", type=int, default=100); enqueue.add_argument("--depends-on-json", default="[]")
    sub.add_parser("queue")
    sub.add_parser("dispatch")
    for name in ("supervisor-start", "supervisor-status", "supervisor-stop", "supervisor-tick"):
        sub.add_parser(name)
    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)
    runtime = ExecutionRuntime(workspace)
    try:
        if args.command == "spawn":
            task, tasks = _task(workspace, args.task_id, args.scope)
            acceptance = task.get("acceptance") or task.get("acceptance_criteria") or []
            if isinstance(acceptance, str):
                acceptance = [acceptance]
            try:
                process = json.loads(args.command_json)
            except json.JSONDecodeError as exc:
                raise ExecutionError("--command-json must be a JSON argv array") from exc
            if not isinstance(process, list) or not all(isinstance(value, str) for value in process):
                raise ExecutionError("--command-json must be a JSON argv array")
            result = runtime.spawn(args.task_id, args.kind, Path(args.repository), str(task.get("title", args.task_id)), acceptance, process, scope=args.scope, delivery_mode=args.delivery_mode, executor=args.executor, brief_sections=_brief_sections(workspace, task, tasks, args.scope))
        elif args.command == "status":
            runtime.reconcile()
            result = runtime.status(args.run_id) if args.run_id else runtime.list_runs()
        elif args.command == "events":
            result = runtime.events(args.run_id)
        elif args.command == "stop":
            result = runtime.stop(args.run_id)
        elif args.command == "teardown":
            runtime.cleanup(args.run_id)
            result = runtime.status(args.run_id)
        elif args.command == "send":
            result = {"path": str(runtime.send(args.run_id, args.message, generation=args.generation))}
        elif args.command == "ack":
            result = {"path": str(runtime.acknowledge_message(args.run_id, args.name, generation=args.generation))}
        elif args.command == "actions":
            result = runtime.actions()
        elif args.command == "ack-action":
            runtime.acknowledge_action(args.action_id); result = {"acknowledged": args.action_id}
        elif args.command == "heartbeat":
            result = runtime.heartbeat(args.run_id, generation=args.generation, summary=args.summary)
        elif args.command == "liveness":
            result = {"run_id": args.run_id, "liveness": runtime.semantic_liveness(args.run_id, wedge_after_seconds=args.wedge_after)}
        elif args.command == "relaunch":
            result = runtime.relaunch(args.run_id)
        elif args.command == "validation-start":
            result = runtime.start_validation(args.run_id, args.validator)
        elif args.command == "validation-submit":
            result = runtime.submit_validation(args.run_id, args.verdict, args.spec, args.standards)
        elif args.command == "research-record":
            result = runtime.record_research(args.run_id, args.report, json.loads(args.citations_json), json.loads(args.decisions_json))
        elif args.command == "research-reconcile":
            result = runtime.reconcile_research(args.run_id, Path(args.evidence_log))
        elif args.command == "github-evidence":
            result = runtime.refresh_github_evidence(args.run_id, args.pr)
        elif args.command == "merge-ready":
            result = runtime.verify_merge_ready(args.run_id)
        elif args.command == "merge-local":
            result = {"head": runtime.merge_local(args.run_id, args.target, approval=args.approval)}
        elif args.command == "merge-github":
            result = {"head": runtime.merge_github(args.run_id, args.pr, approval=args.approval)}
        elif args.command == "reconcile-product":
            result = {"journal": str(runtime.reconcile_product_truth(args.run_id, Path(args.tasks), Path(args.gates)))}
        elif args.command == "compatibility":
            result = {"path": str(write_compatibility_matrix(Path(args.output)))}
        elif args.command == "enqueue":
            result = runtime.enqueue_dispatch(args.task_id, Path(args.repository), json.loads(args.command_json), kind=args.kind, title=args.title, acceptance=json.loads(args.acceptance_json), scope=args.scope, delivery_mode=args.delivery_mode, executor=args.executor, priority=args.priority, depends_on=json.loads(args.depends_on_json))
        elif args.command == "queue":
            result = runtime.dispatch_queue()
        elif args.command == "dispatch":
            result = runtime.supervisor_tick()
        else:
            controller = SupervisorController(workspace)
            result = {"supervisor-start": controller.start, "supervisor-status": controller.status, "supervisor-stop": controller.stop, "supervisor-tick": controller.tick}[args.command]()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except ExecutionError as exc:
        print(f"error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
