---
name: upgrade-loop-engineer
description: Safely upgrades Loop Engineering OS while preserving product plans, memory, tasks, gates, evidence, decisions, handoffs, compact summaries, and product docs. Use when the user types /upgrade-loop-engineer or asks how to update the tool without losing data.
---

# Upgrade Loop Engineer

## Purpose

Update reusable loop-engineering files without overwriting user product state.

## Read First

- `commands/upgrade-loop-engineer.md`
- `docs/UPGRADE.md`
- `memories/MEMORY.md`
- `HANDOFF.md`
- `COMPACT.md`

## Protected Product-State Files

Never overwrite:

- `plan/main_plan.md`
- `plan/`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `TASKS.yml`
- `GATES.yml`
- `HANDOFF.md`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `EVIDENCE_LOG.md`
- `COMPACT.md`
- `.ai/`
- `docs/`

## Safe Process

1. Run or recommend `/compact-loop` first.
2. Identify setup:
   - separate `loop-engineer/` and `product/`
   - embedded copy inside product repo
3. For separate setup, update only `loop-engineer/`.
4. For embedded setup, run `scripts/upgrade_loop_engineer.py` dry-run first.
5. Apply only after dry-run confirms protected files are untouched.
6. Run `scripts/migrate_workspace.py` on the product workspace.
7. Run validators, then `/doctor` and `/status`.
8. Update `memories/MEMORY.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.

## Output

- Detected setup
- Protected files status
- Files to update
- Backup location
- Validation result
- Next command
