---
name: revise-plan
description: Apply a free-form correction or addition to a plan that already exists. The user talks in plain language; the agent - because it always loads the full plan surface first - decides which file(s) actually need to change, instead of asking the user where to put it. Use when the user types /revise-plan, or (once plan/main_plan.md is already initialized) says things like "actually X should be Y", "correct the plan", "add a detail I forgot", "update the plan with...".
---

# Revise Plan

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

`/plan-loop` builds a plan once, phase by phase, with progressive disclosure (load only the
active phase). `/spec-clarify` fills gaps in one unfinished feature spec via structured Q&A.
Neither fits the moment after a plan already exists and the user just wants to correct or add
one fact - they don't know or care which of a dozen files holds it.

`/revise-plan` is that entry point. Its only trick is: **load the entire plan surface every
time, never progressively**. The command's whole value is that the agent - not the user -
knows where a fact lives.

## Command

`/revise-plan <free-form correction or addition>`

Also treat plain language as this command (no explicit `/revise-plan` needed) whenever
`plan/main_plan.md` is already past `Status: INITIALIZED` and the user says something that
reads as a correction/addition rather than a new planning session - "actually...", "correct
the...", "I forgot to mention...", "change X to Y", "add a note that...".

## Required Reads - full context, always, no progressive disclosure

1. `plan/main_plan.md`
2. Every `plan/step_*.md`
3. If platform scale: `plan/PRODUCT_MAP.md`, `plan/ULTRAPLAN_STATUS.md`, root-owned `plan/steps/*/`, and every scope-owned `plan/products/*/` pack plus its `steps/` and `features/`
4. `.loop/active-feature.json` -> active feature's `spec.md`, `clarifications.md`, `feature-plan.md`, `tasks.md`
5. `DECISIONS.md`, `DOUBTS.md`, `EVIDENCE_LOG.md`
6. `TASKS.yml`, `GATES.yml`
7. `DEPLOYMENT_PLAN.md`, `CURRENT_STATE.md`, `HANDOFF.md`

Skipping any of these defeats the purpose of the command - a routing decision made on partial
context is exactly the failure mode this command exists to avoid.

## Routing table (heuristic, not exhaustive - use judgment for edge cases)

| The user's statement is about... | Target file(s) |
|---|---|
| Product name, one-liner, target user, buyer, problem, constraints, sensitive-data posture, preferred stack | `plan/main_plan.md` -> Product section |
| Cloud/LLM/deployment choice | `plan/main_plan.md` -> Deployment & Infrastructure, and `DEPLOYMENT_PLAN.md` if already drafted |
| Scope/requirement for one product step | the matching `plan/step_XX_<slug>.md` |
| Requirement or acceptance criterion for the active buildable feature | active feature `spec.md` (+ `clarifications.md` if it was previously an open question) |
| Feature task breakdown | active feature `tasks.md`, synced into `TASKS.yml` |
| Architecture, data model, integration, or build/buy choice | the owning step file's architecture section, plus a `DECISIONS.md` entry |
| Platform-scale module/agent detail | `plan/PRODUCT_MAP.md` plus its canonical owner: `plan/products/<slug>/` for a sub-product, otherwise `plan/steps/NN-slug/` |
| Reversal of a prior committed decision | `DECISIONS.md` (mark prior entry superseded) + wherever that decision is materialized |
| Answer to an existing open question | `DOUBTS.md` (mark resolved) + `DECISIONS.md` + destination file above |
| Gate criteria itself changing (not just what satisfies it) | `GATES.yml` |

A single user statement may fan out to more than one file (e.g. changing the target user
touches `plan/main_plan.md` AND may resolve a `DOUBTS.md` entry AND invalidate a
`DECISIONS.md` entry). Apply all of them, not just the first match.

## Process

1. `loop session-start --command /revise-plan --text "<user statement>"`.
2. Read everything in **Required Reads**.
3. When the edit changes what one sub-product promises another, update `plan/contracts/`
   and re-run the cross-scope check in the same run.
4. Parse the user's statement into one or more discrete facts. Handle multi-fact statements
   as separate routed edits, not one blob.
5. For each fact, find its current home (it may already be stated elsewhere and need
   correcting, not just appending) using the routing table.
5a. If the revision introduces or changes an agent, re-run `loop auto-agent-skills --write`,
    read `skills/agent-development/SKILL.md`, and reconcile the selected capability chain,
    agent artifacts, eval requirements, tasks, and gates in the same revision.
6. Before writing, check whether the fact's target area is **locked**:
   - an unanswered finding from the parent product covering the same ground
     and will simply be re-raised next session, or
   - a feature already implemented (its tasks in `TASKS.yml` / `tasks.md` are `done`, or
     `/feature-converge` has run against it).
   - **If locked:** tell the user which gate/decision this reopens and get a go-ahead before
     writing. This is a hard stop, not a note-and-continue.
   - **If not locked:** apply the edit directly.
7. Apply the edit(s) - targeted patch to the specific section/line, not a rewrite of the file.
8. **If the fact touches a locked/already-built area (user-approved in step 6):**
   - Still make the plan/spec-level edit (never edit product code from this command).
   - Add or update `TASKS.yml` entries for the rework this creates: new `id`, `phase`,
     `gate`, `blocked_by` pointing at the now-stale build, and `acceptance` describing what
     must change to reconcile the build with the revised plan. Mirror the same task in the
     active feature's `tasks.md` if it's feature-scoped.
   - If the invalidated `GATES.yml` entry's `status` was not `blocked`, set it back to
     `blocked` and add a one-line `note:` explaining why - never leave a stale "passed" gate
     next to a plan that no longer matches it.
9. Log every applied revision in `DECISIONS.md` under a `## Revision Log` entry: date, what
   changed, why (from the user's own words), files touched, and whether it reopened a gate
   or created new tasks.
10. If the fact resolves an open `DOUBTS.md` question, close it with the command so the
   count every other command reads actually moves - never hand-edit the status:

   ```bash
   loop doubts resolve DQ-007 "<the answer this fact gives>" --decision D-014
   ```
11. Update `memories/MEMORY.md` and `HANDOFF.md` with what changed and any new outstanding
    tasks.
12. `loop session-end --command /revise-plan --summary "<what changed>"`. Closeout
    automatically runs feature convergence when active and re-syncs the product tree.

## Not a question - if the user is asking, not changing

If the user's statement is a **question** about the existing plan/build ("why did we pick
X?", "how does auth work?", "what's built so far?") rather than a correction or addition,
that's `/ask-loop` (`skills/ask-loop/SKILL.md`) - the read-only mirror of this command. Route
there instead of editing. Only stay in `/revise-plan` when something should actually change.

## Continuation

Terminus: **plan consistent again.** The edit is not done until everything it
invalidated is reconciled in this same run - gates walked back to `blocked`,
rework tasks written to `TASKS.yml`/`tasks.md`, doubts resolved, decisions logged.
Never leave the workspace describing the old requirement. See
`docs/CONTINUATION.md`.

## Scope boundary

- This command edits **plan, spec, decision, doubt, gate, and task files only**. It never
  edits product/application code. If a revision affects something already built, the fix is
  a new `TASKS.yml` entry plus a pointer to `/develop-product` or `/feature-converge` -
  not a direct code patch from here.
- Do not re-run `/spec-clarify`-style structured Q&A. If the user's statement is ambiguous
  about which file it targets, ask one direct question about that ambiguity - don't turn
  this into a multi-turn interview.
- Do not re-litigate settled product direction. If the "correction" is actually a strategic
  pivot (contradicts the product thesis, not just a detail), stop and say so - route back to
  `/plan-loop` council phase (`skills/plan-loop/phases/council.md`) instead of silently
  editing.

## Output (always end a `/revise-plan` run with this)

1. Which fact(s) changed, and in which file(s)
2. Any `GATES.yml` entry reopened / moved back to `blocked`, and why
3. Any new/updated `TASKS.yml` entries created because of this revision, with their IDs
4. Any `DOUBTS.md` entry resolved
5. Plain-language reminder of what still needs to be done to reconcile already-built work
   with the revised plan (empty if nothing was built yet)
6. Next command (usually back to whatever `HANDOFF.md` already pointed at, or
   `/develop-product` if new tasks were created)

## Stop Conditions

- The target area is locked (passed gate or already-built feature) - confirm before writing.
- The statement is a strategic pivot, not a detail correction - route to plan-loop council.
- The user is asking to add net-new scope (a new feature) rather than correct existing scope
  - that's `/feature-new`, not `/revise-plan`.


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
