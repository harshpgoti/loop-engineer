---
name: session-lifecycle
description: Always-on session start/end for any tool. Run loop session-start before work and loop session-end before stopping. Regenerates plan/SESSION_MANIFEST.md and stages memory review.
---

# Session Lifecycle (Always-on)

## Purpose

Persistent memory that works in **Cursor, Claude Code, Codex, OpenCode, Grok, or any LLM with filesystem access** — not tied to one IDE.

## Commands

| When | Command | Slash |
|------|---------|-------|
| **Before any loop work** | `loop session-start` | `/session-start` |
| **Before stopping** | `loop session-end` | `/session-end` |

Optional flags:

```bash
loop session-start --command /product-develop --tool cursor
loop session-end --summary "Built hero section; next: API wiring"
```

## What session-start does

1. Ensures memory layout (`memories/`, `state.db`, etc.)
2. Recalls past sessions → `plan/SESSION_RECALL.md`
3. Auto-selects frontend skills → `plan/AUTO_SKILLS.md` (if signals match)
4. Auto-detects AI-agent-development signals → `plan/AUTO_AGENT_SKILLS.md` (if signals match) — same mechanism as frontend skills, see `skills/agent-builder/SKILL.md`
5. Writes **`plan/SESSION_MANIFEST.md`** — ordered file list every agent must read (includes active feature when set)
6. Logs to `state.db`

## What session-end does

1. Curates memory (dedupe, trim, closeout proposals)
2. Writes `plan/MEMORY_REVIEW.md`
3. **Stages** memory updates in `.loop/pending/` (default — user approval via `loop pending approve`)
4. Writes `plan/SESSION_CLOSEOUT.md`
5. Logs closeout to `state.db`

User approves staged memory: `loop pending approve --all`

## Agent rules (all tools)

1. **First action** when user runs `/plan-loop`, `/product-develop`, `/loop-engine`, or any product work: `loop session-start`
2. **Read** `plan/SESSION_MANIFEST.md` and every file it lists
3. **Last action** before ending the turn/session: update `HANDOFF.md` + `memories/MEMORY.md`, then `loop session-end`
4. Do not skip because the tool changed — memory lives in the workspace, not the chat

## Idempotent

Safe to run `session-start` multiple times per day; each run refreshes recall and manifest.

## See also

- `docs/SESSION_LIFECYCLE.md`
- `skills/session-recall/SKILL.md`
- `skills/memory-review/SKILL.md`
