# /spec-clarify

Structured clarification for the active feature spec.

## How To Interpret

If the user says `/spec-clarify`, execute this file and `skills/plan-loop/phases/spec-clarify.md`.

## Required Reads

1. `skills/plan-loop/phases/spec-clarify.md`
2. Active feature `spec.md`, `clarifications.md`
3. `DOUBTS.md`, `DECISIONS.md`

## Wired From

- `/plan-loop` after feature spec draft, before spec-checklist
- `/develop-product` when blocked on ambiguous requirements

## Continuation

Terminus: **tasks compiled + go/no-go for build.** After clarifying, continue
automatically into `spec-checklist` → `resolve-doubts` (if open doubts) →
`task-compiler`. Do not stop and tell the user to run those - see
`docs/CONTINUATION.md`.

## Stop Conditions

- A blocking question only the user can answer - ask it, report what you need.
- A strategic pivot - route to `skills/plan-loop/phases/council.md`.
- Sensitive/regulated data before `G-SENSITIVE-DATA` passes.

## Output

Updated `clarifications.md` and resolved open questions in `spec.md`, plus the
downstream results (checklist verdict, doubts cleared, tasks compiled) - or the
Stop Condition that halted the cascade and what it needs.

## Loop

1. READ the active feature's `spec.md`
2. RUN each clarifier from `phases/spec-clarify.md`
3. WRITE the answers into the spec
4. EMIT a `## Clarifications` block in the spec
