"""Dependency-free deterministic validators for durable execution records."""

from __future__ import annotations

import re

RUN_ID = re.compile(r"^run-[a-f0-9]{12}$")


def _require(record: dict, fields: tuple[str, ...], kind: str) -> None:
    missing = [field for field in fields if field not in record]
    if missing:
        raise ValueError(f"{kind} missing required fields: {', '.join(missing)}")


def validate_worker(record: dict) -> None:
    _require(record, ("schema_version", "run_id", "task_id", "kind", "generation", "state", "run_dir"), "worker")
    if record["schema_version"] != 1 or not RUN_ID.fullmatch(str(record["run_id"])):
        raise ValueError("worker identity/schema is invalid")
    if record["kind"] not in {"delivery", "research", "validation"} or int(record["generation"]) < 1:
        raise ValueError("worker kind/generation is invalid")


def validate_event(record: dict) -> None:
    _require(record, ("run_id", "generation", "sequence", "timestamp", "event", "event_id"), "event")
    if int(record["generation"]) < 1 or int(record["sequence"]) < 1 or len(record.get("summary", "")) > 500:
        raise ValueError("event generation/sequence/summary is invalid")


def validate_review(record: dict) -> None:
    _require(record, ("validation_run_id", "run_id", "validator", "base_commit", "head_commit", "verdict", "spec", "standards"), "review")
    if record["verdict"] not in {"pass", "fail"}:
        raise ValueError("review verdict is invalid")


def validate_research(record: dict) -> None:
    _require(record, ("run_id", "report", "citations", "decision_inventory"), "research")
    if not record["report"] or not isinstance(record["citations"], list) or not record["citations"]:
        raise ValueError("research report/citations are invalid")


def validate_dispatch(record: dict) -> None:
    _require(record, ("request_id", "task_id", "repository", "command", "kind", "priority", "depends_on", "state"), "dispatch")
    if not str(record["request_id"]).startswith("dispatch-") or record["kind"] not in {"delivery", "research"} or not isinstance(record["command"], list) or not record["command"]:
        raise ValueError("dispatch identity/kind/command is invalid")
