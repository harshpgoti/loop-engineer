---
name: ask-loop
description: Answer a free-form question about a plan or build that already exists. The user asks in plain language; the agent - because it loads the full plan surface and, when needed, the product code - answers with citations instead of making the user hunt through files. Read-only: never edits plan/state/code. Use when the user types /ask-loop, or (once plan/main_plan.md is initialized) asks "why did we...", "what is the...", "how does X work", "where is Y", "what's built vs pending", "explain the plan/architecture/decision".
---

# Ask Loop

## Purpose

After `/plan-loop` or `/product-develop` finishes, a user who wants to *understand* what
exists has no entry point today. `/status` gives a fixed snapshot, not answers to questions.
`/session-recall` searches past sessions, not current product state. `/revise-plan` changes
the plan rather than reading it. Otherwise the user has to open a dozen plan files themselves
- which contradicts the whole "the agent knows where things live" premise of this OS.

`/ask-loop` is that entry point. It is the exact mirror of `/revise-plan`:

- `/revise-plan` = **talk to change** - one statement, routed to the right file, written.
- `/ask-loop` = **talk to understand** - one question, answered from the right file(s), read.

Its only job is: load full context, answer the question, cite the source, change nothing.

## Command

`/ask-loop <free-form question>`

Also treat plain language as this command (no explicit `/ask-loop` needed) whenever
`plan/main_plan.md` is already past `Status: INITIALIZED` and the user asks a question about
the existing product rather than requesting a change - "why did we pick X?", "what is the
target user again?", "how does auth work?", "where is the billing logic?", "what's built vs
still pending?", "explain the architecture / this decision / this step".

## Read-only guarantee (non-negotiable)

This command **never writes** to plan, spec, decision, doubt, gate, task, or product-code
files. The only file writes it performs are the session lifecycle log
(`loop session-start` / `loop session-end`) and, optionally, a scratch answer file the user
explicitly asks for. If the user wants something changed, hand off to `/revise-plan` (plan
edits) or `/product-develop` (code) - do not edit here.

## Required Reads - full context, always, no progressive disclosure

Plan surface:

1. `plan/main_plan.md`
2. Every `plan/step_*.md`
3. If platform scale (`plan/PLAN_SCALE.md` = platform): `plan/PRODUCT_MAP.md`, `plan/ULTRAPLAN_STATUS.md`, `plan/steps/*/`
4. `.loop/active-feature.json` -> active feature's `spec.md`, `clarifications.md`, `feature-plan.md`, `tasks.md`, `converge-report.md`
5. `DECISIONS.md`, `DOUBTS.md`, `EVIDENCE_LOG.md`
6. `TASKS.yml`, `GATES.yml`

Build surface:

7. `CURRENT_STATE.md`, `HANDOFF.md`, `plan/PROD-GAP.md`
8. `DEPLOYMENT_PLAN.md`
9. `docs/` (PRD, acceptance criteria, test plan, architecture notes, and any generated docs)

Answering on partial context is the failure mode this command exists to avoid - load the
whole surface before answering, the same way `/revise-plan` does.

## Reading the product code (escalation, when needed)

For implementation-level questions ("how does auth work?", "where is the retry logic?",
"does this endpoint validate tenant?"), the plan/docs layer may be stale or silent. When it
cannot fully answer:

1. First answer from plan/docs if they cover it, and say so.
2. If they do not, **read the actual product source code** (locate the product repo via
   `plan/main_plan.md` -> product repo strategy and `CURRENT_STATE.md`), and answer from
   what is actually built.
3. Prefer the built code as the source of truth for "how it works *now*"; prefer plan/docs
   for "why it was decided / what it's supposed to do."
4. If code and plan/docs disagree, that is **drift** - report both and flag it (see routing).

Reading code is still read-only. Never patch code from this command.

## Answer routing (by intent, not just topic)

| The user's question is really... | Do |
|---|---|
| A genuine question about the plan/build | Answer it, with citations. |
| A disguised change request ("shouldn't the target user be X?") | Answer what it currently is, then offer `/revise-plan` to change it. Do not change it yourself. |
| Asking for something the plan never decided | Say it's undecided, point at the `DOUBTS.md` entry if one exists, offer `/revise-plan` or `/plan-loop` to decide it. |
| Answerable only from code, plan/docs silent | Read code, answer, note the plan/docs gap. |
| Revealing drift (plan says X, code/tasks say Y) | Report both sides, cite each, recommend `/sync-loop-state` (state drift) or `/feature-converge` (spec-vs-build drift). Do not silently reconcile. |
| Net-new scope ("can we add feature Z?") | Answer feasibility from context, then point at `/feature-new` - that's not a question about the existing plan. |

## Citations

Every substantive claim in the answer names its source, e.g.
`(plan/step_02_billing.md -> Architecture)`, `(DECISIONS.md -> D-014)`, or
`(src/auth/session.ts:42)`. This keeps answers auditable and consistent with the OS's
evidence-first rule. If a claim has no source in context, say so explicitly rather than
inventing one.

## Process

1. `loop session-start --command /ask-loop --text "<user question>"`.
2. Read everything in **Required Reads**.
3. Parse the question. If it's genuinely ambiguous about *what* is being asked (not just
   where the answer lives), ask one direct clarifying question - otherwise answer.
4. Answer from plan/docs. Escalate to product code when the question is implementation-level
   and plan/docs can't fully answer.
5. Route by intent (table above): plain answer, or answer-plus-handoff for change requests,
   undecided items, drift, or net-new scope.
6. Attach citations to every claim.
7. `loop session-end --command /ask-loop` (read-only closeout - no memory/plan writes beyond
   the lifecycle log unless the user asked for a saved answer file).

## Scope boundary

- **Read-only.** No edits to plan, spec, decision, doubt, gate, task, or code files.
- Does not run structured Q&A interviews - that's `/spec-clarify`. One question in, one
  answer out (plus at most one clarifying question).
- Does not decide undecided things or change decided things - it reports and hands off.
- Does not analyze production readiness gaps in depth - that's `/prod-gap`. For a quick "am I
  ready?" it may summarize `plan/PROD-GAP.md` and point there.

## Output (always end an `/ask-loop` run with this)

1. The answer, in plain language
2. Citations for each claim (file -> section, or code path:line)
3. Any drift or undecided item surfaced while answering
4. Suggested next command if the question implies an action (`/revise-plan`,
   `/product-develop`, `/feature-new`, `/sync-loop-state`, `/feature-converge`) - otherwise none

## Stop Conditions

- The question is actually a change request - answer, then hand off, do not edit.
- The answer requires sensitive/regulated data that a gate hasn't cleared - say so, don't
  surface it.
- The question is a net-new feature request - route to `/feature-new`.
