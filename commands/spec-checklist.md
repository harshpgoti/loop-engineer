# /spec-checklist

Validate active feature spec quality before feature-plan and tasks.

## How To Interpret

If the user says `/spec-checklist`, execute this file and `skills/plan-loop/phases/spec-checklist.md`.

## Required Reads

1. `skills/plan-loop/phases/spec-checklist.md`
2. Active feature `spec.md`, `clarifications.md`, `spec-checklist.md`

## Wired From

- `/plan-loop` after `/spec-clarify`, before `feature-plan.md` and task-compiler

## Stop Condition

If verdict is **Needs clarify**, run `/spec-clarify` - do not compile tasks yet.

## Output

Updated `spec-checklist.md` with ready/blocked verdict.
