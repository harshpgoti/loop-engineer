---
name: develop-product
description: Runs product engineering from the approved plan: frontend, backend, database, agent loops, QA, auto-validation, docs, security, compliance, CI/CD, and deployment readiness. Use when the user types /develop-product or asks to start development.
---

# Product Develop

Inherits `docs/SKILL_CONTRACT.md`.

## Isolated execution runs

When a compiled task is deliberately delegated to a separate local coding-agent
process, use the internal `loop worker` bridge documented in
`docs/LOOP_EXECUTION_ARCHITECTURE_PLAN.md`. Prepare the run before launch, keep
all edits inside its recorded worktree, bind independent validation to the exact
candidate commit, and run cleanup only after its landed-work proof succeeds.
Ordinary single-agent development remains unchanged.

## Purpose

Build the product from `plan/main_plan.md` and `plan/` while respecting gates.

## Command

`/develop-product`

## Read First

> **Progressive disclosure - the one rule.** Read this file every development session.
> Load a **phase file** only when the harness selects it. This list used to hold 32
> entries, 27 of them unconditional, so a session that only needed to write a test
> still pulled in the agent-builder, deployment-plan and security-compliance skills.

Always:

1. `plan/SESSION_MANIFEST.md` (after `loop session-start`) - get the **`BUILD PHASE:`** line
2. `plan/BUILD_CONTEXT.md` - the active task, its dependencies, its gate, its blocking
   doubts. This **replaces** reading `TASKS.yml`, `GATES.yml` and `DOUBTS.md` whole;
   they remain the place to *write*, and to read when you need another task's detail
3. `AGENTS.md`
4. `memories/SOUL.md`, `memories/USER.md`, `memories/MEMORY.md`
5. `plan/main_plan.md`, `HANDOFF.md`
6. Active feature: `.loop/active-feature.json` → `spec.md`, `feature-plan.md`, `tasks.md`
7. `plan/AUTO_SKILLS.md` / `plan/AUTO_AGENT_SKILLS.md` / `plan/AUTO_DOMAIN_SKILLS.md` / `plan/AUTO_AGENTS.md` (only when the manifest lists them)

Then load **one** phase file from the router below, and only the skills it names.

## Build phase router

`scripts/build_phase.py` computes the phase from `TASKS.yml`, `GATES.yml`, the source
tree, and the eval suite's behaviour fingerprint, and writes a `BUILD PHASE:` line into the manifest. Rules first, never a model
judgement (`AGENTS.md` non-negotiable #4).

| Phase | Selected when | File | Skills it loads |
|-------|---------------|------|-----------------|
| **clarify** | a blocking doubt can be answered now | `plan-loop/phases/resolve-doubts.md` | research-search |
| **scaffold** | no product source tree yet | `phases/scaffold.md` | implementation-planner, tool-orchestrator |
| **implement** | a task is active | `phases/implement.md` | implementation-planner, feature-workflow |
| **test** | the active task is QA-phase | `phases/test.md` | qa-validation |
| **converge** | task built, awaiting verification | `phases/converge.md` | feature-converge, code-reviewer |
| **evaluate** | eval cases exist and the last score no longer describes the current agent, or a case regressed | `skills/eval-loop/SKILL.md` | eval-loop |
| **release** | tasks complete, release gate open | `phases/release.md` | security-compliance, prod-gap, deployment-plan, cicd-release |
| **deploy** | release passed, plan names a provider, an environment has nothing recorded | `phases/deploy.md` | deploy, deployment-plan, cicd-release, security-compliance |

Read on demand, not up front: `skills/agent-builder/SKILL.md` (when the product is or
includes an AI agent), `skills/frontend-animation/SKILL.md` (when `AUTO_SKILLS.md`
lists it), `skills/docs/SKILL.md`, `skills/plan-loop/phases/spec-clarify.md` (when
requirements are blocked), `skills/session-lifecycle/SKILL.md`, and the product repo's
own instructions.

Domain work is selected deterministically at session start: database, schema, migration,
pipeline, or lineage signals load `skills/data-engineering/SKILL.md`; training, inference,
dataset, or drift signals load `skills/ml-engineering/SKILL.md`; SLO, incident, backup,
capacity, or runbook signals load `skills/operations/SKILL.md`. The selections and matched
signals are recorded in `plan/AUTO_DOMAIN_SKILLS.md`.

## Needs a decision

`plan/SESSION_MANIFEST.md` carries a **`## Needs a decision`** block when something in
this workspace has gone out of date. It is absent when there is nothing to do, so if it
is there, work it before planning or building on top of it:

| Condition | Response |
|-----------|----------|
| Generated file no longer matches its sources | `loop fresh`, then re-run whatever generates it - the report names the changed input |
| Evidence past its validity window | `loop evidence` - re-check the claim or record a fresh `Date checked`. Uncertain, not disproved: it still supports whatever cited it |
| Reference to an id nothing defines | `loop graph dangling` - fix the id or add the record |
| Reference-graph rule violation | `loop graph check` - each finding names its own fix |

Never report these to the user as a list of commands to run. Run them, act on what they
say, and report what changed (`docs/CONTINUATION.md`).

## Gate Classification

- Planning docs: allowed.
- Reversible synthetic scaffold: allowed when doubts are recorded.
- Production sensitive-data workflow: blocked until relevant gates pass.
- High-risk external action: human approval required unless the product plan says otherwise.

## Build Loop

```text
SESSION-START -> ANSWER PARENT FINDINGS + BLOCKING DOUBTS -> SELECT TASK (from active feature tasks.md + TASKS.yml) -> READ MANIFEST/AUTO-SKILLS -> PLAN DIFF -> BUILD -> TEST -> FEATURE-CONVERGE -> SESSION-END
```

The lifecycle syncs the full product tree at both bookends. For a sub-product, answering a
parent finding includes updating the owning local plan/spec/tasks before selecting build
work; for a main product, generated parent context is published to linked children. Session
closeout runs feature convergence. None of these are manual user steps.

Run `loop session-start --command /develop-product` first and `loop session-end` last. Frontend motion/3D skills and agent-development skills are auto-detected at session-start and included in the manifest when signals match (`plan/AUTO_SKILLS.md`, `plan/AUTO_AGENT_SKILLS.md`). Before frontend coding, always run `loop auto-skills --write` so selected external layers are installed or refreshed for this use. Re-run `loop auto-agent-skills --write` only if the agent-task description changed after session-start.

## Development Domains

1. Monorepo scaffold
2. Frontend - motion/3D skills auto-selected via `frontend_skill_router.py` → `plan/AUTO_SKILLS.md`
3. Backend
4. Database and migrations
5. Authentication, RBAC, tenant isolation
6. Audit logging
7. Secure file ingestion
8. Deterministic parsers and validators
9. Agent loops with schema validation - execute the selected chain from `skills/agent-builder/SKILL.md` and `skills/agent-development/SKILL.md` when the product itself is/includes an AI agent
10. QA and auto-validation
11. Documentation
12. Security checks
13. Compliance checks
14. CI/CD
15. Deployment readiness

## Required Closeout

- Run relevant tests or record why not.
- Update active feature `tasks.md` checkboxes and `TASKS.yml` status.
- Run `loop feature converge` (or `/feature-converge`) - also runs on `loop session-end` for `/develop-product`.
- Run `prod-gap` after meaningful development work.
- Run `loop release-check` when the manifest reports launch blockers - it reports what
  remains, which is worth knowing while there is still time to act on it.
- Run `deployment-plan` at loop closeout to write `DEPLOYMENT_PLAN.md`, following its reconcile-first, verify-after rules (never blind-regenerate over a hand-maintained file).
- Reuse cloud, LLM, and deployment answers already in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`.
- Ask the user only for unresolved deployment questions.
- Fix safe P0/P1 technical blockers found by `prod-gap` when in scope.
- Add human-required blockers from `prod-gap` with `loop doubts add` - never by appending
  prose, which leaves an entry no command can count or close.
- Update `memories/MEMORY.md`, `DOUBTS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, `DEPLOYMENT_PLAN.md`, and `.ai/SESSION_LOG.md`.
- Run `compact-loop` when development is long, many files changed, the user may switch tools, or the context is getting heavy.
- Run `loop session-end --command /develop-product` (mandatory; includes converge + memory-review, which applies directly).

## Output

- What was built
- Tests/checks run
- Security/compliance status
- Files changed
- Production gap status
- Deployment plan status
- Human-required blockers
- Compact status
- Next task


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
