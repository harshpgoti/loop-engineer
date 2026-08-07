# /ultraplan-loop

Deep per-step planning for **platform-scale** products (multiple sub-products / AI agents).

## How To Interpret

If scale is `platform` in `plan/PLAN_SCALE.md`, or the user describes multiple agents/sub-products, execute this file and `skills/plan-loop/phases/ultraplan.md`.

## Scripts

```bash
loop plan-loop scale --write
loop plan-loop modules "Agent A" "Portal B" --types agent product
loop plan-loop decompose
loop plan-loop ultraplan next
loop plan-loop ultraplan status
```

## Wired From

- `/plan-loop` when `plan/PLAN_SCALE.md` says `platform`
- `/loop-engine` planning branch when ultraplan incomplete

## Continuation

Terminus: **the active step's pack complete, its feature spec created and clarified.**
After filling the pack, create the feature spec and continue into `/spec-clarify` -
do not stop and list those for the user.

**One step per session is a deliberate context Stop Condition**, not chunking:
ultraplan packs are large, so after finishing one step's pack and spec, report
progress (`plan/ULTRAPLAN_STATUS.md`), run `/compact-loop`, and continue the next
step in a fresh session. See `docs/CONTINUATION.md`.

## Output

One fully detailed step pack under `plan/steps/NN-slug/`, its feature spec
clarified, and `plan/ULTRAPLAN_STATUS.md` showing what remains.
