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

## One workspace, canonical sources

Questions can be owned by the shared platform or by any folder under
`plan/products/<slug>/DOUBTS.md`. The parser discovers those canonical files, tags every
entry with its owning scope, and rejects duplicate ids before a write. Tables and references
to a doubt elsewhere are not new entries and are deliberately not counted.

`/resolve-doubts` is plan-wide, so every command in this phase uses `--all-scopes`.
Planning and development routing use the selected scope plus the shared platform instead,
so an unrelated sibling cannot stop the current build.

## Read First

1. Root `DOUBTS.md` plus `plan/products/*/DOUBTS.md` (canonical trackers)
2. `plan/contracts/` and `loop scope check`, when the doubt crosses sub-products
2. `DECISIONS.md`, `EVIDENCE_LOG.md`
3. `GATES.yml` (pre-development gates and their unmet criteria)
4. `TASKS.yml`, `plan/main_plan.md`, active `plan/step_*.md`
5. `.loop/active-feature.json` -> active feature `spec.md`, `clarifications.md`
6. `plan/PROD-GAP.md` and `plan/SESSION_RECALL.md` when present

## Steps

0. **Check cross-scope contracts and dependencies first:**

   ```bash
   loop scope check
   ```

   Fix or record any finding that creates, retires, or changes a doubt before asking
   questions. `skills/scope/SKILL.md` holds the full treatment.

1. **Gather every open item** into one list. Do not re-read and re-interpret
   `DOUBTS.md` by eye - one parser owns it, and every command shares its answer:

   ```bash
   loop doubts ask --all-scopes      # this round, with recorded recommendations
   loop doubts list --all-scopes     # every canonical open item, owning scope shown
   loop doubts lint --all-scopes     # bad prerequisites and contradictory status
   ```

   Then add, from the same pass:
   - open questions in the active feature `spec.md` / step plans
   - **blocked pre-development gates** in `GATES.yml` (typically `G-INIT-01`,
     `G-DISCOVERY-01`, `G-DISCOVERY-02`, `G-ARCH-01`, `G-COUNCIL-01`,
     `G-SENSITIVE-DATA`) and the specific criteria not yet met
   - decisions marked pending in `DECISIONS.md`; claims still unsourced that a
     build decision depends on
2. **Classification is already recorded** - `loop doubts` reports each item as
   blocking or non-blocking, from its `- **Blocking:** yes|no` field or, absent
   that, from the entry's own wording. Do not re-derive it by judgement each
   session; if a classification is wrong, fix the field so it stays fixed.
3. **Reuse, don't re-ask.** If `DECISIONS.md`, resolved `DOUBTS.md`,
   `clarifications.md`, or `SESSION_RECALL.md` already answers an item, resolve it
   with that answer and inform the user - do not ask again.

   When a decision does not *answer* a question but removes the reason it was asked,
   say so on the decision and the doubt stops being raised everywhere:

   ```markdown
   ## D-014: Pricing is flat fee only
   - **Supersedes:** DQ-007, DQ-020
   ```

   A main product's decision retires questions inside its sub-products this way.
   Prefer it over answering a question that no longer applies.
4. **Walk the blocking items one at a time**, each as a question with its
   recommended answer:

   - **Question** and **why it matters** - from the entry
   - **Recommended:** the entry's own `Default if unavailable`, which is what the
     person who raised it said to do when nobody answers
   - The three answers: **answer it**, **accept the default**, **defer it**

   Apply the default without asking when it is plainly safe and reversible, and say
   that you did. For research-grounded questions use `skills/research-search/SKILL.md`
   (`loop research "<query>"`) and cite in `EVIDENCE_LOG.md`.
5. **Record every resolution at its source - with the command, not by hand:**

   ```bash
   loop doubts resolve DQ-007 "Flat per-claim fee" --decision D-014 --all-scopes
   loop doubts defer DQ-020 "Decide after the first pilot" --all-scopes
   ```

   That rewrites the status *and* records the answer beside it, so the count every
   other command reads actually goes down. Then:
   - `DECISIONS.md`: add durable decisions (strategy/architecture/scope)
   - update the owning `spec.md` / `plan/step_*.md` / `plan/main_plan.md`
   - `EVIDENCE_LOG.md`: sourced answers
6. **Re-check gates.** For any `GATES.yml` gate whose criteria are now met, set
   its `status` to `pass` (or `ready`) with a one-line `note:` of what satisfied
   it. Never mark a gate passed whose criteria are still unmet.
7. **User unavailable / undecidable:**
   `loop doubts defer <id> "<risk note>" --all-scopes`, naming
   what it blocks. Do **not** loop or invent an answer - report it as a remaining
   blocker in the go/no-go.
8. **Verify before claiming GO.** Both channels, both from the harness:
   `loop doubts counts --all-scopes` is the number the go/no-go must quote and
   `loop doubts lint --all-scopes` must be clean. An entry marked resolved with no
   recorded answer, or filed under Resolved while open, prevents GO.

## Go / No-Go output (always end with this)

1. **Resolved this session** - items and where each was recorded
2. **Gates moved to pass** - and what satisfied them
3. **Cross-scope findings answered** - each one, and what changed as a result
4. **Remaining blockers** - open/deferred items that still block development (empty
   if none)
5. **Verdict** - the counts come from the harness, never from your own tally:
   - **GO** - "No blocking doubts remain, no findings open. Clear to run
     `/develop-product`." (only when `loop doubts counts --all-scopes` reports
     `blocking` 0 and `loop doubts lint --all-scopes` is clean)
   - **NO-GO** - "N blocker(s) remain: <list>. Resolve these before development."
6. Next command (`/develop-product` on GO; otherwise what to do about each blocker)

## Continue automatically

- **GO** -> load `phases/task-compiler.md` and compile tasks if they aren't yet;
  that is the planning terminus. Under `/loop-engine`, continue into
  `commands/develop-product.md` when build gates pass. Do not stop and tell the
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
