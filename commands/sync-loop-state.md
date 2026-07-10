# /sync-loop-state

Reconcile product-loop state files when memory, handoff, tasks, gates, or compact summaries drift apart.

## How To Interpret

If the user says `/sync-loop-state`, `sync loop state`, `reconcile state`, or state files look inconsistent, execute this file directly.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files in the registered product workspace.

1. `AGENTS.md`
2. `skills/sync-loop-state/SKILL.md`
3. `memories/MEMORY.md`
4. `HANDOFF.md`
5. `TASKS.yml`
6. `GATES.yml`
7. `COMPACT.md`
8. `plan/PROD-GAP.md`
9. `CURRENT_STATE.md`

## Loop

```text
READ STATE FILES -> DETECT DRIFT -> APPLY SAFE FIXES -> WRITE SYNC_REPORT.md -> UPDATE MEMORY/HANDOFF
```

## Rules

- Do not overwrite product decisions or task content.
- Safe fixes only: missing pointers, sync notes, and obvious handoff/compact references.
- Record drift instead of guessing when reconciliation is ambiguous.

## Optional Script

```bash
python scripts/sync_loop_state.py
```

Custom workspace:

```bash
python scripts/sync_loop_state.py --workspace ../product
```

## Output

Return:

1. `SYNC_REPORT.md` path
2. Drift items found
3. Safe fixes applied
4. Next recommended command
