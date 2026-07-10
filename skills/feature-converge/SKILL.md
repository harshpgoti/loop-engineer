---
name: feature-converge
description: Compares active feature spec/plan/tasks against TASKS.yml and implementation drift. Use at /product-develop closeout or /feature-converge.
---

# Feature Converge

## Purpose

Post-build drift check: spec, feature-plan, tasks.md, and `TASKS.yml` stay aligned.

## Command

`/feature-converge`

## Script

```bash
loop feature converge
python scripts/feature_converge.py
```

## Read First

1. `skills/feature-workflow/SKILL.md`
2. Active feature folder artifacts
3. `TASKS.yml`, `HANDOFF.md`, `CURRENT_STATE.md`

## Steps

1. Run `loop feature converge` to write `converge-report.md`.
2. Review gaps: missing artifacts, unchecked tasks, TASK id mismatch.
3. Fix real drift via `task-compiler` or update spec if scope changed (with user approval).
4. Update `HANDOFF.md` with next task from active feature `tasks.md`.

## Output

- `converge-report.md`
- Recommended next command: `/product-develop`, `/spec-clarify`, or `/prod-gap`

## When

- End of each `/product-develop` session that touched code
- Before `/prod-gap` for a feature milestone
