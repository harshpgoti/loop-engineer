# /feature-new

Create a numbered feature spec folder and set it as the active feature.

## How To Interpret

If the user says `/feature-new`, `feature new`, or planning needs a buildable feature slice, execute this file.

## Required Reads

1. `skills/feature-workflow/SKILL.md`
2. `plan/main_plan.md`
3. Active `plan/step_*.md` (if any)

## Script

```bash
loop feature new "<title>" --step plan/step_XX_<name>.md
loop feature list
```

## Steps

1. Infer title from current step plan or user message.
2. Run `loop feature new` with `--step` pointing at the related step file.
3. Fill `spec.md` from PRD / step plan content — do not duplicate entire step plan; link and summarize.
4. Tell user next steps: `/spec-clarify` → `/spec-checklist` → feature-plan → task-compiler.

## Wired From

- `/plan` step 14–15 (after step plan, before task-compiler)
- `/loop-engine` when entering planning for a new module

## Output

- `plan/features/NNN-slug/`
- `.loop/active-feature.json`
