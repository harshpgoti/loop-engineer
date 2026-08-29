#!/usr/bin/env python3
"""The slice of build state one task actually needs.

A development session used to load `TASKS.yml`, `GATES.yml` and `DOUBTS.md` whole -
on a real workspace that is 38 tasks, every gate, and every question ever raised,
about 43KB, to implement one task. The cost is not only tokens: attention spent on
37 irrelevant tasks and a dozen passed gates is attention not on the one being built.

So this writes `plan/BUILD_CONTEXT.md`: the active task, what it is blocked by, the
gate it must satisfy, and the doubts that actually block it. The full files stay on
disk and stay the place to *write* - this only narrows what is read.

Deterministic (`AGENTS.md` non-negotiable #4): the task is selected by status and
dependency order, never by a model's judgement.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

BUILD_CONTEXT_FILE = "plan/BUILD_CONTEXT.md"

ACTIVE_STATUSES = ("in_progress", "doing", "active")
DONE_STATUSES = ("completed", "done", "complete")

TASK_ID = re.compile(r"^\s*-\s+id:\s*(?P<id>\S+)\s*$")
FIELD = re.compile(r"^\s+(?P<key>[a-z_]+):\s*(?P<value>.*)$")
LIST_ITEM = re.compile(r"^\s+-\s+(?P<value>.+)$")


def build_context_file(workspace: Path) -> Path:
    return workspace / BUILD_CONTEXT_FILE


# ---------------------------------------------------------------------------
# TASKS.yml - parsed without a yaml dependency, the same way the rest of the
# harness reads it (status.py, parent_watermark.py).
# ---------------------------------------------------------------------------


def parse_tasks(workspace: Path) -> list[dict]:
    return parse_tasks_file(workspace / "TASKS.yml")


def parse_tasks_file(path: Path) -> list[dict]:
    """Parse one `TASKS.yml`. Split out from `parse_tasks` so the scope loader can
    read a sub-product's file (`plan/products/<slug>/TASKS.yml`) with the same parser
    rather than growing a second one that drifts."""
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    tasks: list[dict] = []
    current: dict | None = None
    list_key: str | None = None

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        header = TASK_ID.match(raw)
        if header:
            current = {"id": header.group("id").strip().strip("\"'"), "raw": [raw]}
            tasks.append(current)
            list_key = None
            continue
        if current is None:
            continue

        current["raw"].append(raw)

        item = LIST_ITEM.match(raw)
        if item and list_key:
            current.setdefault(list_key, []).append(item.group("value").strip())
            continue

        field = FIELD.match(raw)
        if not field:
            continue
        key, value = field.group("key"), field.group("value").strip()
        if not value:
            list_key = key
            current.setdefault(key, [])
            continue
        list_key = None
        if value.startswith("[") and value.endswith("]"):
            current[key] = [v.strip().strip("\"'") for v in value[1:-1].split(",") if v.strip()]
        else:
            current[key] = value.strip().strip("\"'")

    return tasks


def _status(task: dict) -> str:
    return str(task.get("status", "")).lower()


def active_task(tasks: list[dict]) -> dict | None:
    """The task being built: an in-progress one, else the first unblocked pending one.

    Ties break on file order, which is the order tasks were compiled - so the same
    session picks the same task, and two agents reading the same workspace agree.
    """
    for task in tasks:
        if _status(task) in ACTIVE_STATUSES:
            return task

    done = {t["id"] for t in tasks if _status(t) in DONE_STATUSES}
    for task in tasks:
        if _status(task) in DONE_STATUSES:
            continue
        blockers = task.get("blocked_by") or []
        if isinstance(blockers, str):
            blockers = [blockers]
        # A gate id in blocked_by is not a task - it is checked through the gate.
        outstanding = [b for b in blockers if b.startswith("TASK") and b not in done]
        if not outstanding:
            return task
    return None


def dependencies(tasks: list[dict], task: dict) -> list[dict]:
    by_id = {t["id"]: t for t in tasks}
    blockers = task.get("blocked_by") or []
    if isinstance(blockers, str):
        blockers = [blockers]
    return [by_id[b] for b in blockers if b in by_id]


# ---------------------------------------------------------------------------
# GATES.yml
# ---------------------------------------------------------------------------


# Two shapes of `GATES.yml` are in the wild and both are valid YAML for the same data:
# the starter's mapping form (`  G-INIT-01:` with fields beneath it) and the sequence
# form (`  - id: G-INIT-01`). Reading only the mapping form is not a cosmetic gap - a
# root file written in sequence form parsed to *zero* gates, so every platform gate was
# invisible to the union loader, to `duplicate-gate` detection, and to the brief
# compiler's "Required gate" section, silently and with no error anywhere.
GATE_LINE = re.compile(r"^(?P<indent>\s{2,})(?P<id>G-[A-Za-z0-9][A-Za-z0-9-]*):\s*$")
GATE_ROW = re.compile(r"^(?P<indent>\s*)-\s+id:\s*(?P<id>G-[A-Za-z0-9][A-Za-z0-9-]*)\s*$")
GATE_FIELD = re.compile(r"^\s+(?P<key>name|phase|status):\s*(?P<value>.+?)\s*$")


def gate_headers(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """`(line index, indent, gate id, form)` for every gate declared in `lines`.

    `form` is `mapping` or `sequence`. One scanner so every reader agrees on where a
    gate starts and where the next one begins - `task_context.gate_block` slices the
    same headers this function reports.
    """
    out: list[tuple[int, int, str, str]] = []
    for index, raw in enumerate(lines):
        mapping = GATE_LINE.match(raw)
        if mapping:
            out.append((index, len(mapping.group("indent")), mapping.group("id"), "mapping"))
            continue
        row = GATE_ROW.match(raw)
        if row:
            out.append((index, len(row.group("indent")), row.group("id"), "sequence"))
    return out


def gate_field(line: str):
    """One headline field of the gate currently being read, or None."""
    return GATE_FIELD.match(line)


def gate_forms(path: Path) -> set[str]:
    """Which declaration forms one file uses - `{"mapping"}`, `{"sequence"}`, or both."""
    if not Path(path).is_file():
        return set()
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return set()
    return {form for _index, _indent, _gid, form in gate_headers(lines)}


def gate_block(workspace: Path, gate_id: str) -> str:
    """The one gate this task must satisfy, with its criteria - not all of them."""
    path = workspace / "GATES.yml"
    if not gate_id or not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return ""

    # Both declaration forms, through the one scanner - a sequence-form file used to
    # match nothing here, so a brief for a task gated by it was compiled with its
    # "Required gate" section simply absent rather than failing.
    headers = gate_headers(lines)
    start = None
    indent = 0
    form = "mapping"
    for index, gate_indent, gid, gate_form in headers:
        if gid == gate_id:
            start, indent, form = index, gate_indent, gate_form
            break
    if start is None:
        return ""

    nxt = min(
        (index for index, _i, _g, _f in headers if index > start),
        default=len(lines),
    )

    out = [lines[start]]
    for line in lines[start + 1 : nxt]:
        stripped = line.strip()
        if not stripped:
            out.append(line)
            continue
        if stripped.startswith("```"):
            break
        # Anything back at the gate's own indent starts the next section - including a
        # comment, which would otherwise be pulled in as part of this gate. A sequence
        # row's fields are indented past the `-`, so its own indent is not a boundary.
        line_indent = len(line) - len(line.lstrip())
        if form == "mapping" and line_indent <= indent and (stripped.endswith(":") or stripped.startswith("#")):
            break
        if form == "sequence" and line_indent <= indent and stripped.startswith("#"):
            break
        out.append(line)

    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out).rstrip()


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def _task_yaml(task: dict) -> str:
    return "\n".join(task.get("raw", [])).rstrip()


def _blocking_doubts(workspace: Path) -> list:
    try:
        from doubts import blocking_doubts

        return blocking_doubts(workspace)
    except Exception:
        return []


def render(workspace: Path) -> str:
    tasks = parse_tasks(workspace)
    task = active_task(tasks)
    counts = {
        "total": len(tasks),
        "done": sum(1 for t in tasks if _status(t) in DONE_STATUSES),
    }

    lines = [
        "# Build Context",
        "",
        f"**Generated:** {date.today().isoformat()}",
        "",
        "The slice of build state this task needs. Generated by `loop session-start` -",
        "never edit it. `TASKS.yml`, `GATES.yml` and `DOUBTS.md` remain the source of",
        "truth and the place to **write**; this is only what you need to **read**.",
        "",
    ]

    if task is None:
        lines.extend(
            [
                "## No active task",
                "",
                f"{counts['done']}/{counts['total']} task(s) complete and nothing is unblocked.",
                "Compile tasks with `/plan-loop` (task-compiler phase), or read `TASKS.yml`",
                "directly if you believe this is wrong.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"## Active task: {task['id']}",
            "",
            f"- **Title:** {task.get('title', '(untitled)')}",
            f"- **Status:** {task.get('status', 'pending')}",
            f"- **Phase:** {task.get('phase', '-')}  **Priority:** {task.get('priority', '-')}",
            f"- **Gate:** `{task.get('gate', '-')}`",
            f"- **Progress:** {counts['done']}/{counts['total']} task(s) complete",
            "",
            "```yaml",
            _task_yaml(task),
            "```",
            "",
        ]
    )

    deps = dependencies(tasks, task)
    if deps:
        lines.extend(["## Depends on", ""])
        for dep in deps:
            state = _status(dep) or "pending"
            mark = "done" if state in DONE_STATUSES else f"**{state}**"
            lines.append(f"- `{dep['id']}` ({mark}) - {dep.get('title', '')}")
        unmet = [d for d in deps if _status(d) not in DONE_STATUSES]
        if unmet:
            lines.extend(
                [
                    "",
                    f"**{len(unmet)} dependency(ies) are not done.** Finish those first, or say why "
                    "this task can proceed without them.",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## If you need more",
            "",
            "- Another task's detail: `TASKS.yml`",
            "- Another gate: `GATES.yml`",
            "- Resolved or non-blocking questions: `loop doubts list --verbose`",
            "- Why a finished task or decision was made that way: `loop archive --search \"<term>\"`",
            "",
        ]
    )

    # Constraints last, and verbatim. Two 2026 studies measured constraint loss
    # through compaction independently: violations rose 0% -> 30% (Governance Decay,
    # arXiv:2606.22528) and session constraints retained ~17% on average, with
    # *process* constraints - which is what a gate is - under 10% (Lost in
    # Compaction, arXiv:2608.11242). Both land on the same rule: keep constraints out
    # of any lossy path, quote them in full, and put them near the end, where
    # retention measured 25-40% against 1-15% at the top.
    lines.extend(_constraints_block(workspace, task))
    return "\n".join(lines)


def _constraints_block(workspace: Path, task: dict) -> list[str]:
    lines = ["## Constraints - do not summarise or skip", ""]

    gate = gate_block(workspace, str(task.get("gate", "")))
    if gate:
        lines.extend([f"### Gate `{task.get('gate')}` - this task cannot pass without it", "", "```yaml", gate, "```", ""])

    blocking = _blocking_doubts(workspace)
    if not blocking:
        lines.extend(["### Blocking questions", "", "None. No open question is holding up the build.", ""])
        return lines

    lines.extend(
        [
            f"### Blocking questions ({len(blocking)}) - answer or defer before building",
            "",
            "`loop doubts ask` gives each one with its recommended answer;",
            "`loop doubts resolve <id> \"<answer>\"` records it.",
            "",
        ]
    )
    # In full, every one of them. A truncated list is the lossy path the studies above
    # measured, and a dropped constraint is obeyed at 38% versus 100% when it survives.
    for item in blocking:
        lines.append(f"**{item.id}: {item.title}**")
        if item.question:
            lines.append(f"- **Question:** {item.question}")
        if item.why:
            lines.append(f"- **Why it matters:** {item.why}")
        if item.default:
            lines.append(f"- **Default if unavailable:** {item.default}")
        lines.append("")
    return lines


# Bump when `render` changes shape. A generated file whose generator has moved is
# wrong-but-clean otherwise - Make's most famous defect, and the one hashing inputs
# alone does not catch.
GENERATOR_VERSION = 2

# Every file `render` reads. This list is the load-bearing part of the freshness
# check: an input that is read but not declared here will never mark the view stale,
# silently and permanently. `test_freshness.BuildFuzz` guards it.
SOURCES = ("TASKS.yml", "GATES.yml", "DOUBTS.md", "DECISIONS.md")


def write_context(workspace: Path) -> Path | None:
    """Write plan/BUILD_CONTEXT.md. Returns None when there is no TASKS.yml to slice."""
    if not (workspace / "TASKS.yml").is_file():
        return None
    path = build_context_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(workspace), encoding="utf-8")
    try:
        import freshness

        freshness.stamp(
            path,
            [workspace / name for name in SOURCES],
            generator="build-context",
            version=GENERATOR_VERSION,
            workspace=workspace,
            command="loop session-start",
        )
    except Exception:
        pass  # an unstamped view reads as stale, which is the safe direction
    return path


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()

    parser = argparse.ArgumentParser(description="Write plan/BUILD_CONTEXT.md for the active task.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--print", action="store_true", help="Print instead of writing.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    if args.print:
        print(render(workspace))
        return 0
    path = write_context(workspace)
    print(f"Wrote {path}" if path else "No TASKS.yml in this workspace - nothing to slice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
