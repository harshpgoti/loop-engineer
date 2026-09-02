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

## Grill catalog (technical and non-technical)

The areas above are the topic headlines; this catalog is the working list of questions
under them. Ask whichever the current frontier exposes. Each entry carries a default so
the build inherits a stated fallback instead of a silent one. `Why it matters` is the
sentence you tell the user when a question feels obvious and they ask why you are asking.

Ask a question only when it is on the frontier. If the answer was already settled in
`DECISIONS.md`, in a prior session, or by a parent sub-product, reuse it (`AGENTS.md` #15)
and tell the user you are reusing it.

### Product, user, and buyer

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Who exactly pays for this, and who signs the cheque? | The named user is also the buyer. | Two different people buy differently: the user buys workflow, the buyer buys outcomes. A plan that names only the user often stalls at approval. |
| What does the buyer read or hear before saying yes? | A 90-second demo on real data. | Forces the build toward the smallest thing the buyer will see, not the largest thing the team wants to ship. |
| What does the user do **today** that this replaces? | Spreadsheet or email. | The replacement workflow is the wedge. A new tool with no incumbent workflow is a new habit to teach. |
| What is the user's frequency? Daily, weekly, monthly? | Daily. | Frequency drives cost-per-use ceiling, latency budget, and whether you can afford a 30-second cold start. |
| What is the first session meant to do? | One concrete thing the user wanted done. | First-session outcomes predict retention more than feature breadth. |
| When does the user give up and switch back? | After two failed attempts. | Names the failure budget. |
| What does "done" look like for one user, on one day? | One saved artifact or one sent message. | A concrete artifact beats a feature list. |

### Distribution, pricing, and commercial

| Q | Default if unavailable | Why it matters |
|---|---|---|
| How is this sold: self-serve, sales-led, partner, marketplace? | Self-serve free trial. | Sales-led changes the entire UX (admin roles, seats, SSO). |
| What is the unit of pricing: seat, usage, transaction, flat? | Per seat, monthly. | Determines every quota, billing-event, and refund path. |
| What is the **price** the user will pay before they ask the boss? | A number that fits inside their discretionary budget, not procurement. | Procurement buys risk-averse; the buyer buys speed. |
| Where does revenue land: first purchase, expansion, renewal? | First purchase. | Tells you which motions get product investment now. |
| What is the kill criterion - the metric below which you shut this down? | A 30-day retention number stated explicitly. | Without this, the project outlasts its evidence. |

### Legal, compliance, and data

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Will this handle personal data, financial data, health data, or minors' data? | No to all four. | Triggers GDPR/HIPAA/COPPA/PCI obligations; defaults to "no" mean the design stays simple. |
| Whose data is on the screen? Whose data is in the logs? | The end user's own data only. | Tenants and PII share one rule: never log it, never display it in someone else's session. |
| Is the product multi-tenant? | Yes. | Forces server-side scoping on every query from day one. |
| What jurisdictions does the data live in or move through? | One region; pick the one closest to the user. | Multi-region adds a quiet 6–8 weeks of work. |
| Does anything leave the user's session into a third party (analytics, LLM, support)? | Anonymised usage analytics only. | Surfaces a hidden "send data to a third-party provider" decision before it ships. |
| What records must be kept, for how long, and who can read them? | Application logs only, 30 days, engineers only. | Audit posture is a build decision, not a runtime afterthought. |
| What is the breach-notification path? | The CTO is paged; user is notified within 72 hours. | Has to exist before any sensitive data is collected. |

### Operations, support, and on-call

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Who is on call at 03:00? | One named person; rotation weekly. | "We'll figure it out" is a hiring decision the build inherits. |
| What does the runbook look like for the first three failures? | Three failure modes each with one paragraph. | If the runbook does not exist, the pager is just blame. |
| How does the user report a problem? | In-app button + email. | The channel shapes how fast you learn what's broken. |
| How long can the product be down before users churn? | One business day. | Drives SLO and on-call staffing. |
| What data is restored, and from where, on disaster? | The database, from the last 24h snapshot. | Backup is a product decision. |
| How are environments separated: dev, staging, prod? | Three named environments with separate credentials. | Cross-environment accidents are the most common production incident. |

### Security and threat model

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Who is the attacker? | A bored logged-in user trying to see another tenant's data. | The cheapest threat model beats no threat model. |
| What is the most damaging single thing a logged-in user can do? | Read one other tenant's record. | If you cannot name it, you cannot test against it. |
| Are secrets stored in env vars, secret manager, or files? | Secret manager. | Files in git are the most common leak. |
| What happens if an employee laptop is stolen? | Full-disk encryption, MFA, SSO revoke in 5 minutes. | One sentence per control; gaps become tasks. |
| What dependencies need a vulnerability scan? | All of them, on every build. | A single unmaintained dep can take the whole app down. |

### Design, UX, and accessibility

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Who is excluded from this UI by default, and what would unblock them? | Keyboard-only users. | Names the minimum bar; the rest is improvement. |
| What is the empty state? What is the error state? What is the "this took too long" state? | A sentence per state. | Three states define whether the screen is finished. |
| What is the slowest acceptable interaction? | 100ms feedback, 1s save. | Latency is a design decision. |
| What is the language and tone for error messages? | Short, blame-free, name the next step. | Tone is part of the product. |
| Will this UI be localized? | English only at launch. | Each locale roughly doubles the surface to maintain. |
| What user research has actually happened, and what is still assumed? | Five conversations in the last 30 days. | "We should talk to users" is not research. |

### Engineering, architecture, and quality

| Q | Default if unavailable | Why it matters |
|---|---|---|
| What is the single thing that, if it fails, takes the product down? | The primary database. | Names the dependency the SLA is built around. |
| What is the **first** thing to scale: requests, data, users, models? | Users. | Pick one. "All of them" is not an architecture. |
| What is the migration policy: forward-only, reversible, or expand-contract? | Expand-contract, forward-only. | Migrations are the most expensive silent bug. |
| What is the testing bar for a task to be marked done? | TDD per `skills/tdd/SKILL.md`. | "Looks done" is not a bar. |
| What is the rollback path for a deploy that goes wrong? | Revert the deploy. | Without this, a bad deploy is a permanent incident. |
| What logs are kept, at what level, for how long? | Application info, 30 days. | Logging is a product decision. |
| What is the on-call signal-to-noise ratio? | One alert per 100 deploys. | A pager that fires for nothing is one that is ignored for everything. |
| What is the build's forbidden dependency: no internet at build time, no native binaries, no GPL? | No native binaries on the user's machine. | Naming it up front prevents an audit-time panic. |

### Data, ML, and LLM

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Where does the training or prompt data come from, and is it licensed? | First-party data only. | Data lineage is the most common audit failure. |
| What is the unit of cost: token, request, document, model-load? | Per token, per request. | Names the budget guardrail. |
| What is the model-tier routing: when does this go to the cheapest model that works? | Default cheap, escalate on quality regression. | One routing rule saves 80% of LLM spend. |
| What is the eval set, and what is the threshold to ship? | One golden case per user-visible behavior, 95% pass. | "We tested it" without a number is not testing. |
| What happens when the model is unavailable? | Cached fallback + queue. | LLM downtime is the new 503. |
| What PII goes into prompts, into logs, and into the model provider? | None of the above, ever. | Defaults to "no" stay simple. |
| Is there a human-in-the-loop path for low-confidence outputs? | Yes, with explicit "AI suggested" labeling. | Hidden AI is a trust killer. |

### Integrations, vendors, and lock-in

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Which vendor, if any, is acceptable to be locked into? | Cloud provider and LLM provider. | Lock-in is fine if named; surprise lock-in is the problem. |
| What is the data-egress plan if we switch vendors in 12 months? | Standard export in CSV or JSON. | Names whether exit is a feature or a project. |
| What is the SLA we need from this vendor? | 99.9% availability, 4-hour support. | Without an SLA, every outage is a fight. |
| Are we willing to send data to this vendor? | Only the data they need, anonymised where possible. | Surfaces "send data to a third-party provider" before it ships. |
| What is the integration's failure mode? | Degrade silently and surface a clear user message. | Vendor outages are guaranteed; the product must behave. |

### People, team, and timing

| Q | Default if unavailable | Why it matters |
|---|---|---|
| Who is the decision maker for non-trivial pivots? | One named person, named in `DECISIONS.md`. | "The team" decides slowly; one person decides at all. |
| Who is the technical owner for the first 90 days? | One named engineer. | The plan inherits an owner, not a committee. |
| What is the team's prior experience with this stack? | Pick a stack the team has shipped before. | New stack + new product = 2× the timeline. |
| What is the budget for the first three months: hours, dollars, infra? | Stated in numbers, not ranges. | A range is a guess with plausible deniability. |
| What is the deadline, and what is the consequence of missing it? | No hard deadline; ship when it's right. | Artificial deadlines bake in shortcuts. |
| What is the kill criterion for this product line at 90 days? | A single stated metric. | Without it, every quarter is "give it more time." |

### Meta and process

| Q | Default if unavailable | Why it matters |
|---|---|---|
| How will we know this is working, before the metrics tell us? | A daily conversation with a real user. | Lagging metrics lie for the first 90 days. |
| What is the smallest release we can put in front of a real user in the next 14 days? | A clickable prototype, not a deploy. | Names the smallest thing worth testing. |
| What is the anti-metric - the thing we explicitly do not want to maximise? | Time-on-platform past one hour. | Anti-metrics prevent success-the-villain. |
| What does "post-launch v0" look like? | A versioned changelog, on-call coverage, weekly review. | Names what stops being optional once shipped. |

### When to stop grilling

The frontier is empty when:
- every row of the tech-stack table is named or deferred with a stated default;
- the buyer, the user, the data, the on-call, and the kill criterion are all named;
- the cheapest defensible answer fits on one screen.

If a question needs a fact from the environment (what the code already does, what a vendor's
pricing is, what a regulator requires), go get it. Do not block the whole round on a single
lookup - a lookup in flight is an unsettled prerequisite, so only questions downstream of it
wait. Ask the rest of the frontier now (`plan-loop/phases/grill.md` - "Finding facts is your
job, never the user's").

After the user confirms a shared understanding, load `phases/council.md` - pressure-test the
grilled plan across senior perspectives before locking strategy or architecture. Do not stop
and ask the user to run council; it is the next thing to execute.

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
