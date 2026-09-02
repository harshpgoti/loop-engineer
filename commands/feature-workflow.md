# /feature-workflow

Run the spec-driven per-feature pipeline: spec -> clarify -> checklist -> feature
plan -> task compiler. The skill is wired into the chain; this command is
for direct invocation when the user wants a focused feature pass.

## How To Interpret

If the user says `/feature-workflow`, `run the feature pipeline`, `spec the
feature`, or asks to drive a single feature through the workflow, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/feature-workflow/SKILL.md`
3. `plan/features/<id>/spec.md` (when present)
4. `.loop/active-feature.json` (when present)
5. `TASKS.yml`, `GATES.yml`

## Loop

```text
DETECT active feature -> LOAD phase files -> RUN clarify -> RUN checklist -> WRITE feature-plan.md -> COMPILE tasks -> SYNC with TASKS.yml
```

## Output

- `plan/features/<id>/spec.md` (clarified)
- `plan/features/<id>/feature-plan.md` (locked)
- `plan/features/<id>/tasks.md` (compiled)
- `TASKS.yml` updated
- Gate status for the feature

## Continuation

After `/feature-workflow`, the chain continues with `/develop-product`
to build the feature, or with `/feature-converge` to drift-check an
already-built feature. The active-feature pointer (`.loop/active-feature.json`)
is set to the just-worked feature so subsequent commands can find it.