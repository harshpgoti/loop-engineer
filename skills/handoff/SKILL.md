---
name: handoff
description: Owns the discipline of writing HANDOFF.md at every chain transition. The hand-off is the durable record that survives session boundaries, tool switches, and model resets. Use whenever a chain run ends, a sub-task hands off to its caller, or a session resumes.
---

# Handoff

Inherits `docs/SKILL_CONTRACT.md`.

A small discipline skill that makes `HANDOFF.md` the canonical
hand-off surface. The chain has many skills that write to it
(`/session-end`, `/plan-loop`, `/develop-product`, `/plan-orchestrate`,
`/release-check`, `/feature-converge`); this skill is the source of
truth for *what* HANDOFF.md must contain and *how* to write it well.

## When to use

- A chain run ends (any command's terminus, any Stop Condition, any
  `loop session-end`).
- A sub-task hands control back to its caller (e.g. `/plan-loop`
  hands off to `/develop-product`).
- A session resumes and a previous `HANDOFF.md` must be interpreted.
- A scope change: the active sub-product changes, the active feature
  changes, the active task changes.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A short-lived internal note (use a TODO in the task body) | `/task` tools |
| A per-file change (the commit message) | git |
| A human-readable summary for non-engineers | `/docs` |

## The 7-Field Format

Every `HANDOFF.md` has the same seven fields. The order is fixed. Empty
fields are recorded as "—"; the absence of a field is the bug.

```markdown
# HANDOFF

**Date:** <ISO 8601 with timezone>
**Last command:** <the command that wrote this>
**Active feature:** <feature id, or "—">
**Active task:** <task id, or "—">
**Sub-product / scope:** <slug, or "—">
**Session id:** <the state.db row id>

## State
<one paragraph: what changed in this run; what is true now>

## Open questions
- <doubt ids and one-line descriptions>

## Next concrete action
1. <the exact command, task, or manual action>
2. <fallback if the first is blocked>
```

A hand-off with all seven fields filled is complete. A hand-off with
"open questions" empty is a sign that the run finished without leaving
a thread for the next session; the next session will rediscover the
question.

## Workflow

### 1. The writing rule

A skill that mutates state writes the hand-off at the end of its
work, before the chain halts or the next skill starts. The hand-off
is **not** a "nice to have"; it is the durability contract.

The hand-off is the **only** place the next session reads the prior
state from. `state.db` is searchable but lossy; `HANDOFF.md` is the
single source of truth for the immediate next action.

### 2. The reading rule

A skill that resumes a chain reads the hand-off first, before any
other state. The hand-off is authoritative for the next action;
state.db is authoritative for history.

### 3. The handoff between roles

When a role hands off to another role (e.g. `architect` -> `builder`),
the hand-off is a single `HANDOFF.md` update. The sender writes;
the receiver reads. The hand-off names the receiver:

```markdown
## Next concrete action
1. The `builder` role picks up at T-007 step 3 (auth middleware).
2. The `builder` runs `/develop-product` on T-007.
```

A handoff that does not name the receiver is a TODO, not a handoff.

## Output

A single `HANDOFF.md` file with the seven fields. The chain's
`loop session-end` reads it; the chain's `loop session-start` writes
it (or accepts the prior one).

## Anti-Patterns

- **A HANDOFF.md that says "see memory."** The hand-off is the memory;
  pointing the next session at memory is circular.
- **A HANDOFF.md that says "TBD."** The hand-off is the answer; "TBD"
  is the failure to decide.
- **A HANDOFF.md that lists every open doubt.** The hand-off lists
  the doubts that block the next action, not every open doubt in
  the workspace. A long doubt list is a fog report, not a hand-off.
- **A HANDOFF.md that is not written.** A run that ends without a
  hand-off is a run that the next session cannot continue. The
  chain is broken in that case; `/session-end` is the only safe
  recovery.
- **A HANDOFF.md that contradicts state.db.** The hand-off is the
  present; `state.db` is the past. A contradiction means a session
  ended without writing the hand-off. The next session must
  reconcile, not pick a winner.

## Related Skills

- `session-lifecycle` - the always-on session management; this
  skill is the HANDOFF.md discipline.
- `plan-loop` - the planning chain; writes a hand-off at the end
  of planning.
- `develop-product` - the build chain; writes a hand-off at the
  end of each task and at the end of the run.
- `feature-converge` - the post-build drift check; writes a
  hand-off if drift is found.
- `release-check` - the pre-launch gate; writes a hand-off if
  blockers are open.
- `prod-gap` - the production-readiness report; writes a hand-off
  when blockers are escalated.