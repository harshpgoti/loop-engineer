# Phase: Task Compiler

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: task-compiler` - the last planning phase, run after `spec-checklist` is Ready and before `/develop-product`.

## Purpose

Turn strategy into small, gated engineering tasks.

## Required Reads

- `plan/main_plan.md`
- active `plan/step_*.md`
- active feature `spec.md`, `feature-plan.md`, `tasks.md` (`.loop/active-feature.json`)
- `DECISIONS.md`
- `GATES.yml`
- `TASKS.yml`
- `templates/acceptance_criteria.template.md`
- `templates/test_plan.template.md`
- `templates/feature_tasks.template.md`

## Cut vertically

A task is a **tracer bullet**: a narrow but complete path through every layer the behaviour
touches - schema, service, interface, tests - not a horizontal slice of one layer. A finished
task is demoable or verifiable on its own.

"Add the claims table", "add the claims endpoint", "add the claims screen" is three tasks that
each prove nothing and cannot be checked until all three land. "A user can see one imported
claim" is one task that proves the whole path works, thinly.

Prefactoring goes first: make the change easy, then make the easy change.

## The one exception: a wide refactor

One mechanical change whose blast radius fans across the codebase - rename a column, retype a
shared symbol - cannot be a tracer bullet. A single edit breaks thousands of call sites and no
vertical slice lands green. Sequence it **expand -> migrate -> contract** instead:

| Task | What it does | Blocked by |
|------|--------------|------------|
| expand | Add the new form beside the old. Nothing breaks | - |
| migrate (one per batch) | Move call sites over, batched by package or directory | expand |
| contract | Delete the old form once no caller remains | every migrate |

Tests stay green batch to batch because the old form still exists. When even a batch cannot
stay green alone, keep the sequence but let the batches share an integration branch that all
block a final integrate-and-verify task - green is promised there, and only there.

## Compilation Rules

- Every task must map to a user-visible outcome, platform capability, risk reduction, or validation need.
- Every development task needs acceptance criteria, and each one is independently checkable.
- Risky tasks need a gate in `GATES.yml`.
- **Reconcile before compiling.** Run `loop plan-reconcile check`: superseded or
  retired ids cited as live, scope/root mirror divergence, and map-vs-tracker
  mismatches must be fixed or retired (`loop plan-reconcile retire`) first -
  compiling tasks on top of a contradicted plan bakes the old story into the
  build. Blockers must read 0.
- **Sized for one fresh context window.** A task an agent cannot hold in a single session gets
  split, or it gets abandoned halfway and picked up wrong.
- Name the **seam** the task's tests will observe from (`skills/codebase-design/SKILL.md`).
  Prefer an existing seam, and the highest one that reaches the behaviour.
- Blockers must be explicit: `blocked_by` names the tasks that genuinely gate this one, and a
  task with none can start immediately. Work the frontier - whatever has no unfinished blocker.
- Write human-readable tasks to active feature `tasks.md` using `[P]` for parallel-safe items and `files:` paths.
- Sync the same task ids into `TASKS.yml` - do not maintain two conflicting lists.

## Output Files

Update or create:

- `TASKS.yml`
- active feature `tasks.md` (when `.loop/active-feature.json` exists)
- `GATES.yml`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TEST_PLAN.md`
- `HANDOFF.md`

## Task Shape

Each task should include:

- id
- title
- phase
- gate
- status
- priority
- blocked_by
- acceptance
- the seam its tests observe from

## Output

- New/updated tasks
- New/updated gates
- Acceptance criteria summary
- Next build task

## Continue automatically

This is the **planning terminus**: tasks are compiled and the feature is buildable.

- Invoked via `/loop-engine`: continue into `commands/develop-product.md` when the
  build gates pass - do not stop at the plan/build boundary.
- Invoked via `/plan-loop` (or a phase command that cascaded here): report the
  go/no-go and the compiled tasks, then run `loop session-end`. Starting the build
  is a scope change the user opts into with `/develop-product` or `/loop-engine`.

Either way, finish the run: update `TASKS.yml`, `HANDOFF.md`, and memory before
ending. See `docs/CONTINUATION.md`.
