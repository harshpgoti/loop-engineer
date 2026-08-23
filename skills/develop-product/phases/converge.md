# Phase: Converge

> Loaded by `skills/develop-product/SKILL.md` when `BUILD PHASE: converge` - the code is
> written and needs to be checked against what was specified. Load only this file.

## Purpose

Confirm what was built is what was planned, and close the loop on the task.

## Read First

1. `plan/BUILD_CONTEXT.md`
2. `skills/feature-converge/SKILL.md`
3. `skills/code-reviewer/SKILL.md`
4. Active feature: `spec.md`, `feature-plan.md`, `tasks.md`

## Process

1. **Run the drift check**: `loop feature converge`. It compares the active feature's
   spec and tasks against what is actually implemented and against `TASKS.yml`.
2. **Review the diff** with `skills/code-reviewer/SKILL.md` - correctness first, then
   reuse and simplification.
3. **Reconcile every gap it finds**, in this session:

   | Gap | Action |
   |-----|--------|
   | Spec says something the code does not do | Implement it, or record why the spec changed |
   | Code does something the spec never asked for | Add it to the spec, or remove it |
   | `TASKS.yml` says done, nothing was built | Reopen the task |

4. **Move the gate.** If the task's gate criteria are now genuinely met, set its
   `status` in `GATES.yml` with a one-line `note:` of what satisfied it. Never mark a
   gate passed on unmet criteria.
5. **Update `HANDOFF.md`** with what changed and what is next.

## Continue automatically

- **Converged, gate moved, tasks remain** -> continue: pick up the next task rather than
  ending the turn.
- **Converged and nothing is left, and the product has eval cases** -> continue into
  `skills/eval-loop/SKILL.md` first. Agent behaviour changes are invisible to unit tests,
  so the score has to move before release, not after.
- **Converged and nothing is left** -> continue into `phases/release.md`.
- **A gap needs a product decision** -> Stop Condition, named.

## Output

Convergence result, review findings and what was done about each, gate movement, and
the next task or phase.
