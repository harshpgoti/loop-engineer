---
name: develop-product
description: Runs product engineering from the approved plan: frontend, backend, database, agent loops, QA, auto-validation, docs, security, compliance, CI/CD, and deployment readiness. Use when the user types /develop-product or asks to start development.
---

# Product Develop

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
7. `plan/AUTO_SKILLS.md` / `plan/AUTO_AGENT_SKILLS.md` (only when the manifest lists them)

Then load **one** phase file from the router below, and only the skills it names.

## Build phase router

`scripts/build_phase.py` computes the phase from `TASKS.yml`, `GATES.yml`, the source
tree, and the eval suite's behaviour fingerprint, and writes a `BUILD PHASE:` line into the manifest. Rules first, never a model
judgement (`AGENTS.md` non-negotiable #4).

| Phase | Selected when | File | Skills it loads |
|-------|---------------|------|-----------------|
| **scaffold** | no product source tree yet | `phases/scaffold.md` | implementation-planner, tool-orchestrator |
| **implement** | a task is active | `phases/implement.md` | implementation-planner, feature-workflow |
| **test** | the active task is QA-phase | `phases/test.md` | qa-validation |
| **converge** | task built, awaiting verification | `phases/converge.md` | feature-converge, code-reviewer |
| **evaluate** | eval cases exist and the last score no longer describes the current agent, or a case regressed | `skills/eval-loop/SKILL.md` | eval-loop |
| **release** | tasks complete, release gate open | `phases/release.md` | security-compliance, prod-gap, deployment-plan, cicd-release |

Read on demand, not up front: `skills/agent-builder/SKILL.md` (when the product is or
includes an AI agent), `skills/frontend-animation/SKILL.md` (when `AUTO_SKILLS.md`
lists it), `skills/docs/SKILL.md`, `skills/plan-loop/phases/spec-clarify.md` (when
requirements are blocked), `skills/session-lifecycle/SKILL.md`, and the product repo's
own instructions.

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

Run `loop session-start --command /develop-product` first and `loop session-end` last. Frontend motion/3D skills and agent-development skills are both auto-detected at session-start and included in the manifest when signals match (`plan/AUTO_SKILLS.md`, `plan/AUTO_AGENT_SKILLS.md`) - re-run `loop auto-agent-skills --write` only if the task description changed after session-start.

## Development Domains

1. Monorepo scaffold
2. Frontend - motion/3D skills auto-selected via `frontend_skill_router.py` → `plan/AUTO_SKILLS.md`
3. Backend
4. Database and migrations
5. Authentication, RBAC, tenant isolation
6. Audit logging
7. Secure file ingestion
8. Deterministic parsers and validators
9. Agent loops with schema validation - see `skills/agent-builder/SKILL.md` when the product itself is/includes an AI agent
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
- Run `deployment-plan` at loop closeout to write `DEPLOYMENT_PLAN.md`.
- Reuse cloud, LLM, and deployment answers already in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`.
- Ask the user only for unresolved deployment questions.
- Fix safe P0/P1 technical blockers found by `prod-gap` when in scope.
- Add human-required blockers from `prod-gap` with `loop doubts add` - never by appending
  prose, which leaves an entry no command can count or close.
- Update `memories/MEMORY.md`, `DOUBTS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, `DEPLOYMENT_PLAN.md`, and `.ai/SESSION_LOG.md`.
- Run `compact-loop` when development is long, many files changed, the user may switch tools, or the context is getting heavy.
- Run `loop session-end --command /develop-product` (mandatory; includes converge + memory-review staging).

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
