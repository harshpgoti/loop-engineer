---
name: loop-engine
description: Runs the all-in-one product loop. It chooses planning or development based on gates, tracks doubts, updates memory, and advances product development safely across tools. Use when the user types /loop-engine.
---

# Loop Engine

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Self-drive the product loop from planning to development without manual context transfer. **Primary entry point** - must wire every built-in capability.

## Command

`/loop-engine`

## Read First

1. `plan/SESSION_MANIFEST.md` (after `loop session-start`)
2. `AGENTS.md`
3. `memories/SOUL.md`, `memories/USER.md`, `memories/MEMORY.md`
4. `DOUBTS.md`, `plan/main_plan.md`, `HANDOFF.md`
5. `commands/loop-engine.md` (routing table)
6. `.loop/active-feature.json` and active feature folder when present
7. `plan/PLAN_SCALE.md`, `plan/ULTRAPLAN_STATUS.md` (when platform)
8. `plan/SESSION_RECALL.md`, `plan/AUTO_SKILLS.md`, `plan/AUTO_AGENT_SKILLS.md` (if present)
9. `TASKS.yml`, `GATES.yml`, `CURRENT_STATE.md`
10. `skills/tool-orchestrator/SKILL.md` (supporting tool/pattern selection - `docs/PROCESS.md` names this a key `/loop-engine` skill)

## Mandatory bookends

```bash
loop session-start --command /loop-engine --tool "<tool>"
loop session-end --command /loop-engine --summary "<progress>"
```

Both lifecycle bookends automatically sync the product tree. A sub-product assimilates
cross-scope contract findings into the plan before routing; a platform
product publishes refreshed generated context to its children. Mutating closeout converges
the active feature, so the user never chains `loop scope check` or `/feature-converge`.

## Routing (enter here, then **keep going** - do not stop at the branch boundary)

Pick the entry branch from state, then cascade through it and into the next until
the build slice is complete or a Stop Condition fires (`docs/CONTINUATION.md`).
Plan work flows into development automatically **when the gates pass** - crossing
that boundary is this command's job, not the user's.

| State | Delegate to |
|-------|-------------|
| A sub-product consumes a contract nobody provides | `skills/scope/SKILL.md` / the cross-scope check |
| Blocking doubts open | `skills/plan-loop/phases/resolve-doubts.md` / `loop doubts ask` |
| Uninitialized / init gates blocked | `commands/plan-loop.md` full flow |
| Idea scope unknown | `loop plan-loop scale --write` |
| Scale **platform**, ultraplan incomplete | `skills/plan-loop/phases/ultraplan.md` / `loop plan-loop ultraplan next` |
| Missing step plan or feature spec | `commands/plan-loop.md` (steps 14-16) |
| Spec needs clarify/checklist | `/spec-clarify` → `/spec-checklist` → `/resolve-doubts` → compile (run the chain, don't hand it back) |
| Missing tasks | `skills/plan-loop/phases/task-compiler.md` |
| Product is/includes an AI agent | `skills/agent-builder/SKILL.md` + the selectively loaded capability chain in `skills/agent-development/SKILL.md` (`loop auto-agent-skills --write` first) |
| Build gates pass | `commands/develop-product.md` full flow |
| Blocked on requirements mid-build | `/spec-clarify` |
| After develop slice | `loop feature converge` + `skills/prod-gap/SKILL.md` |
| `BUILD PHASE: evaluate` - the score no longer describes the current agent, or a case regressed | `skills/eval-loop/SKILL.md` (`loop eval`). Computed from a behaviour fingerprint, not judged - code review does not see behaviour |
| Launch blockers reported in the manifest | `skills/release-check/SKILL.md` (`loop release-check`) - it says what remains, so read it during build rather than discovering it at the end |
| Meaningful work unit complete | `skills/deployment-plan/SKILL.md` (`loop deployment-plan`) |
| Release in scope | `skills/cicd-release/SKILL.md` |
| Long session | `skills/compact-loop/SKILL.md` |
| Memory/handoff/gates/tasks look inconsistent mid-loop | `skills/sync-loop-state/SKILL.md` (`loop sync`), then resume |
| Scripts fail to import, workspace not detected, or setup looks broken | `skills/doctor/SKILL.md` (`loop doctor`) before continuing |

## Full cycle

```text
SESSION-START → MANIFEST → RECALL → AUTO-SKILLS → AUTO-AGENT-SKILLS
→ [PLAN: scale → map → ultraplan/step → feature → clarify → checklist → compile]
→ [DEVELOP: task → plan diff → build → review → QA → security]
→ CONVERGE → PROD-GAP → DEPLOYMENT-PLAN → COMPACT? → SESSION-END
```

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

## Decision Logic

0. Run `loop session-start`; read manifest and listed files.
1. If Step 1 gates blocked → execute `skills/plan-loop/SKILL.md` / `commands/plan-loop.md`.
2. Run `loop plan-loop scale --write` when product idea may be platform-scale.
3. If scale is **platform** and ultraplan incomplete → `skills/plan-loop/phases/ultraplan.md` (one step per session).
4. If no active feature or spec incomplete → feature workflow (`feature-new`, `spec-clarify`, `spec-checklist`).
3. If tasks missing → `task-compiler`.
4. If build gates pass → execute `skills/develop-product/SKILL.md` / `commands/develop-product.md`.
5. For a frontend build task, run `loop auto-skills --write` to install/update selected
   external layers for this use, then read `plan/AUTO_SKILLS.md`.
5a. Read `plan/AUTO_AGENT_SKILLS.md` when manifest lists agent-development skills (auto-detected at session-start) and execute `skills/agent-builder/SKILL.md`.
6. After develop work → `feature-converge` + `prod-gap`.
7. If sensitive-data gates blocked → synthetic data only.
8. Invoke review skills when required: `qa-validation`, `security-compliance`, `code-reviewer`, `cicd-release`.
9. Human-required blockers → `DOUBTS.md` + `HANDOFF.md`.
10. Long session → `compact-loop`.
10a. If `HANDOFF.md`/`TASKS.yml`/`GATES.yml`/`memories/MEMORY.md` look mutually inconsistent → `loop sync` (`skills/sync-loop-state/SKILL.md`) before trusting them further.
10b. If a script import fails or the workspace doesn't resolve as expected → `loop doctor` (`skills/doctor/SKILL.md`) before continuing.
11. Closeout → `loop session-end` (memory-review applies directly; converge on develop).

## Continuation

Terminus: **build slice complete** (task built, reviewed, QA'd, converged,
prod-gap checked) - or the planning terminus when build gates are still blocked.
Cascade automatically; stop only on a Stop Condition from `docs/CONTINUATION.md`
(user decision, human-approval gate, sensitive-data boundary, missing info,
context exhaustion → `/compact-loop` first). When you stop, name the condition and
what you need.

## Output

- Branches ran end to end (plan / develop / both)
- Gate and feature state
- Session lifecycle + auto-skills status
- Work completed, gaps, blockers
- If stopped early: which Stop Condition fired and what is needed
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
