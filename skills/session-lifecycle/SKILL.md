---
name: session-lifecycle
description: Always-on session start/end for any tool. Run loop session-start before work and loop session-end before stopping. Regenerates plan/SESSION_MANIFEST.md and stages memory review.
---

# Session Lifecycle (Always-on)

## Purpose

Persistent memory that works in **Cursor, Claude Code, Codex, OpenCode, Grok, or any LLM with filesystem access** - not tied to one IDE.

## Commands

| When | Command | Slash |
|------|---------|-------|
| **Before any loop work** | `loop session-start` | `/session-start` |
| **Before stopping** | `loop session-end` | `/session-end` |

Optional flags:

```bash
loop session-start --command /develop-product --tool cursor
loop session-end --summary "Built hero section; next: API wiring"
```

## What session-start does

1. Ensures memory layout (`memories/`, `state.db`, etc.)
2. Recalls past sessions → `plan/SESSION_RECALL.md`
3. Auto-selects frontend skills → `plan/AUTO_SKILLS.md` (if signals match)
4. Auto-detects AI-agent-development signals → `plan/AUTO_AGENT_SKILLS.md` (if signals match) - same mechanism as frontend skills, see `skills/agent-builder/SKILL.md`
5. Runs a bidirectional product-tree sync:
   - main product: refreshes `SUBPRODUCTS.md` and publishes generated `PARENT_CONTEXT.md` to every linked child
   - sub-product: refreshes `PARENT_CONTEXT.md` and the parent's `SUBPRODUCTS.md`
6. Writes **`plan/SESSION_MANIFEST.md`** - ordered file list every agent must read (includes active feature when set)
7. Logs to `state.db`

## What session-end does

1. Curates memory (dedupe, trim, closeout proposals)
2. Writes `plan/MEMORY_REVIEW.md`
3. **Writes** `memories/MEMORY.md` for this workspace - no approval step
4. Runs `feature converge` for mutating planning/development commands when an active feature exists
5. Re-syncs the product tree so parent and child generated views include this command's results
6. Writes `plan/SESSION_CLOSEOUT.md`
7. Logs closeout to `state.db`

Nothing is left for the user to run. `.loop/pending/` collects only writes that
need a human decision - a parent workspace proposing into a sub-product, and
agent-authored skill files - and a single-product loop never fills it.

## Parent-context assimilation

For a sub-product, `PARENT_CONTEXT.md` is an input to the command, not a report for
the user to process later. Before doing its own planning or development, every
mutating command must resolve the derived parent findings and fold accepted constraints
into the sub-product's own plan/spec/tasks in the same run. Apply an unambiguous
recommendation automatically; ask only when accepting or declining changes product
direction. The workspace boundary still holds: the parent publishes generated context,
while the sub-product alone authors its plan and code.

The user does not run `loop scope check` or `/feature-converge` between commands.
Those remain explicit diagnostic commands for a requested mid-session recheck only.

## Agent rules (all tools)

1. **First action** when user runs `/plan-loop`, `/develop-product`, `/loop-engine`, or any product work: `loop session-start`
2. **Read** `plan/SESSION_MANIFEST.md` and every file it lists
3. **Last action** before ending the turn/session: update `HANDOFF.md` + `memories/MEMORY.md`, then `loop session-end`
4. Do not skip because the tool changed - memory lives in the workspace, not the chat

## What HANDOFF.md has to carry

The next agent starts cold. `HANDOFF.md` is the only thing that survives the gap, so it is
written for someone with no memory of this session and no way to ask you a question.

**Reference, never restate.** Anything already captured elsewhere - a spec, a decision, a
task's acceptance criteria, a commit, a diff - gets named by its path, not copied. A copy goes
stale the moment the original moves, and a handoff full of stale copies is worse than a short
one. Say what changed and where it lives.

Four things, in this order:

1. **Continue here** - the state the next agent inherits, in a few sentences. What is done,
   what is verified, and what must not be repeated.
2. **The immediate next action** - one thing, specific enough to start on. Not a menu.
3. **What is waiting on an input you do not control** - the task, and the exact input that
   unblocks it. This is what stops the next session re-attempting work that cannot succeed.
4. **Load these** - the command to run, and the skills that apply to this particular work.
   The next agent cannot infer that a red test means `skills/diagnose-loop/SKILL.md`, or that
   a seam decision means `skills/codebase-design/SKILL.md`. Name them.

**Redact.** `AGENTS.md` #6 applies here too: no credentials, no regulated data, no customer
identifiers - not in a path, a sample payload, or a quoted error.

## Idempotent

Safe to run `session-start` multiple times per day; each run refreshes recall and manifest.

## See also

- `docs/SESSION_LIFECYCLE.md`
- `skills/session-recall/SKILL.md`
- `skills/memory-review/SKILL.md`
