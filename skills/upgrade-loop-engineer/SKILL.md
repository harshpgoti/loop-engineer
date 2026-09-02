---
name: upgrade-loop-engineer
description: Safely upgrades Loop Engineering OS while preserving product plans, memory, tasks, gates, evidence, decisions, handoffs, compact summaries, and product docs. Use when the user types /upgrade-loop-engineer or asks how to update the tool without losing data.
---

# Upgrade Loop Engineer

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Update reusable loop-engineering files without overwriting user product state.

## Read First

- `commands/upgrade-loop-engineer.md`
- `docs/UPGRADE.md`
- `memories/MEMORY.md`
- `HANDOFF.md`
- `COMPACT.md`

## Protected Product-State Files

Never overwrite:

- `plan/main_plan.md`
- `plan/`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `TASKS.yml`
- `GATES.yml`
- `HANDOFF.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `EVIDENCE_LOG.md`
- `COMPACT.md`
- `.ai/`
- `docs/`

## Safe Process

1. Run or recommend `/compact-loop` first.
2. Identify setup:
   - separate `loop-engineer/` and `product/`
   - embedded copy inside product repo
3. For separate setup, update only `loop-engineer/`.
4. For embedded setup, run `scripts/upgrade_loop_engineer.py` dry-run first.
5. Apply only after dry-run confirms protected files are untouched.
6. Run `scripts/migrate_workspace.py` on the product workspace.
7. Run validators, then `/doctor` and `/status`.
8. Update `memories/MEMORY.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.

## Output

- Detected setup
- Protected files status
- Files to update
- Backup location
- Validation result
- Next command


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
