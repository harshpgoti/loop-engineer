# /feature-converge

Check active feature spec/plan/tasks against implementation and TASKS.yml.

## How To Interpret

If the user says `/feature-converge`, execute this file and `skills/feature-converge/SKILL.md`.

## Script

```bash
loop feature converge
```

## Required Reads

1. `skills/feature-converge/SKILL.md`
2. Active feature folder
3. `TASKS.yml`, `HANDOFF.md`

## Wired From

- `/develop-product` closeout (before session-end)
- `/loop-engine` development phase closeout

## Continuation

Terminus: **drift resolved or captured.** Detecting drift is not the deliverable -
for each item, either fix it now (when it is a small, safe reconciliation) or write
a `TASKS.yml` entry describing the rework. Do not hand the user a drift list with
nothing tracking it. See `docs/CONTINUATION.md`.

## Output

`converge-report.md`, the drift items fixed or the task IDs created for them, and
the next task.
