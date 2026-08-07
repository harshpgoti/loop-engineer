# Phase: Resolve Doubts (pre-development readiness)

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: resolve-doubts`, or when the
> user types `/resolve-doubts`. Runs inside `/plan-loop` as the final readiness
> sweep, and standalone anytime open doubts accumulate.

## Purpose

Sit with the user and clear **every open doubt and blocker across the whole plan**
- not one feature spec - so development can start without ambiguity. Unlike
`/spec-clarify` (one active feature's open questions) this is plan-wide; unlike
`/ask-loop` (read-only) this records decisions; unlike `/prod-gap` (writes a
report) this is an interactive drive-to-green that ends in a **go/no-go**.

Where each fits:

- `/revise-plan` - talk to **change** a detail
- `/ask-loop` - talk to **understand** (read-only)
- `/resolve-doubts` - talk to **resolve** open blockers to green before build

## Read First

1. `DOUBTS.md` (the open-doubt tracker)
2. `DECISIONS.md`, `EVIDENCE_LOG.md`
3. `GATES.yml` (pre-development gates and their unmet criteria)
4. `TASKS.yml`, `plan/main_plan.md`, active `plan/step_*.md`
5. `.loop/active-feature.json` -> active feature `spec.md`, `clarifications.md`
6. `plan/PROD-GAP.md` and `plan/SESSION_RECALL.md` when present

## Steps

1. **Gather every open item** into one list:
   - `DOUBTS.md` entries with `status: open`
   - open questions in the active feature `spec.md` / step plans
   - **blocked pre-development gates** in `GATES.yml` (typically `G-INIT-01`,
     `G-DISCOVERY-01`, `G-DISCOVERY-02`, `G-ARCH-01`, `G-COUNCIL-01`,
     `G-SENSITIVE-DATA`) and the specific criteria not yet met
   - decisions marked pending in `DECISIONS.md`; claims still unsourced that a
     build decision depends on
2. **Classify** each as **blocking** (development can't safely start) or
   **deferrable** (can be decided during build). Show the user the grouped list.
3. **Reuse, don't re-ask.** If `DECISIONS.md`, resolved `DOUBTS.md`,
   `clarifications.md`, or `SESSION_RECALL.md` already answers an item, mark it
   resolved and inform the user - do not ask again.
4. **Walk the blocking items one at a time.** Ask the user a direct question per
   item. For research-grounded questions use `skills/research-search/SKILL.md`
   (`loop research "<query>"`) and cite in `EVIDENCE_LOG.md`.
5. **Record every resolution** at its source:
   - `DOUBTS.md`: set the item `status: resolved` with the answer, or
     `status: deferred` for non-blocking items (never leave a decided item `open`)
   - `DECISIONS.md`: add durable decisions (strategy/architecture/scope)
   - update the owning `spec.md` / `plan/step_*.md` / `plan/main_plan.md`
   - `EVIDENCE_LOG.md`: sourced answers
6. **Re-check gates.** For any `GATES.yml` gate whose criteria are now met, set
   its `status` to `pass` (or `ready`) with a one-line `note:` of what satisfied
   it. Never mark a gate passed whose criteria are still unmet.
7. **User unavailable / undecidable:** mark the item `status: deferred` in
   `DOUBTS.md` with an explicit risk note and a `blocks:` pointer to what it
   affects. Do **not** loop or invent an answer - report it as a remaining
   blocker in the go/no-go.

## Go / No-Go output (always end with this)

1. **Resolved this session** - items and where each was recorded
2. **Gates moved to pass** - and what satisfied them
3. **Remaining blockers** - open/deferred items that still block development (empty
   if none)
4. **Verdict:**
   - **GO** - "No blocking doubts remain. Clear to run `/product-develop`." (only
     when there are zero remaining blockers and the pre-dev gates pass)
   - **NO-GO** - "N blocker(s) remain: <list>. Resolve these before development."
5. Next command (`/product-develop` on GO; otherwise what to do about each blocker)

## Continue automatically

- **GO** -> load `phases/task-compiler.md` and compile tasks if they aren't yet;
  that is the planning terminus. Under `/loop-engine`, continue into
  `commands/product-develop.md` when build gates pass. Do not stop and tell the
  user to run the next command.
- **NO-GO** -> this is a legitimate Stop Condition (blocking items need the user).
  Report each remaining blocker and the specific question it needs answered - not
  a command to run. Route ones that are strategic pivots to `phases/council.md`.

See `docs/CONTINUATION.md`.

## Stop Conditions

- A blocking doubt is a strategic pivot, not a detail - route to
  `skills/plan-loop/phases/council.md` instead of resolving inline.
- Sensitive/regulated data is requested before `G-SENSITIVE-DATA` passes - keep
  synthetic-only and record the doubt, don't surface real data.
