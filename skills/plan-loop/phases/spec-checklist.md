# Phase: Spec Checklist

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: spec-checklist`, or when the user types `/spec-checklist`.

## Purpose

Quality gate on the active feature spec - completeness, testability, alignment with product plan.

## Read First

1. `skills/feature-workflow/SKILL.md`
2. Active feature `spec.md`, `clarifications.md`
3. `plan/main_plan.md`, active `plan/step_*.md`
4. `templates/feature_spec_checklist.template.md`

## Steps

1. Ensure active feature exists; if `spec-checklist.md` missing, copy from template.
2. Walk each checklist section; mark pass/fail with brief notes.
3. Flag duplicates vs step plan or `plan/main_plan.md`.
4. If **Needs clarify**, stop and go back to the `spec-clarify` phase.
5. If **Ready for feature-plan**, proceed to `feature-plan.md` and the `task-compiler` phase.

## Output

- Updated `spec-checklist.md` with verdict
- Blockers list (if not ready)

## Next phase

`task-compiler` → then `/product-develop`.
