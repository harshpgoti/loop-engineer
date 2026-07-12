---
name: revise-plan
description: Apply a free-form correction or addition to a plan that already exists. The user talks in plain language; the agent - because it always loads the full plan surface first - decides which file(s) actually need to change, instead of asking the user where to put it. Use when the user types /revise-plan, or (once plan/main_plan.md is already initialized) says things like "actually X should be Y", "correct the plan", "add a detail I forgot", "update the plan with...".
---

# Revise Plan

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
3. If platform scale (`plan/PLAN_SCALE.md` = platform): `plan/PRODUCT_MAP.md`, `plan/ULTRAPLAN_STATUS.md`, `plan/steps/*/`
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
| Platform-scale module/agent detail | `plan/PRODUCT_MAP.md` or the relevant `plan/steps/NN-slug/` file |
| Reversal of a prior committed decision | `DECISIONS.md` (mark prior entry superseded) + wherever that decision is materialized |
| Answer to an existing open question | `DOUBTS.md` (mark resolved) + `DECISIONS.md` + destination file above |
| Gate criteria itself changing (not just what satisfies it) | `GATES.yml` |

A single user statement may fan out to more than one file (e.g. changing the target user
touches `plan/main_plan.md` AND may resolve a `DOUBTS.md` entry AND invalidate a
`DECISIONS.md` entry). Apply all of them, not just the first match.

## Process

1. `loop session-start --command /revise-plan --text "<user statement>"`.
2. Read everything in **Required Reads**.
3. Parse the user's statement into one or more discrete facts. Handle multi-fact statements
   as separate routed edits, not one blob.
4. For each fact, find its current home (it may already be stated elsewhere and need
   correcting, not just appending) using the routing table.
5. Before writing, check whether the fact's target area is **locked**:
   - a `GATES.yml` entry whose `status:` is anything other than `blocked` (i.e. already
     passed) and whose criteria this fact would invalidate, or
   - a feature already implemented (its tasks in `TASKS.yml` / `tasks.md` are `done`, or
     `/feature-converge` has run against it).
   - **If locked:** tell the user which gate/decision this reopens and get a go-ahead before
     writing. This is a hard stop, not a note-and-continue.
   - **If not locked:** apply the edit directly.
6. Apply the edit(s) - targeted patch to the specific section/line, not a rewrite of the file.
7. **If the fact touches a locked/already-built area (user-approved in step 5):**
   - Still make the plan/spec-level edit (never edit product code from this command).
   - Add or update `TASKS.yml` entries for the rework this creates: new `id`, `phase`,
     `gate`, `blocked_by` pointing at the now-stale build, and `acceptance` describing what
     must change to reconcile the build with the revised plan. Mirror the same task in the
     active feature's `tasks.md` if it's feature-scoped.
   - If the invalidated `GATES.yml` entry's `status` was not `blocked`, set it back to
     `blocked` and add a one-line `note:` explaining why - never leave a stale "passed" gate
     next to a plan that no longer matches it.
8. Log every applied revision in `DECISIONS.md` under a `## Revision Log` entry: date, what
   changed, why (from the user's own words), files touched, and whether it reopened a gate
   or created new tasks.
9. If the fact resolves an open `DOUBTS.md` question, mark it `resolved` and cross-link the
   `DECISIONS.md` entry.
10. Update `memories/MEMORY.md` and `HANDOFF.md` with what changed and any new outstanding
    tasks.
11. `loop session-end --command /revise-plan --summary "<what changed>"`.

## Not a question - if the user is asking, not changing

If the user's statement is a **question** about the existing plan/build ("why did we pick
X?", "how does auth work?", "what's built so far?") rather than a correction or addition,
that's `/ask-loop` (`skills/ask-loop/SKILL.md`) - the read-only mirror of this command. Route
there instead of editing. Only stay in `/revise-plan` when something should actually change.

## Scope boundary

- This command edits **plan, spec, decision, doubt, gate, and task files only**. It never
  edits product/application code. If a revision affects something already built, the fix is
  a new `TASKS.yml` entry plus a pointer to `/product-develop` or `/feature-converge` -
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
   `/product-develop` if new tasks were created)

## Stop Conditions

- The target area is locked (passed gate or already-built feature) - confirm before writing.
- The statement is a strategic pivot, not a detail correction - route to plan-loop council.
- The user is asking to add net-new scope (a new feature) rather than correct existing scope
  - that's `/feature-new`, not `/revise-plan`.
