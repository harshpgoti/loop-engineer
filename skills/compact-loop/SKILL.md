---
name: compact-loop
description: Compacts long-running product-loop context into COMPACT.md, preserving current state, decisions, doubts, gates, tasks, and next actions. Use when the user types /compact-loop, before tool switches, or during long /loop-engine runs.
---

# Compact Loop

## Purpose

Prevent context-window loss by creating a durable, human-readable context summary.

## When To Use

- User types `/compact-loop`.
- Before switching tools.
- Before or after a long `/loop-engine` run.
- When the chat is getting long.
- When `.ai/SESSION_LOG.md`, `HANDOFF.md`, or active planning docs become hard to scan.

## Required Reads

- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md`
- active `plan/step_*.md`
- `TASKS.yml`
- `GATES.yml`
- `DECISIONS.md`
- `EVIDENCE_LOG.md`
- `HANDOFF.md`
- `.ai/SESSION_LOG.md`

## Write

Update:

- `COMPACT.md`
- `HANDOFF.md`
- `.ai/SESSION_LOG.md`

## Summary Must Preserve

- Product name and status
- Current phase/gate
- Active task
- Latest completed work
- Open doubts
- Decisions
- Evidence status
- Files changed or important files
- Next command
- Do-not-do warnings

## Native Tool Compaction

If the current tool has native context compaction, run it only after `COMPACT.md` is current. The repo summary is the source of truth across tools.

## Output

- Compact summary path
- Next action
- Anything still unsafe or unresolved
