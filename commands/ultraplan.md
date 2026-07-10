# /ultraplan

Deep per-step planning for **platform-scale** products (multiple sub-products / AI agents).

## How To Interpret

If scale is `platform` in `plan/PLAN_SCALE.md`, or the user describes multiple agents/sub-products, execute this file and `skills/ultraplan/SKILL.md`.

## Scripts

```bash
loop plan scale --write
loop plan modules "Agent A" "Portal B" --types agent product
loop plan decompose
loop plan ultraplan next
loop plan ultraplan status
```

## Wired From

- `/plan` when `plan/PLAN_SCALE.md` says `platform`
- `/loop-engine` planning branch when ultraplan incomplete

## Output

One fully detailed step pack under `plan/steps/NN-slug/` per session.
