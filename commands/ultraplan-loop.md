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

When the user names an existing step, target it explicitly instead of accepting the
tracker's default:

```bash
loop plan-loop ultraplan next --step "<step id or exact title>"
```

Rows bound to `plan/products/<slug>` (by `scope.json` map id or plan path), or to an
external `Workspace`, are planned by that owner and excluded from the root tracker.
Deferred rows are excluded until promoted.

## Wired From

- `/plan-loop` when `plan/PLAN_SCALE.md` says `platform`
- `/loop-engine` planning branch when ultraplan incomplete

## Continuation

Terminus: **the active step is fully planned: pack complete, feature spec ready,
blocking doubts resolved or explicitly deferred, tasks compiled, and a go/no-go recorded.**
After filling the pack, continue automatically through `/spec-clarify`, `/spec-checklist`,
`/resolve-doubts`, and task compilation. Do not stop and list those for the user.

**One fully planned step per session is a deliberate context Stop Condition**, not
chunking: after its pack, spec and tasks are complete, report progress
(`plan/ULTRAPLAN_STATUS.md`), run `/compact-loop`, and continue the next step in a
fresh session. See `docs/CONTINUATION.md`.

## Output

One fully detailed step pack under `plan/steps/NN-slug/`, a ready feature spec,
compiled tasks, a go/no-go, and `plan/ULTRAPLAN_STATUS.md` showing what remains.
