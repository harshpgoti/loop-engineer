---
name: loop-engine
description: Runs the all-in-one product loop. It chooses planning or development based on gates, tracks doubts, updates memory, and advances product development safely across tools. Use when the user types /loop-engine.
---

# Loop Engine

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

## Routing (enter here, then **keep going** - do not stop at the branch boundary)

Pick the entry branch from state, then cascade through it and into the next until
the build slice is complete or a Stop Condition fires (`docs/CONTINUATION.md`).
Plan work flows into development automatically **when the gates pass** - crossing
that boundary is this command's job, not the user's.

| State | Delegate to |
|-------|-------------|
| Unanswered findings from the parent product | `skills/plan-loop/phases/parent-findings.md` / `loop findings ask` |
| Blocking doubts open | `skills/plan-loop/phases/resolve-doubts.md` / `loop doubts ask` |
| Uninitialized / init gates blocked | `commands/plan-loop.md` full flow |
| Idea scope unknown | `loop plan-loop scale --write` |
| Scale **platform**, ultraplan incomplete | `skills/plan-loop/phases/ultraplan.md` / `loop plan-loop ultraplan next` |
| Missing step plan or feature spec | `commands/plan-loop.md` (steps 14-16) |
| Spec needs clarify/checklist | `/spec-clarify` → `/spec-checklist` → `/resolve-doubts` → compile (run the chain, don't hand it back) |
| Missing tasks | `skills/plan-loop/phases/task-compiler.md` |
| Product is/includes an AI agent | `skills/agent-builder/SKILL.md` (`loop auto-agent-skills --write` first) |
| Build gates pass | `commands/product-develop.md` full flow |
| Blocked on requirements mid-build | `/spec-clarify` |
| After develop slice | `loop feature converge` + `skills/prod-gap/SKILL.md` |
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

## Decision Logic

0. Run `loop session-start`; read manifest and listed files.
1. If Step 1 gates blocked → execute `skills/plan-loop/SKILL.md` / `commands/plan-loop.md`.
2. Run `loop plan-loop scale --write` when product idea may be platform-scale.
3. If scale is **platform** and ultraplan incomplete → `skills/plan-loop/phases/ultraplan.md` (one step per session).
4. If no active feature or spec incomplete → feature workflow (`feature-new`, `spec-clarify`, `spec-checklist`).
3. If tasks missing → `task-compiler`.
4. If build gates pass → execute `skills/product-develop/SKILL.md` / `commands/product-develop.md`.
5. Read `plan/AUTO_SKILLS.md` when manifest lists frontend skills.
5a. Read `plan/AUTO_AGENT_SKILLS.md` when manifest lists agent-development skills (auto-detected at session-start) and execute `skills/agent-builder/SKILL.md`.
6. After develop work → `feature-converge` + `prod-gap`.
7. If sensitive-data gates blocked → synthetic data only.
8. Invoke review skills when required: `qa-validation`, `security-compliance`, `code-reviewer`, `cicd-release`.
9. Human-required blockers → `DOUBTS.md` + `HANDOFF.md`.
10. Long session → `compact-loop`.
10a. If `HANDOFF.md`/`TASKS.yml`/`GATES.yml`/`memories/MEMORY.md` look mutually inconsistent → `loop sync` (`skills/sync-loop-state/SKILL.md`) before trusting them further.
10b. If a script import fails or the workspace doesn't resolve as expected → `loop doctor` (`skills/doctor/SKILL.md`) before continuing.
11. Closeout → `loop session-end` (memory-review staged; converge on develop).

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
