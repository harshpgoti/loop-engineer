# /spec-checklist

Validate active feature spec quality before feature-plan and tasks.

## How To Interpret

If the user says `/spec-checklist`, execute this file and `skills/plan-loop/phases/spec-checklist.md`.

## Required Reads

1. `skills/plan-loop/phases/spec-checklist.md`
2. Active feature `spec.md`, `clarifications.md`, `spec-checklist.md`

## Wired From

- `/plan-loop` after `/spec-clarify`, before `feature-plan.md` and task-compiler

## Continuation

Terminus: **tasks compiled + go/no-go for build.**

- Verdict **Ready** → continue into `resolve-doubts` (if `DOUBTS.md` has open
  items) then `task-compiler`.
- Verdict **Needs clarify** → loop back into `spec-clarify` yourself, resolve the
  listed blockers, then re-run this checklist. This is a loop-back, **not** a stop:
  do not hand it to the user.

Do not compile tasks while the verdict is Needs clarify. See `docs/CONTINUATION.md`.

## Stop Conditions

- A blocker needs an answer only the user has - ask it directly.
- Repeated clarify↔checklist cycles with no progress - report what is unresolvable.

## Output

Updated `spec-checklist.md` with ready/blocked verdict, plus the downstream results
(doubts cleared, tasks compiled) - or the Stop Condition and what it needs.
