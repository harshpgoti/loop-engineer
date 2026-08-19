# /product-tree-sync

Make the main product and its sub-products agree, run from **either** folder. One
command instead of remembering which `loop workspace ...` call belongs where.

## How To Interpret

If the user says `/product-tree-sync`, `sync my products`, `sync main and sub product`,
`sync the tree`, `my sub-product is out of date`, `the main plan changed`, or asks to
refresh the link between a main product and a sub-product, execute this file directly.

Use `/product-tree` instead when the user only wants to **see** the tree. This command
writes: it regenerates the reports, advances the sub-product's parent watermark, and
stages drift notes.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read
and write product-state files in the **active workspace** (local `.loop-engineer/`
auto-detected from cwd).

1. `AGENTS.md`
2. `skills/product-tree-sync/SKILL.md`
3. `plan/SESSION_MANIFEST.md`
4. `plan/SUBPRODUCTS.md` (main product) or `plan/PARENT_CONTEXT.md` (sub-product)
5. `plan/PRODUCT_MAP.md`

## Loop

```text
SESSION-START -> SYNC BOTH ENDS -> READ FINDINGS -> EXPLAIN -> RECOMMEND NEXT COMMAND
```

## Scripts

```bash
loop workspace sync              # the whole sync, from whichever folder you are in
loop workspace sync --no-stage   # report only, stage nothing
```

Run it from the folder the user is standing in. It works out the rest:

| Run from | What it does |
|----------|--------------|
| Main product | Re-scans sub-products, rewrites `plan/SUBPRODUCTS.md`, stages drift notes into each affected sub-product |
| Sub-product | Rewrites its `plan/PARENT_CONTEXT.md`, advances its parent watermark, **and** refreshes the parent's roll-up so the main product is no longer stale |

It also refreshes `plan/ULTRAPLAN_STATUS.md` and drops duplicate pending writes.

## Rules

- **Authored state never crosses a workspace.** Only generated reports
  (`SUBPRODUCTS.md`, `PARENT_CONTEXT.md`) are regenerated from either end. `DOUBTS.md`,
  `HANDOFF.md` and the rest of `plan/` are written only in their own workspace.
- **Staging originates from the main product only.** Syncing from a sub-product stages
  nothing, so a sub-product can never queue work into its siblings.
- A finding says the two plans disagree - **not which one is wrong**. Decide with the user.
- Never "fix" a sub-product by editing its files from the main workspace.

## Continuation

Writes reports, then stops. When drift needs resolving, hand off to `/resolve-doubts`
(this workspace), `/revise-plan` (correct this plan), or `/plan-loop` (correct the master
plan). See `docs/CONTINUATION.md`.

## Output

Return:

1. Which workspace was synced, its role, and whether the other end was refreshed too
2. Drift findings by level, and what each means
3. What was staged into which sub-product, and the command to apply it there
4. Next recommended command
