# Phase: Spec Clarify

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: spec-clarify`, or when the user types `/spec-clarify`.

## Purpose

Turn open questions in the active feature `spec.md` into answered rows in `clarifications.md`.

## Read First

1. `skills/feature-workflow/SKILL.md`
2. `.loop/active-feature.json`
3. Active feature `spec.md`
4. `DOUBTS.md`, `DECISIONS.md`, `EVIDENCE_LOG.md`
5. Related `plan/step_*.md`

## Steps

1. If no active feature, run `loop feature new "<title>"` or ask which feature to clarify.
2. List every open question from `spec.md` and step plan.
3. Reuse answers from `clarifications.md`, `DOUBTS.md`, `DECISIONS.md`, `SESSION_RECALL.md` - inform the user; do not re-ask.
4. Ask only blocking unknowns. Record the rest in `DOUBTS.md`.
5. Update `clarifications.md` with question / answer / source table.
6. Update `spec.md` open questions section - remove resolved items.
7. Log evidence-backed answers in `EVIDENCE_LOG.md` when needed.

## Output

- Updated `clarifications.md`
- Updated `spec.md`
- List of still-open questions (if any)

## Next phase

`spec-checklist` - quality-gate the spec before writing `feature-plan.md`.
