---
name: session-recall
description: Recalls relevant past loop sessions from state.db into plan/SESSION_RECALL.md at session start. Use when the user types /session-recall or at the start of /plan-loop, /product-develop, or /loop-engine.
---

# Session Recall

## Purpose

Search `state.db` and inject top hits before planning or building.

## Command

`/session-recall`

## Read First

1. `plan/main_plan.md`
2. `CURRENT_STATE.md`
3. `HANDOFF.md`
4. `plan/SESSION_RECALL.md`

## Script

```bash
python scripts/session_recall.py
loop recall
```

## Bootstrap Order

After recall, session reads should follow:

```text
memories/SOUL.md -> memories/USER.md -> memories/MEMORY.md -> CONTEXT.md -> plan/SESSION_RECALL.md
```

Use `loop bootstrap` to print the resolved list for the active workspace.

## Reuse Rule

If a past session or plan file already answers a question, inform the user and do not ask again unless they want to change it.

## Output

- `plan/SESSION_RECALL.md`
- Query used and hit count
- Top excerpts to reuse
