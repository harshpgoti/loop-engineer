---
name: status
description: Shows current workspace, product, gate, task, human blockers, and next recommended command in STATUS.md. Use when the user types /status or asks what is happening now.
---

# Status

## Purpose

Provide a fast operational snapshot without running a full planning or development loop.

## Read First

- `commands/status.md`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md`
- `TASKS.yml`
- `GATES.yml`
- `CURRENT_STATE.md`
- `HANDOFF.md`
- `plan/PROD-GAP.md`

## Write

- `STATUS.md`
- optional note in `.ai/SESSION_LOG.md`

## Must Include

- current workspace
- product name and phase
- active gate
- active task
- open human blockers
- next recommended command

## Optional Script

Use `scripts/status.py` for a structured draft, then refine if needed.

## Closeout

Tell the user the next command and any human blockers that need attention.

`/status` is a fixed snapshot, not a Q&A. If the user wants detail - "why did we decide X?",
"how does Y work?", "what's built vs pending?" - point them at `/ask-loop`
(`skills/ask-loop/SKILL.md`), which answers from full plan and build context.
