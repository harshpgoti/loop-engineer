# 0001 - Product truth and execution state are separate stores

**Status:** Accepted
**Phase:** 0 (contracts and fixtures) of `docs/LOOP_EXECUTION_ARCHITECTURE_PLAN.md`

## Context

Loop gained an execution plane: compiled tasks become bounded worker runs in
isolated git worktrees, observed and reconciled by a supervisor. That plane
produces its own durable state - a run registry, leases, event streams, worktree
and branch names, backend process identity, review verdicts.

Without a stated boundary, that state has an obvious place to go: the same
workspace files the product already keeps its truth in. A worker would append its
own status to `TASKS.yml`, a review verdict would flip a row in `GATES.yml`, and
a research run would write straight into `EVIDENCE_LOG.md`. Each of those is one
small convenience, and together they make the workspace unreadable: nobody can
tell which lines a human decided and which a process wrote, a crashed run leaves
half-written product truth behind, and re-running a task rewrites history that
gates were approved against.

The supervisor is an execution role. It is not a second author of the product.

## Decision

Product truth and execution state are two stores with one direction of flow
between them.

**Product truth** - human- and agent-authored, durable, the thing gates approve:

| Store | Holds |
|---|---|
| `plan/` (`main_plan.md`, steps, `plan/products/<scope>/`, `plan/features/`) | What is being built |
| `TASKS.yml`, `GATES.yml` | What is committed to and what blocks it |
| `DECISIONS.md`, `DOUBTS.md`, `EVIDENCE_LOG.md` | What was decided, what is unresolved, what it rests on |
| `memories/`, `HANDOFF.md`, `state.db` | What carries across sessions |

**Execution state** - derived, disposable, owned entirely by the runtime:

| Store | Holds |
|---|---|
| `workers/registry.json` | Every run, keyed by `run_id`, schema-versioned |
| `workers/<run_id>/meta.json`, `events.jsonl` | One run's record and its ordered events |
| `locks/task-<id>.lock`, `locks/delivery.lock` | Leases that refuse a duplicate or concurrent run |
| Git worktrees and branches | The isolated tree a run is allowed to change |

`scripts/execution_runtime.py` roots all of it at `<workspace>/workers` and
`<workspace>/locks`. Deleting that subtree loses runs in flight and loses nothing
about the product.

### The two crossings

**Truth into a run: read-only, at one point, immutably.** The brief compiler in
`scripts/execution_cli.py` reads the canonical task, its dependencies, the
required gate block, and bounded slices of `DECISIONS.md`, `prd.md`, and
`architecture.md`, and freezes them into one brief. The brief is hashed at
launch; if it no longer matches, the runtime refuses to relaunch rather than
continue against changed truth. A worker reads its brief and its worktree, never
the workspace's live product files.

**Run into truth: through the supervisor, never by the worker.** A delivery
candidate, a cited research report, and a validation verdict are all *findings*.
They reconcile into evidence, doubts, decisions, or tasks as a deliberate
supervisor action, subject to Loop's existing gates and human authority. No
worker process writes `TASKS.yml`, `GATES.yml`, or any file in the table above.

### Numbering

ADRs in this directory are `NNNN-kebab-title.md`, numbered in the order they were
accepted, and are append-only: a decision that no longer holds gets a new ADR
that supersedes it, not an edit. Product-workspace ADRs are a different thing and
live with the product, in its `DECISIONS.md` or its `architecture.md`.

## Consequences

- A crashed, killed, or abandoned run cannot leave the product in a half-written
  state; teardown is a subtree delete plus worktree removal.
- Gate approval stays meaningful: the artifact a gate was approved against cannot
  have been mutated by a run that started after it.
- Duplicate work is refused at the lease, not detected later by reading tasks.
- Cost: findings need an explicit reconciliation step. That is intended - it is
  the point at which a human or the supervisor exercises authority.
- Anything in `workers/` is a runtime detail and may change with the schemas in
  `schemas/execution/`; nothing outside the runtime may depend on its layout.
