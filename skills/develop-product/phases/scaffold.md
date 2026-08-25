# Phase: Scaffold

> Loaded by `skills/develop-product/SKILL.md` when `BUILD PHASE: scaffold` - no product
> source tree exists yet. Load only this file.

## Purpose

Create the repo structure the plan calls for, so implementation has somewhere to land.

## Read First

1. `plan/BUILD_CONTEXT.md`
2. `plan/main_plan.md` -> **Tech Stack** and **Deployment & Infrastructure**
3. `DECISIONS.md` (stack, repo strategy)
4. `skills/implementation-planner/SKILL.md`
5. `skills/tool-orchestrator/SKILL.md`

## Process

1. **Reuse the decisions already made.** Stack, cloud, LLM and repo strategy are in
   `DECISIONS.md` and `plan/main_plan.md`. A sub-product inherits them through
   the shared `DECISIONS.md` and the scope's own plan - do not re-decide, and do not re-ask.
   **Never substitute a stack layer the plan left blank.** A `TBD` datastore is a planning
   gap: raise it as a doubt and stop, rather than scaffolding onto a local file database
   because it was the easy thing to start with.
2. **Scaffold only what the first task needs.** A monorepo skeleton, a package
   manifest, a test directory, a CI stub. Not features.
3. **Commit the lock file** - `prod-gap` treats a manifest without one as a P1.
4. **Add `.env.example`** rather than real values. Synthetic data only until
   `G-SENSITIVE-DATA` passes.

## Continue automatically

Scaffold in place -> continue straight into `phases/implement.md` in the same session.
Creating an empty repo and stopping is not a result.

## Output

Structure created, decisions reused (and from where), and the first task now unblocked.
