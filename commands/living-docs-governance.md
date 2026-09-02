# /living-docs-governance

Detect drift between documentation (CLAUDE.md, ADRs, READMEs, API specs,
runbooks) and the actual code. Use when docs feel stale, when an audit reveals
drift, or as a scheduled `/prod-gap` companion.

## How To Interpret

If the user says `/living-docs-governance`, `docs drift check`, `are the docs
current`, or asks whether the documentation matches the code, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/living-docs-governance/SKILL.md`
3. `CLAUDE.md`, `AGENTS.md`, `docs/adr/*.md`, `docs/*.md`, `README.md`,
   `docs/CONTRIBUTING.md`, `docs/api/*.md`, `docs/runbook/*.md`

## Loop

```text
DISCOVER DOC SURFACE -> RUN DETERMINISTIC CHECKS -> EMIT DRIFT REPORT -> FILE TASKS OR DOUBTS
```

## Output

- `plan/DOCS_DRIFT/<timestamp>.md` (the report)
- High-severity findings filed as tasks in `TASKS.yml` (if a `/plan-loop` or
  `/develop-product` is active) or as doubts in `DOUBTS.md`.

## Continuation

The drift report is a task list. The tasks must close before the next release.
A drift report that never closes is a backlog of lies.