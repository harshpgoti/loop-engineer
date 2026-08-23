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

**Terminus: both ends agree and every finding it surfaced has been put to the user.**

Syncing produces findings, and a finding is a question with a recommended answer
already attached. Printing them and naming a command to go run is stopping halfway
through the job - the questions are the job.

So when the sync reports drift, raise it here, in this session:

```bash
loop findings ask                                    # each one, with its recommendation
loop findings resolve <id> accepted --note "<what changed>"
loop findings resolve <id> declined --note "<why the master plan is wrong>"
loop findings resolve <id> deferred --note "<when this gets decided>"
```

Accepting one usually means an edit here - make it, then re-sync so both ends agree
on the result. `skills/plan-loop/phases/parent-findings.md` has the full treatment.

**Stop Condition:** a finding whose answer changes product direction and only the user
can settle. Name it, give your recommendation, and stop there - do not guess, and do not
hand back a command list instead of the question. See `docs/CONTINUATION.md`.

## Output

Return:

1. Which workspace was synced, its role, and whether the other end was refreshed too
2. Drift findings by level, and what each means
3. What was staged into which sub-product, and the command to apply it there
4. Each finding raised, and the answer recorded for it
