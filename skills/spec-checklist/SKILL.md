---
name: spec-checklist
description: Validates active feature spec quality before feature-plan and task compile. Use when the user types /spec-checklist during /plan.
---

# Spec Checklist

## Purpose

Quality gate on the active feature spec — completeness, testability, alignment with product plan.

## Command

`/spec-checklist`

## Read First

1. `skills/feature-workflow/SKILL.md`
2. Active feature `spec.md`, `clarifications.md`
3. `plan/main_plan.md`, active `plan/step_*.md`
4. `templates/feature_spec_checklist.template.md`

## Steps

1. Ensure active feature exists; if `spec-checklist.md` missing, copy from template.
2. Walk each checklist section; mark pass/fail with brief notes.
3. Flag duplicates vs step plan or `plan/main_plan.md`.
4. If **Needs clarify**, stop and run `/spec-clarify`.
5. If **Ready for feature-plan**, proceed to `feature-plan.md` and `task-compiler`.

## Output

- Updated `spec-checklist.md` with verdict
- Blockers list (if not ready)

## Next

`skills/task-compiler/SKILL.md` → then `/product-develop`.
