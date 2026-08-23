# Phase: Grill

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: grill` - force clarity before build work.
> Also the internal grill step during `/plan-loop`, pivots, and ICP/pricing/compliance/architecture decisions.

## Purpose

Interview the user until you reach a shared understanding of the plan. Weak strategy that
survives this phase becomes product debt that survives the whole build.

## Read First

- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md`
- active `plan/step_*.md`

## The tree and the frontier

Decisions branch: settling one opens the decisions that hang off it. The **frontier** is
every decision whose prerequisites are already settled - the questions you can ask now
without guessing at answers you have not heard yet.

`loop doubts ask` computes the frontier over recorded doubts and prints exactly one round.
Questions you raise fresh in this session belong to the same tree: record each one with
`Depends on:` when it sits behind another, so the next session inherits the ordering
instead of rediscovering it.

Ask the whole frontier in one round. Then stop and wait. A question whose answer depends on
another question still open **in this round** belongs to a later round, not this one.

## One round

Number every question and attach your recommended answer. A question with no recommendation
puts the work back on the user, which is the thing this phase exists to avoid.

```text
Q1 - Target buyer: Clinic owner or billing manager? They buy differently: the owner buys
     outcomes and signs same-day; the manager buys workflow and needs a champion above them.

  -> Clinic owner. The plan's whole GTM is a paid audit, and a manager cannot approve spend.

---

Q2 - ...
```

Then wait. Each round of answers reshapes the tree: recompute the frontier and ask the next
round.

## Finding facts is your job, never the user's

If a frontier question needs a fact from the environment - what the code already does, what
a payer's format actually contains, what a competitor charges - go get it. Read the repo.
Run `loop research "<query>"`. Never ask the user something you could look up.

Do not block the whole round on it: a lookup in flight is an unsettled prerequisite, so only
the questions downstream of it wait. Ask the rest of the frontier now.

## Grill areas

Coverage, not a checklist - reach for whichever the current plan leaves soft:

target user and buyer · urgency and budget · workflow frequency · data access ·
differentiation · risk and compliance posture · cloud provider and deployment · LLM provider,
model, and cost posture · distribution path · pilot or validation path · what to kill or delay

## After each round

| The answer | Where it goes |
|------------|---------------|
| Settles a recorded question | `loop doubts resolve <id> "<answer>"` |
| Not now, go with the default | `loop doubts defer <id> "<why>"` |
| Changes strategy or architecture | `DECISIONS.md`, plus `Supersedes:` for questions it retires |
| Needs proof | `EVIDENCE_LOG.md` - cite the source, never the search |
| Raises a new question | `loop doubts add`, with `Depends on:` / `Ask:` where they apply |
| Belongs to someone who is not here | `Ask: <who>`, then `loop doubts questionnaire` |
| In scope but not yet sharp enough to ask | `## Not yet specified` in `plan/main_plan.md` |

Then `memories/MEMORY.md`.

## Done

The frontier is empty: every branch visited, nothing left silently assumed. Blocking
questions that remain are either out with someone else (`loop doubts questionnaire`) or
deferred with a recorded default - not forgotten.

Do not act on the plan until the user confirms you have reached a shared understanding.

## Continue automatically

Load `phases/council.md` and keep going - pressure-test the grilled plan across senior
perspectives before locking strategy/architecture. Do not stop and ask the user to run
council; it is the next thing to execute, not a suggestion.

Stop early only if grilling surfaced a question that genuinely changes product direction and
only the user can settle it. See `docs/CONTINUATION.md`.
