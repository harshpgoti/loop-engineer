---
name: feature-workflow
description: Routes feature spec folders under plan/features - create, clarify, checklist, compile tasks, develop, converge. Wired into /plan-loop and /develop-product.
---

# Feature Workflow

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Build one feature at a time with a durable spec folder. This is Loop Engineer's built-in spec-driven path - not a vendored external tool.

## Layout

```text
plan/features/001-slug/
  spec.md
  clarifications.md
  feature-plan.md
  tasks.md
  research.md
  spec-checklist.md
  converge-report.md
  contracts/
.loop/active-feature.json   # pointer to active feature
```

## Commands

| Command | When |
|---------|------|
| `/feature-new` | New buildable feature during `/plan-loop` |
| `/spec-clarify` | Resolve open questions before feature-plan |
| `/spec-checklist` | Quality gate before task compile |
| `/feature-converge` | After dev slices - drift vs spec/tasks |

## Scripts

```bash
loop feature new "auth login" --step plan/step_01_auth.md
loop feature list
loop feature converge
```

## Wiring (required)

- **`/plan-loop`:** After step plan, run `loop feature new` (or update active feature `spec.md`).
- **`task-compiler`:** Write `tasks.md` in active feature; sync ids to `TASKS.yml`.
- **`/develop-product`:** Read active feature `tasks.md` and `feature-plan.md`.
- **`session-start`:** Manifest includes active feature artifacts.
- **`session-end`:** Run `loop feature converge` when implementation changed.

## Read First

1. `.loop/active-feature.json`
2. Active feature `spec.md`
3. `plan/main_plan.md` and related `plan/step_*.md`

## Output

- Numbered feature folder
- Active feature pointer
- No duplicate task sources - `tasks.md` is human view; `TASKS.yml` is machine sync


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
