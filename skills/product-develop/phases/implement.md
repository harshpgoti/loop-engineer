# Phase: Implement

> Loaded by `skills/product-develop/SKILL.md` when `BUILD PHASE: implement`.
> Load only this file. The other phase files are for other phases.

## Purpose

Build the one task named in `plan/BUILD_CONTEXT.md`, in the smallest safe diff.

## Read First

1. `plan/BUILD_CONTEXT.md` - the active task, its dependencies, its gate, and the
   doubts that block it. This replaces reading `TASKS.yml` and `GATES.yml` whole.
2. `plan/SESSION_MANIFEST.md`
3. Active feature: `spec.md`, `feature-plan.md`, `tasks.md`
4. `skills/implementation-planner/SKILL.md`
5. `skills/feature-workflow/SKILL.md`
6. `plan/AUTO_SKILLS.md` / `plan/AUTO_AGENT_SKILLS.md` when present

Do **not** preload the security, deployment, prod-gap or release skills - they load
in the `release` phase.

## Process

1. **Check the blockers first.** `plan/BUILD_CONTEXT.md` lists blocking doubts and
   unmet dependencies. Run `loop doubts ask` and `loop findings ask` if either is
   non-empty - each comes with a recommended answer. Do not build past an unanswered
   blocking question.
2. **Plan the diff** with `skills/implementation-planner/SKILL.md` before editing.
3. **Implement the smallest change** that satisfies the task's `acceptance` list.
   Match surrounding conventions; no drive-by refactors (`AGENTS.md` #9).
4. **Write the tests with the code** (`AGENTS.md` #10). No task is done without them,
   or a documented reason they could not run.
5. **Update the task's status** in `TASKS.yml` when it is genuinely complete - that is
   the source of truth, and it is what moves the next session on.

## Gate check

Classify before building. Blocked until the relevant gate passes:

- Production feature, sensitive or regulated data, external integration.
- Unanswered `error` finding from the parent product.

Reversible synthetic scaffolding is allowed when the doubts are recorded.

## Continue automatically

- **Task complete, tests green** -> mark it done, then continue: the next
  `loop session-start` routes to `test` or `converge`. Do not stop to report.
- **A blocking question has no answer you can derive** -> Stop Condition. Name it and
  what you need (`docs/CONTINUATION.md`).

## Output

Task built, files changed, tests added and their result, `TASKS.yml` status change,
and what the next phase will be.
