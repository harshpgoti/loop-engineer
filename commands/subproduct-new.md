# /subproduct-new

Carve a product-map row out of the main product into its own sub-product workspace,
ready for `/loop-engine`.

## How To Interpret

If the user says `/subproduct-new`, `/subproduct-new 17 18`, `make row 17 a sub-product`,
`split module 12 out into its own folder`, `I want to work on rows 17 and 18`, or names
map rows they want built separately, execute this file directly.

Run it **from the main product workspace** - it reads `plan/PRODUCT_MAP.md` there.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone).
Read and write product-state files in the **active workspace**.

1. `AGENTS.md`
2. `skills/subproduct-new/SKILL.md`
3. `plan/PRODUCT_MAP.md` - the rows, their type, and their status
4. `DECISIONS.md` - a row deferred by a recorded decision is not one to build

## Scripts

```bash
loop subproduct list            # rows typed sub-product; READY vs later, and why
loop subproduct new 17 18       # carve those rows out
loop subproduct new 17 --dry-run
```

## Loop

```text
SESSION-START -> LIST ROWS -> CONFIRM WHICH -> CREATE -> REPORT TASK OVERLAP -> HAND OVER TO /loop-engine
```

## Rules

- **Only a row typed `sub-product`.** A `module` is planned and built inside the main
  product; retyping the row is a plan decision, not something this command does for you.
- **The folder name comes from the row title.** `map_id` binds by exact slug match, so a
  hand-picked folder name is how a row ends up silently unbound. Never rename it after.
- **A `later` row is a warning, not a blocker.** The plan says it has not started;
  carving it out now creates an empty workspace to keep in sync. Say so and confirm.
- **Check `DECISIONS.md` before carving a deferred row.** If a decision parked it, building
  it contradicts a call the user already made - raise that before doing anything.
- **Tasks are reported, never moved.** The command lists the main-product tasks carrying
  the gate the row declares. Retiring or retargeting them is the user's edit, after the
  new workspace has compiled its own.

## Continuation

Created → tell the user the exact `cd` and that `/loop-engine` is next. Do not start
building in the new workspace from this command; it is a different workspace and a
different session.

Nothing created → say which row was refused and why. A refusal here is always a plan
problem (wrong type, already built, deferred by decision), not a tool problem.

## Output

1. Each row: created or refused, with the reason
2. Where its plan came from
3. Main-product tasks that now belong to it, and the gate that says so
4. The `cd` and the next command
