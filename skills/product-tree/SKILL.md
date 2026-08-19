---
name: product-tree
description: Shows how a main product workspace and its sub-product workspaces link together - each sub-product's plan state rolled up, and every place a sub-product's plan contradicts the master plan. Use when the user types /product-tree, asks about sub-products, splits a product into sub-products, or asks whether a sub-product's plan still matches the main plan.
---

# Product Tree

## Purpose

A product large enough to split gets split on disk: a main folder holding the master
plan, sub-product folders under it that are planned and built on their own. Each folder
has its own `.loop-engineer/` workspace, so by default neither end can see the other.

This skill closes that gap in both directions:

- **Main product** reads every sub-product's plan state into `plan/SUBPRODUCTS.md`.
- **Sub-product** reads the constraints it inherits into `plan/PARENT_CONTEXT.md`.

## Read First

- `commands/product-tree.md`
- `plan/SESSION_MANIFEST.md` (the `## Hierarchy` block)
- `plan/SUBPRODUCTS.md` (main) or `plan/PARENT_CONTEXT.md` (sub)
- `plan/PRODUCT_MAP.md`
- `plan/main_plan.md`, `DECISIONS.md`, `DOUBTS.md`

## Roles

| Role | Meaning |
|------|---------|
| `main` | Holds the master plan and links sub-product workspaces. Also a normal workspace - it may plan **and** build its own shared code |
| `sub` | A sub-product with its own plan, tasks, and gates; inherits the parent's decisions |
| `standalone` | No parent and no sub-products - the default, and unchanged from single-product behavior |

Roles are auto-detected: a workspace with discovered children becomes `main`, one whose
parent lists it becomes `sub`. A workspace can be both (a middle node keeps both links).
Pin a role with `loop workspace role <role>` when auto-detection is wrong.

## Discovery

Sub-product folders under the main folder are found by scan (depth 3, skipping
`node_modules`, `.git`, build output). A discovered sub-product is **not** descended
into - its own sub-products belong to it.

For a sub-product in another repo or elsewhere on disk:

```bash
loop workspace link ../billing --map-id 03
```

## Scripts

```bash
loop workspace tree                 # role, parent, sub-products
loop workspace refresh              # rewrite reports, stage drift notes
loop workspace refresh --no-stage   # report only
loop workspace unlink billing
```

`loop session-start` already runs the refresh - run these only to re-check mid-session.

## Drift checks (deterministic, not model-generated)

| Kind | Level | Fires when |
|------|-------|-----------|
| `decision-conflict` | error | Same topic decided differently in the parent's and the sub-product's `DECISIONS.md` |
| `deployment-conflict` | error | Same row of **Deployment & Infrastructure** differs between main plan and sub plan |
| `contract-gap` | error | Parent's `plan/steps/NN-slug/integrations.md` defines contracts with modules the sub-product's plan never mentions |
| `unmapped-sub` | error | A sub-product workspace has no `plan/PRODUCT_MAP.md` row |
| `missing-link` | error | A linked sub-product folder no longer exists |
| `unbuilt-row` | warn | A map row has no sub-product workspace |
| `uninitialized-sub` | warn | Sub-product exists but its `plan/main_plan.md` is UNINITIALIZED |
| `dependency-gap` | warn | Map says this sub-product depends on another; its plan never references it |
| `parent-added` | warn / error | Master plan gained a constraint this sub-product has never synced |
| `parent-changed` | warn / error | A synced constraint now has a different value upstream (both values reported) |
| `parent-removed` | warn / error | A constraint was dropped upstream and may still be honored here |
| `stale-sub` | info | Main plan changed after the sub-product's last session |

The three `parent-*` kinds answer "what changed upstream", which the conflict
checks cannot: they compare current values, so a *new* platform constraint
contradicts nothing. Each sub-product keeps a watermark of the parent surface it
last synced (`.loop/parent-sync.json`), the parent diffs against it, and the
sub-product advances it at its own `loop session-start`. Level rises to `error`
when the sub-product has an in-progress task in `TASKS.yml`. See
`docs/PRODUCT_HIERARCHY.md`.

## Write policy (do not violate)

- **Metadata** (`.loop/workspace.json`) may be written into a sub-product directly.
- **Product state** (`DOUBTS.md`, `HANDOFF.md`, `plan/*`) is **never** written across
  workspaces. `error` findings and every `parent-*` update are staged into the
  sub-product's `.loop/pending/`; the user decides there with `loop pending list`
  then `loop pending approve <id>`.
- Anything staged is listed in `plan/SUBPRODUCTS.md` with its write id.

## Reading a finding

A finding says the master plan and a sub-product's plan disagree - it does **not** say
which one is wrong. Decide with the user:

- The sub-product is wrong → the staged note in its `DOUBTS.md` is the correction.
- The master plan is wrong → fix it here (`/revise-plan` or `/plan-loop`), then
  `loop workspace refresh`; the finding disappears and the staged note can be rejected
  with `loop pending reject --all` in the sub-product.

## Closeout

Report the role, the sub-product table, findings by level, what was staged where, and
the next command. Do not "fix" a sub-product by editing its files from here.
