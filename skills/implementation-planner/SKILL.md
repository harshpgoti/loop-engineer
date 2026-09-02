---
name: implementation-planner
description: Plans implementation like a senior engineer before coding: reads the active task, identifies files/modules, risks, tests, rollout, and rollback. Use inside /develop-product before editing code.
---

# Implementation Planner

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Prevent sloppy implementation by planning the smallest safe diff.

## Required Reads

- `TASKS.yml`
- `GATES.yml`
- active `plan/step_*.md`
- `DECISIONS.md`
- `CONTEXT.md` - the repo's own names for things; use them
- `skills/codebase-design/SKILL.md` - module, interface, depth, seam, adapter
- product repo structure

## Planning Checklist

- What behavior changes?
- What files/modules are likely touched?
- **Which seam does this change sit behind, and which seam do its tests observe from?**
  Prefer an existing seam to a new one, and the highest one that reaches the behaviour. Name
  them before writing a test (`skills/tdd/SKILL.md`).
- Multi-step task? Decide sequential vs parallel with
  `skills/parallel-execution-optimizer/SKILL.md` before committing to the plan.
- If frontend motion/3D signals exist: run `python scripts/frontend_skill_router.py --write` and read `plan/AUTO_SKILLS.md`
- What data model or API contracts change?
- What tests must be added or updated?
- What security/risk checks apply?
- What docs must change?
- What rollback path exists?

## Output

Before coding, write a short implementation plan:

- task id
- intended files
- acceptance criteria
- the seams the tests observe from
- test plan
- risks
- rollback/handoff notes

Then implement only that scope.


## Stop Conditions and Rollback

A mutating skill declares when to halt and how to revert, before it runs. This section
is required by the canonical skill contract (`docs/SKILL_CONTRACT.md` "Risk and approval")
and is the E3 pattern adopted in round 4.

### When to stop

- **Three failed attempts at the same step.** Retrying past three means the
  hypothesis is wrong, not the execution. Stop, record what was tried, and
  escalate to the user as a doubt.
- **A change introduces more errors than it resolves.** Net negative progress
  is a regression, not a fix. Revert the change; record the failure mode.
- **A gate fails that the plan said must pass.** A gate is a contract; a
  failing gate is the chain telling you the work is not done. Stop and resolve.
- **The active task's `acceptance` criteria become unreachable** because of
  upstream changes. The plan is no longer valid; the task needs re-design,
  not more attempts.
- **Cost drift outside the budget.** A skill that consumes tokens or dollars
  unboundedly is a runaway; stop and report.

### When to escalate to the user

- **High-risk external actions** (publish, deploy, spend, destructive,
  privileged) require explicit user approval per `AGENTS.md` #5. The skill
  prepares the change, names the risk, and waits.
- **A blocker that is human-owned.** The blocker is a question only the
  user can answer (a stakeholder's call, a missing credential, a sign-off).
  Record it in `DOUBTS.md` and `HANDOFF.md`; do not invent an answer.
- **A goal-direction change.** The plan no longer matches what the user
  wants. The chain halts; the user re-plans.

### Rollback path

- **A single-task rollback** is `git revert <task-sha>` (or `git restore` for
  staged-only changes) followed by re-running the active feature's
  `converge-report` to confirm the rollback did not regress the rest of
  the build.
- **A multi-task rollback** is a feature-level revert: identify the feature
  commit range from `.loop/active-feature.json`, revert the range, then run
  `feature-converge` to confirm the surface is clean.
- **A state-only rollback** (files, configs, but no code) is a `git restore
  <path>` + `git clean -fd <path>` for the recorded paths. The skill's
  output records which paths it touched; the rollback reverses exactly
  those.
- **A data-only rollback** is database- and tenant-scoped; record the
  affected rows in the change record, run the inverse migration, and
  verify the diff matches the change record before declaring done.
- **A deploy rollback** is the prior version's artifact promoted through
  the same path the deploy took; `cicd-release/SKILL.md` carries the
  per-deploy rollback procedure.

A rollback that cannot be performed in one step is a planning problem.
Stop and re-plan; do not chain partial rollbacks.
