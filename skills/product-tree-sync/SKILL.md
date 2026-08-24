---
name: product-tree-sync
description: Syncs a main product and its sub-products from whichever folder the user is standing in - regenerates the roll-up and parent context, advances the parent watermark, and stages drift notes. Use when the user types /product-tree-sync, asks to sync main and sub products, says the main plan changed, or says a sub-product is out of date.
---

# Product Tree Sync

## Purpose

`/product-tree` **shows** the tree. Session lifecycle already keeps it current; this
command forces an explicit mid-session refresh when the user asks for one.

A main product and its sub-products each hold their own authored workspace. The shared
lifecycle calls this same synchronization seam from either end, while this command exposes
it directly for diagnosis.

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
| **Main product** | Re-scans for sub-products, re-binds map rows, rewrites `plan/SUBPRODUCTS.md`, runs every drift check, and refreshes every linked child's generated `PARENT_CONTEXT.md` |
| **Sub-product** | Rewrites `plan/PARENT_CONTEXT.md` from the parent's current state, advances `.loop/parent-sync.json` (so upstream changes stop re-reporting once genuinely seen), then refreshes the parent's roll-up so the main product is no longer stale |
| **Standalone** | Says so and does nothing |

Both paths also refresh `plan/ULTRAPLAN_STATUS.md` and drop duplicate pending writes.

## Write policy (do not violate)

- **Generated reports** - `SUBPRODUCTS.md`, `PARENT_CONTEXT.md`, `ULTRAPLAN_STATUS.md` -
  are regenerated from either end. They are derived views; there is no authored content
  to lose, which is what makes the two-way refresh safe.
- **Authored state** - `DOUBTS.md`, `HANDOFF.md`, `DECISIONS.md`, the rest of `plan/` -
  is written only in its own workspace, never across one.
- **Findings are derived, not staged.** Each sub-product owns its resolution log and
  authored plan changes.

## Reading a finding

A finding says the master plan and a sub-product's plan disagree. It does **not** say
which is wrong:

- Sub-product wrong → accept the finding there and materialize it in the local plan/tasks.
- Master plan wrong → decline the finding there and fix the main workspace with
  `/revise-plan`; lifecycle re-syncs both ends.

## Closeout

Report which workspace was synced, whether the other end was refreshed, and findings by
level. Do not "fix" authored sub-product state from the main workspace.
