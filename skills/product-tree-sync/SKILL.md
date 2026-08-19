---
name: product-tree-sync
description: Syncs a main product and its sub-products from whichever folder the user is standing in - regenerates the roll-up and parent context, advances the parent watermark, and stages drift notes. Use when the user types /product-tree-sync, asks to sync main and sub products, says the main plan changed, or says a sub-product is out of date.
---

# Product Tree Sync

## Purpose

`/product-tree` **shows** the tree. This command **makes it current**.

A main product and its sub-products each hold their own workspace, and each only
regenerates its own view at its own `loop session-start`. So a sub-product could be
three sessions behind the master plan while the master plan's roll-up still described
the sub-product as it was last week. Closing that needed two different commands run in
two different folders, in the right order.

This is one command, run from either end.

## Read First

- `commands/product-tree-sync.md`
- `plan/SESSION_MANIFEST.md` (the `## Hierarchy` block)
- `plan/SUBPRODUCTS.md` (main) or `plan/PARENT_CONTEXT.md` (sub)
- `plan/PRODUCT_MAP.md`

## Scripts

```bash
loop workspace sync              # sync from here, both directions
loop workspace sync --no-stage   # report only
```

## What it does, by where it runs

| Standing in | Effect |
|-------------|--------|
| **Main product** | Re-scans for sub-products, re-binds map rows, rewrites `plan/SUBPRODUCTS.md`, runs every drift check, stages `error` and `parent-*` findings into the affected sub-products' `.loop/pending/` |
| **Sub-product** | Rewrites `plan/PARENT_CONTEXT.md` from the parent's current state, advances `.loop/parent-sync.json` (so upstream changes stop re-reporting once genuinely seen), then refreshes the parent's roll-up so the main product is no longer stale |
| **Standalone** | Says so and does nothing |

Both paths also refresh `plan/ULTRAPLAN_STATUS.md` and drop duplicate pending writes.

## Write policy (do not violate)

- **Generated reports** - `SUBPRODUCTS.md`, `PARENT_CONTEXT.md`, `ULTRAPLAN_STATUS.md` -
  are regenerated from either end. They are derived views; there is no authored content
  to lose, which is what makes the two-way refresh safe.
- **Authored state** - `DOUBTS.md`, `HANDOFF.md`, `DECISIONS.md`, the rest of `plan/` -
  is written only in its own workspace, never across one.
- **Staging originates from the main product only.** Syncing from a sub-product stages
  nothing.
- Anything staged is listed in `plan/SUBPRODUCTS.md` with its write id, and applied in
  the sub-product with `loop pending approve <id>`.

## Reading a finding

A finding says the master plan and a sub-product's plan disagree. It does **not** say
which is wrong:

- Sub-product wrong → approve the staged note there.
- Master plan wrong → fix it in the main workspace, run `loop workspace sync` again, and
  reject the stale note in the sub-product.

## Closeout

Report which workspace was synced, whether the other end was refreshed, findings by
level, what was staged where, and the next command. Do not "fix" a sub-product by
editing its files from the main workspace.
