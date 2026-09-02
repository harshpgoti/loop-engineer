# /adr

Capture an architectural decision as a durable ADR (Architecture Decision Record).

## How To Interpret

If the user says `/adr`, `adr`, `record an architecture decision`, `why did we choose X`,
or asks to lock in a non-trivial choice (framework, library, database, pattern, deployment
shape, auth provider, queue, model tier routing), execute this file directly.

Also run it, unasked, when `/plan-loop` or `/revise-plan` locks a decision whose rationale
survives the session - that is the canonical ADR signal.

## Required Reads

1. `AGENTS.md`
2. `skills/architecture-decision-records/SKILL.md`
3. `docs/adr/` (existing decisions)
4. `plan/main_plan.md` `## Tech Stack`
5. `DECISIONS.md`
6. `EVIDENCE_LOG.md`

## Loop

```text
DETECT DECISION SIGNAL -> RESOLVE EXISTING ADR -> NUMBER NEW ADR -> WRITE FILE -> UPDATE INDEX -> REFERENCE FROM PLAN
```

## Schema (locked)

```markdown
# <number>. <short title>

- **Date:** <YYYY-MM-DD>
- **Status:** proposed | accepted | superseded | deprecated
- **Deciders:** <who decided; named roles>
- **Supersedes:** <ADR numbers or blank>
- **Superseded by:** <ADR numbers or blank>

## Context
<what forces are at play; cite EVIDENCE_LOG entries>
## Decision
<the choice itself; one paragraph>
## Alternatives Considered
<table with option + reason>
## Consequences
### Positive / Negative / Risks
## Lifecycle
<date: status transitions>
```

## Output

1. `docs/adr/NNNN-<slug>.md` path
2. `docs/adr/README.md` updated with a new index row
3. Existing ADR's `Status` updated if applicable
4. One-line citation in `plan/main_plan.md` `## Tech Stack` if the decision is at stack level
5. Entry in `state.db` via session-closeout

## Continuation

The ADR is the canonical place for the decision rationale. Subsequent plans, tasks, and
reviews must cite the ADR number - not re-derive the reasoning in their own. If the chain
makes a contradictory decision later, it must write a new ADR that `Supersedes:` the prior
one. Silent contradiction is a bug.