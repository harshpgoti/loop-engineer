---
name: sync-loop-state
description: Reconciles MEMORY, HANDOFF, TASKS, GATES, COMPACT, and PROD-GAP drift and writes SYNC_REPORT.md. Use when the user types /sync-loop-state or state files look inconsistent.
---

# Sync Loop State

## Purpose

Keep durable loop state aligned so the next agent does not follow stale handoff or gate information.

## Read First

- `commands/sync-loop-state.md`
- `memories/MEMORY.md`
- `HANDOFF.md`
- `TASKS.yml`
- `GATES.yml`
- `COMPACT.md`
- `plan/PROD-GAP.md`
- `CURRENT_STATE.md`

## Write

- `SYNC_REPORT.md`
- safe updates to `memories/MEMORY.md` and `HANDOFF.md`
- `.ai/SESSION_LOG.md`

## Rules

- Do not overwrite product decisions or task content.
- Record ambiguous drift instead of guessing.
- Prefer pointers and sync notes over destructive edits.

## Optional Script

Use `scripts/sync_loop_state.py` for deterministic drift detection and safe fixes.

## Closeout

Recommend `/status` after sync so the user can see the reconciled snapshot.
