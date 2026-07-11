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

## Output

One fully detailed step pack under `plan/steps/NN-slug/` per session.
