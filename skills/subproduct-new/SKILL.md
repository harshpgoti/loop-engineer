---
name: subproduct-new
description: Carve a product-map row out of the main product into its own sub-product workspace, seeded from the row's step plan and linked by map id. Use for /subproduct-new, or when the user wants a map row built in its own folder.
---

# Sub-product New

Turn a `plan/PRODUCT_MAP.md` row into a workspace that can run its own `/loop-engine`.

## Why this is a command and not five steps

By hand it is `mkdir`, `loop setup --role sub --parent ..`, copy the step plan across,
`loop workspace refresh`, then `/loop-engine`. Two of those fail quietly:

- **The folder name is load-bearing.** `map_id` binds by exact slug match of folder name
  to the row's title. A folder named `patient-engagement` instead of
  `Patient Engagement And Rebooking Agent` binds to nothing, and the row stays unbuilt
  while looking built.
- **The plan handover is a manual copy.** Skip it and the new workspace starts from the
  blank template and re-plans a row the main product already planned in full.

Deriving both from the row removes both failure modes.

## Process

1. `loop subproduct list` - every row typed `sub-product`, marked `READY` or `later`.
2. Read the row's status against `DECISIONS.md`. A row parked by a decision is not one to
   build; raise it rather than carving it out.
3. Confirm the rows with the user when more than one is `later`, or when any row's status
   disagrees with what they asked for.
4. `loop subproduct new <rows>` - per row it seeds the starter files, hands over
   `plan/step_<id>_*.md` as the new `plan/main_plan.md`, links it by `map_id`, and
   refreshes both ends of the hierarchy.
5. Report the task overlap, then hand off: `cd` into the folder, run `/loop-engine`.

## What it will not do

**Move the main product's tasks.** Which of them belong to a row is not reliably
derivable: a `# ===== STEP 18 =====` banner has nothing that closes it, and a step plan
mentions every gate it *depends* on as well as the one it owns. Both over-claim, and a
wrong move deletes real work.

So attribution comes from what the row **declares** - the gate named in its Status or
Scope - and the result is printed, not applied. The new workspace compiles its own tasks
from the plan it inherited, which is the normal path; retiring the main product's copies
is a deliberate edit afterwards.

## It stops at the workspace

This command does **not** run `/loop-engine`. It prints the `cd` and the next command and
stops there, because the build belongs to a different workspace and a different session:
the new workspace has its own manifest, its own recall, its own gates, and `loop
session-start` has to run inside it. Chaining straight into a build would skip all of that
and build the new product using the main product's session state.

So: carve the rows out here, then move.

## Reading the list

| Mark | Meaning |
|------|---------|
| `READY` | Typed `sub-product`, not dormant, nothing blocking. Carve it out |
| `later` | The plan says it has not started. Possible, but it creates an empty workspace to keep in sync |
| (blank) | Blocked - the reason is printed beneath it |
