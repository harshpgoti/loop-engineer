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

## Sharpen the words as you go

When the user uses a term that clashes with `CONTEXT.md`, say so in the round: "your glossary
calls this a Denial, you seem to mean a rejection - which is it?". When they use a vague or
overloaded word, propose a precise one. Write the resolution into `CONTEXT.md` `## Language`
**there and then**, not at the end - a name settled in conversation and never recorded is a
name the next session re-litigates.

`loop glossary` reports where the plan still uses a displaced synonym. It reports and never
rewrites: two words that turn out to name different things get two definitions, not a rename.

## Tech stack finalization

The stack is a grill output, not a build-time discovery. Every layer below is named
explicitly, with the version line the build will pin, before planning leaves this phase.

| Layer | What must be named |
|-------|--------------------|
| Language + runtime | Language and major version (Node 22, Python 3.12, Go 1.23) |
| Backend framework | Framework and API style (REST / GraphQL / RPC) |
| Frontend | Framework, rendering model (SSR/SPA/static), styling system |
| **Datastore** | The actual engine and where it is hosted - see below |
| Data access | ORM/query layer and the migration tool that owns schema history |
| Auth | Identity provider or in-house, session vs token, tenancy model |
| Background work | Queue/scheduler, or an explicit "none, synchronous only" |
| File/object storage | Provider, or an explicit "none" |
| Package/build | Package manager, monorepo tool, bundler |
| Test runner | Unit and end-to-end runners the QA phase will call |

Two rules make this stick:

**There is no default datastore.** No skill in this loop picks one for you, and no build may
pick one for itself. Name the engine (Postgres, MySQL, DynamoDB, …) *and* its hosting, and
write it into **Deployment & Infrastructure -> Database hosting** as the same string. A
scaffold that reaches for a local file database because the plan never said otherwise is the
exact failure `phases/resolve-doubts.md` describes: a build sitting on SQLite while the plan
had decided Postgres with row-level security. A local dev stand-in (PGLite, an in-memory
adapter) is a *test* decision that belongs to `skills/codebase-design/SKILL.md`, never a
substitute for naming production.

**Inherited beats invented.** In a sub-product, the parent's stack rows are constraints, not
suggestions. Reuse them, say you are reusing them, and raise a doubt if this scope needs to
diverge - `loop scope check` reports a divergence as a `deployment-conflict`, and it is far
cheaper as a question here than as a migration later.

Constrain the choice against what is already settled: the cloud provider limits managed
datastores, the compute model limits long-running processes, the compliance posture limits
regions and vendors. A layer that hangs on an unsettled prerequisite is downstream frontier -
ask it next round, not this one.

Every unresolved layer leaves this phase as a doubt with a recorded
`Default if unavailable`, so the build inherits a stated fallback instead of a silent one.

## Grill areas

Coverage, not a checklist - reach for whichever the current plan leaves soft:

target user and buyer · urgency and budget · workflow frequency · data access ·
differentiation · risk and compliance posture · cloud provider and deployment · tech stack
finalization (see above) · LLM provider, model, and cost posture · distribution path · pilot or
validation path · what to kill or delay

## After each round

| The answer | Where it goes |
|------------|---------------|
| Settles a recorded question | `loop doubts resolve <id> "<answer>"` |
| Not now, go with the default | `loop doubts defer <id> "<why>"` |
| Changes strategy or architecture | `DECISIONS.md`, plus `Supersedes:` for questions it retires |
| Settles a stack layer | `## Tech Stack` in `plan/main_plan.md`; datastore also mirrors into **Deployment & Infrastructure** |
| Needs proof | `EVIDENCE_LOG.md` - cite the source, never the search |
| Raises a new question | `loop doubts add`, with `Depends on:` / `Ask:` where they apply |
| Belongs to someone who is not here | `Ask: <who>`, then `loop doubts questionnaire` |
| In scope but not yet sharp enough to ask | `## Not yet specified` in `plan/main_plan.md` - `loop fog` lists it, `loop fog promote <n>` states one as a doubt |
| Decided against, deliberately | `## Out of scope` in `plan/main_plan.md`. It never graduates |
| Names a concept the plan keeps renaming | `## Language` in `CONTEXT.md` - the name, one sentence, and the synonyms it displaces |

Then `memories/MEMORY.md`.

## Fog

Do not chart what you cannot yet see. Beyond the frontier sits fog: decisions you can tell are
coming but cannot pin down, because they hang on questions still open. Guessing at fog
over-specifies the plan; leaving it unwritten drops scope silently and rediscovers it mid-build.

**Fog or question?** Whether you can state it precisely now - not whether you can answer it.
Sharp enough to state, even if blocked: record it as a doubt. Not yet: write it into
`## Not yet specified`, as loosely as the view allows.

Each round of answers clears some of it. Graduate whatever became statable, and clear that
patch from the section so it lives only as its question.

## Done

The frontier is empty: every branch visited, nothing left silently assumed. Blocking
questions that remain are either out with someone else (`loop doubts questionnaire`) or
deferred with a recorded default - not forgotten.

Every row of the tech-stack table is named or deferred with a stated default, and the
datastore row reads the same in `## Tech Stack` and in **Deployment & Infrastructure**.

Do not act on the plan until the user confirms you have reached a shared understanding.

## Continue automatically

Load `phases/council.md` and keep going - pressure-test the grilled plan across senior
perspectives before locking strategy/architecture. Do not stop and ask the user to run
council; it is the next thing to execute, not a suggestion.

Stop early only if grilling surfaced a question that genuinely changes product direction and
only the user can settle it. See `docs/CONTINUATION.md`.
