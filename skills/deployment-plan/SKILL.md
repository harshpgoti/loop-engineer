---
name: deployment-plan
description: Writes or refreshes DEPLOYMENT_PLAN.md at loop closeout, reusing prior cloud, LLM, and deployment decisions from plan/main_plan.md, DECISIONS.md, and DOUBTS.md. Use when /plan-loop, /develop-product, or /loop-engine completes, or when deployment planning is needed.
---

# Deployment Plan

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Produce a durable deployment plan when planning or development loops complete. Reuse decisions already captured in `plan/main_plan.md` and planning files. Ask the user only for unresolved deployment choices.

## When To Run

- At closeout of `/plan-loop` once deployment choices are captured or marked TBD
- At closeout of `/develop-product`
- At closeout of `/loop-engine`
- After `/release-check` when preparing production launch
- When the user asks for deployment planning

## Read First

- `plan/main_plan.md`
- `DECISIONS.md`
- `DOUBTS.md`
- `memories/MEMORY.md`
- `plan/PROD-GAP.md`
- `RELEASE_CHECK.md`
- relevant `plan/step_*.md`

## Write

- `DEPLOYMENT_PLAN.md`
- `DOUBTS.md` for unresolved deployment questions
- `HANDOFF.md`
- `.ai/SESSION_LOG.md`

## Questions To Resolve

Ask the user directly when unresolved:

- cloud provider
- single-cloud vs multi-cloud
- production region(s)
- compute model
- database hosting
- LLM provider and model(s)
- embedding provider/model
- agent runtime
- CI/CD platform
- secrets management

## Reuse Rule

If a question was already answered in `DECISIONS.md`, resolved `DOUBTS.md`, `plan/main_plan.md`, or step plans:

1. Reuse the same answer in `DEPLOYMENT_PLAN.md`
2. Mark it under **Confirmed Decisions (Reused)**
3. Inform the user which decisions were reused
4. Do not ask again unless the user wants to change it

## Optional Script

```bash
python scripts/deployment_plan.py --source plan
```

Custom workspace:

```bash
python scripts/deployment_plan.py --workspace ../product
```

Then refine the draft with product-specific infrastructure details.

## Closeout Behavior

1. Write or refresh `DEPLOYMENT_PLAN.md`
2. List reused decisions for user confirmation
3. Ask only unresolved deployment questions
4. Record unresolved items in `DOUBTS.md`
5. Mention deployment follow-ups in `HANDOFF.md`

## Output

- `DEPLOYMENT_PLAN.md` path
- Reused decisions count
- Open deployment questions
- User actions required


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
