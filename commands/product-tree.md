# /product-tree

Show how this product workspace relates to the others: its role (main product, sub-product, or standalone), every linked sub-product's plan state, and where the master plan and a sub-product's plan disagree.

## How To Interpret

If the user says `/product-tree`, `product tree`, `show sub products`, `how do my products link`, `is my sub product plan aligned`, or asks why a sub-product's plan differs from the main plan, execute this file directly.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read and write product-state files in the **active workspace** (local `.loop-engineer/` auto-detected from cwd). Sub-product workspaces are **read-only** from here.

1. `AGENTS.md`
2. `skills/product-tree/SKILL.md`
3. `plan/SESSION_MANIFEST.md`
4. `plan/SUBPRODUCTS.md` (main product) or `plan/PARENT_CONTEXT.md` (sub-product)
5. `plan/PRODUCT_MAP.md`
6. `plan/main_plan.md`
7. `DECISIONS.md`
8. `DOUBTS.md`

## Loop

```text
SESSION-START -> REFRESH TREE -> READ ROLL-UP -> EXPLAIN DRIFT -> RECOMMEND NEXT COMMAND
```

## Scripts

```bash
loop workspace tree                 # role, parent, sub-products
loop workspace refresh              # rewrite the roll-up / parent context and stage drift notes
loop workspace refresh --no-stage   # report only, stage nothing
loop workspace link ../billing      # sub-product outside the main folder
loop workspace unlink billing
loop workspace role main            # pin a role instead of auto-detecting
```

## Rules

- **Read-only across workspaces.** Never edit a sub-product's plan files from the main
  workspace. Corrections are staged into that sub-product's `.loop/pending/` and applied
  there with `loop pending approve --all`.
- Sub-products are discovered by scanning folders under the main product folder. Use
  `loop workspace link` only for sub-products that live somewhere else.
- Every sub-product should bind to a `plan/PRODUCT_MAP.md` row. An unmapped sub-product
  is work the master plan cannot account for - fix the map, not the report.

## Continuation

**Read-only - deliberately does not cascade.** Reporting the tree and naming the next
command *is* this command's product - it is read-only by design, so it reports rather
than resolves. When drift needs resolving, hand off to
`/resolve-doubts` (this workspace) or `/plan-loop` (to correct the master plan). See the
read-only exemption in `docs/CONTINUATION.md`.

## Output

Return:

1. Role of the current workspace (main / sub / standalone) and its parent, if any - plus any sub-products held as **scopes** in this workspace (`loop scope list`), which have no workspace of their own
2. Sub-product table: map row, plan status, gate, tasks, open doubts, last session
3. Drift findings by level, and what each one means for the master plan
4. What was staged into which sub-product, and the command to apply it there
5. Next recommended command
