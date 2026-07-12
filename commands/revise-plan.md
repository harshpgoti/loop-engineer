# /revise-plan

Apply a free-form correction or addition to a plan that already exists - the user talks, the
agent decides which file to edit because it always loads full plan context first.

## How To Interpret

If the user says `/revise-plan <text>`, execute this file and `skills/revise-plan/SKILL.md`.

Also treat plain language as this command whenever `plan/main_plan.md` is already past
`Status: INITIALIZED` and the user says something that reads as a correction or addition
rather than a new planning session - e.g. "actually the target user is X, not Y", "correct
the plan", "I forgot to mention...", "add a note that...", "update the plan with...". Do not
make the user type the slash command explicitly.

## Required Reads

Full plan context, always all of it - no progressive disclosure. See
`skills/revise-plan/SKILL.md` -> Required Reads for the exact list
(`plan/main_plan.md`, all `plan/step_*.md`, active feature folder, `DECISIONS.md`,
`DOUBTS.md`, `TASKS.yml`, `GATES.yml`, `DEPLOYMENT_PLAN.md`, `CURRENT_STATE.md`,
`HANDOFF.md`).

## Wired From

- Any time after `/plan-loop` has produced an initialized `plan/main_plan.md` and the user
  wants to correct or add a detail rather than run through grill/spec-clarify again.
- `/status`, `/doctor`, and `/sync-loop-state` may point here when they detect a stale gate
  or a contradiction between plan files.

## Loop

```text
READ FULL PLAN CONTEXT -> PARSE STATEMENT INTO FACTS -> ROUTE EACH FACT TO ITS FILE
-> CHECK GATE/BUILD LOCK -> APPLY EDIT(S) -> LOG DECISIONS.md -> UPDATE TASKS.yml IF NEEDED
-> UPDATE HANDOFF/MEMORY
```

## Output

1. Which fact(s) changed and in which file(s)
2. Any `GATES.yml` entry reopened / moved back to `blocked`
3. Any new/updated `TASKS.yml` entries created by this revision, with IDs
4. Any `DOUBTS.md` entry resolved
5. What still needs doing to reconcile already-built work with the revised plan
6. Next command
