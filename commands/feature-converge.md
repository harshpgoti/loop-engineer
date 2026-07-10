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

- `/product-develop` closeout (before session-end)
- `/loop-engine` development phase closeout

## Output

`converge-report.md` and handoff next task.
