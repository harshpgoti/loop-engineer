# Phase: Hierarchy Reconcile

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: hierarchy` - the master plan and one
> or more sub-product plans contradict each other. Reconcile before deeper planning, or
> the rest of this loop plans on top of a claim a sub-product has already broken.

## Purpose

A main product workspace links sub-product workspaces that are planned and built on
their own. This phase makes the master plan and those sub-product plans agree again -
by fixing whichever of the two is actually wrong.

## Required Reads

- `plan/SUBPRODUCTS.md` (the roll-up and findings - regenerated at session start)
- `plan/PRODUCT_MAP.md`
- `plan/main_plan.md` → **Deployment & Infrastructure**
- `DECISIONS.md`
- `DOUBTS.md`

Refresh first if the roll-up looks stale:

```bash
loop workspace refresh
```

## Process

1. **Read the findings**, worst level first. Each one names a sub-product, a kind, and
   the two values that disagree.
2. **For every `error` finding, decide which side is wrong** - with the user when it is
   a product decision, from evidence when it is a fact:

   | Finding | Master plan is wrong when… | Sub-product is wrong when… |
   |---------|---------------------------|----------------------------|
   | `decision-conflict` / `deployment-conflict` | the sub-product has a real constraint the platform decision ignored | the sub-product decided locally without checking the platform decision |
   | `contract-gap` | the parent's `integrations.md` describes a contract that is no longer real | the sub-product simply has not planned the contract yet |
   | `unmapped-sub` | (almost always) the map is missing a row for real work | the folder is not a sub-product at all - unpin with `loop workspace role standalone` there |
   | `missing-link` | the link is stale after a move or rename | - |

3. **Master plan wrong** → fix it here: update `plan/main_plan.md`, `plan/PRODUCT_MAP.md`,
   or `DECISIONS.md`, record the change in `DECISIONS.md`, then `loop workspace refresh`.
   The finding disappears; tell the user to run `loop pending reject --all` in the
   sub-product to drop the now-wrong staged note.
4. **Sub-product wrong** → the note is already staged in that sub-product's
   `.loop/pending/`. Do **not** edit its files from here. Tell the user the exact
   command: `cd <sub-product> && loop pending approve --all`, and that its next
   `/plan-loop` picks the note up from its `DOUBTS.md`.
5. **Cannot decide without the user** → add the question to this workspace's `DOUBTS.md`
   with both values and what each choice costs.
6. **Warnings** (`unbuilt-row`, `uninitialized-sub`, `dependency-gap`): record them as
   planned work - a map row with no workspace is the next sub-product to start, not an
   error.
7. **Re-run** `loop workspace refresh` and confirm the `error` count is zero, or that
   every remaining one is now an open doubt with a named owner.

## Rules

- **Never edit a sub-product's plan files from the main workspace.** Metadata is stamped;
  product state is staged. That boundary is what keeps a main-level run from silently
  rewriting plans in folders the user was not working in.
- A finding is a *disagreement*, not a verdict. Do not assume the master plan wins.
- Do not delete a finding by weakening the master plan just to make it quiet - if a
  platform decision no longer holds, say so in `DECISIONS.md`.

## Output

- Findings resolved, and which side changed for each
- Master-plan files updated
- Notes staged per sub-product, with the approve command for each
- New open doubts raised
- Remaining `error` count after refresh

## Continue automatically

Execute the branch - do not report it and stop:

- **Errors cleared** → continue the pipeline: load `phases/council.md` (or
  `phases/ultraplan.md` when `plan/PLAN_SCALE.md` is platform and a step is incomplete).
- **A finding needs a user decision** → that is a Stop Condition. Name the finding, the
  two values, and what you need. See `docs/CONTINUATION.md`.
