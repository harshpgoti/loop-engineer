---
name: task-compiler
description: Converts product plans, PRDs, ADRs, and step plans into buildable tasks, gates, acceptance criteria, test plans, and handoff-ready implementation slices. Use after /plan-loop and before /product-develop.
---

# Task Compiler

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

## Compilation Rules

- Every task must map to a user-visible outcome, platform capability, risk reduction, or validation need.
- Every development task needs acceptance criteria.
- Risky tasks need a gate in `GATES.yml`.
- Tasks should be small enough for one focused agent session when possible.
- Blockers must be explicit.
- Write human-readable tasks to active feature `tasks.md` using `[P]` for parallel-safe items and `files:` paths.
- Sync the same task ids into `TASKS.yml` — do not maintain two conflicting lists.

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

## Output

- New/updated tasks
- New/updated gates
- Acceptance criteria summary
- Next build task
