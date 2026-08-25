"""Tasks, gates and doubts unioned across the platform and every scope.

In the federated design each sub-product's `TASKS.yml` lived in a workspace of its
own, so a task in one could never be `blocked_by` a task in another - the id was not
resolvable. Here every scope's file is in the same tree, so the union is the natural
read and a cross-scope dependency is an index lookup rather than a sync problem.

Two rules the loaders enforce:

- **Every record carries the scope it came from.** Nothing downstream should have to
  infer it from a path, and a record with no scope is platform-level, not unknown.
- **An unresolvable reference is reported, never dropped.** A `blocked_by` naming a
  task no scope defines is exactly what a half-finished absorb leaves behind, and
  quietly ignoring it would let a build start on a dependency that does not exist.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import scope_paths as sp
from task_context import parse_tasks_file


DONE_STATUSES = {"done", "complete", "completed", "shipped"}


# ---------------------------------------------------------------------------
# tasks
# ---------------------------------------------------------------------------


def load_tasks(workspace: Path, *, scope: str | None = None) -> list[dict]:
    """Every task, tagged with its scope.

    `scope=None` returns the union (platform + all scopes). `scope="<slug>"` returns
    that scope's own tasks **plus** the platform tasks, because platform work gates
    scope work - a scope build that could not see `G-PLATFORM-01` would report itself
    unblocked when it is not.
    """
    tasks: list[dict] = []
    for task in parse_tasks_file(Path(workspace) / "TASKS.yml"):
        task["scope"] = sp.PLATFORM
        task["source"] = "TASKS.yml"
        tasks.append(task)

    for record in sp.list_scopes(workspace):
        if scope is not None and record.slug != scope:
            continue
        for task in parse_tasks_file(record.tasks_file):
            task["scope"] = record.slug
            task["source"] = f"plan/products/{record.slug}/TASKS.yml"
            tasks.append(task)
    return tasks


def blockers_of(task: dict) -> list[str]:
    raw = task.get("blocked_by") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(item).strip() for item in raw if str(item).strip()]


@dataclass
class Unresolved:
    task: str
    scope: str
    missing: str

    def __str__(self) -> str:
        return f"{self.task} ({self.scope}) is blocked by `{self.missing}`, which no scope defines"


def unresolved_blockers(tasks: list[dict]) -> list[Unresolved]:
    """`blocked_by` entries naming neither a known task nor a gate.

    Gate ids in `blocked_by` are legitimate and checked through the gate, so they are
    not reported here - the same rule `task_context.active_task` applies.
    """
    known = {str(task.get("id")) for task in tasks if task.get("id")}
    out: list[Unresolved] = []
    for task in tasks:
        for blocker in blockers_of(task):
            if blocker.startswith("G-") or blocker in known:
                continue
            out.append(Unresolved(task=str(task.get("id")), scope=str(task.get("scope")), missing=blocker))
    return out


def cross_scope_blocks(tasks: list[dict]) -> list[dict]:
    """Tasks blocked by a task belonging to a different scope - the thing the
    federated design could not express at all."""
    by_id = {str(task.get("id")): task for task in tasks if task.get("id")}
    done = {tid for tid, task in by_id.items() if str(task.get("status", "")).lower() in DONE_STATUSES}
    out: list[dict] = []
    for task in tasks:
        for blocker in blockers_of(task):
            other = by_id.get(blocker)
            if other is None or other.get("scope") == task.get("scope"):
                continue
            out.append(
                {
                    "task": str(task.get("id")),
                    "scope": str(task.get("scope")),
                    "blocked_by": blocker,
                    "provider_scope": str(other.get("scope")),
                    "satisfied": blocker in done,
                }
            )
    return out


def ready_tasks(tasks: list[dict]) -> list[dict]:
    """Not done, and nothing outstanding blocks them - across scopes."""
    by_id = {str(task.get("id")): task for task in tasks if task.get("id")}
    done = {tid for tid, task in by_id.items() if str(task.get("status", "")).lower() in DONE_STATUSES}
    out: list[dict] = []
    for task in tasks:
        if str(task.get("status", "")).lower() in DONE_STATUSES:
            continue
        outstanding = [b for b in blockers_of(task) if not b.startswith("G-") and b not in done]
        if not outstanding:
            out.append(task)
    return out


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------


GATE_LINE = re.compile(r"^\s{2,}(?P<id>G-[A-Za-z0-9][A-Za-z0-9-]*):\s*$")
GATE_FIELD = re.compile(r"^\s+(?P<key>name|phase|status):\s*(?P<value>.+?)\s*$")


def parse_gates_file(path: Path) -> list[dict]:
    """Gate ids and their headline fields, parsed the same yaml-free way as tasks."""
    if not Path(path).is_file():
        return []
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    gates: list[dict] = []
    current: dict | None = None
    for raw in lines:
        header = GATE_LINE.match(raw)
        if header:
            current = {"id": header.group("id")}
            gates.append(current)
            continue
        if current is None:
            continue
        field_match = GATE_FIELD.match(raw)
        if field_match:
            current[field_match.group("key")] = field_match.group("value").strip().strip("\"'")
    return gates


def load_gates(workspace: Path, *, scope: str | None = None) -> list[dict]:
    gates: list[dict] = []
    for gate in parse_gates_file(Path(workspace) / "GATES.yml"):
        gate["scope"] = sp.PLATFORM
        gates.append(gate)
    for record in sp.list_scopes(workspace):
        if scope is not None and record.slug != scope:
            continue
        for gate in parse_gates_file(record.gates_file):
            gate["scope"] = record.slug
            gates.append(gate)
    return gates


def duplicate_gate_ids(gates: list[dict]) -> list[str]:
    """The same gate id declared in two places.

    Per-scope gates are the decided model, so `G-AUTH-01` living in `auth` is normal -
    but the *same* id in two scopes means one of them will be read and the other
    ignored, which is how a gate silently stops being enforced.
    """
    seen: dict[str, str] = {}
    clashes: list[str] = []
    for gate in gates:
        gid = str(gate.get("id"))
        scope = str(gate.get("scope"))
        if gid in seen and seen[gid] != scope:
            clashes.append(f"{gid} declared in both `{seen[gid]}` and `{scope}`")
        else:
            seen[gid] = scope
    return clashes


# ---------------------------------------------------------------------------
# doubts
# ---------------------------------------------------------------------------


def doubt_files(workspace: Path, *, scope: str | None = None) -> list[tuple[str, Path]]:
    """(scope, path) for every `DOUBTS.md` that exists - platform first."""
    out: list[tuple[str, Path]] = []
    root = Path(workspace) / "DOUBTS.md"
    if root.is_file():
        out.append((sp.PLATFORM, root))
    for record in sp.list_scopes(workspace):
        if scope is not None and record.slug != scope:
            continue
        if record.doubts_file.is_file():
            out.append((record.slug, record.doubts_file))
    return out


# ---------------------------------------------------------------------------
# one summary every command can print
# ---------------------------------------------------------------------------


@dataclass
class ScopeSummary:
    slug: str
    name: str
    code_dir: str | None
    status: str
    tasks_total: int = 0
    tasks_ready: int = 0
    tasks_done: int = 0
    blocked_on: list[str] = field(default_factory=list)

    def line(self) -> str:
        where = f" ({self.code_dir})" if self.code_dir else ""
        bits = [f"{self.tasks_ready} ready", f"{self.tasks_done}/{self.tasks_total} done"]
        if self.blocked_on:
            bits.append("blocked on " + ", ".join(sorted(set(self.blocked_on))))
        return f"{self.slug}{where} - {'; '.join(bits)}"


def summarize(workspace: Path) -> list[ScopeSummary]:
    tasks = load_tasks(workspace)
    ready = {str(t.get("id")) for t in ready_tasks(tasks)}
    blocks = cross_scope_blocks(tasks)
    out: list[ScopeSummary] = []
    ordered, _cycles = sp.dependency_order(workspace)
    for record in ordered:
        mine = [t for t in tasks if t.get("scope") == record.slug]
        out.append(
            ScopeSummary(
                slug=record.slug,
                name=record.title,
                code_dir=record.code_dir,
                status=record.status,
                tasks_total=len(mine),
                tasks_ready=len([t for t in mine if str(t.get("id")) in ready]),
                tasks_done=len([t for t in mine if str(t.get("status", "")).lower() in DONE_STATUSES]),
                blocked_on=[
                    b["provider_scope"]
                    for b in blocks
                    if b["scope"] == record.slug and not b["satisfied"]
                ],
            )
        )
    return out
