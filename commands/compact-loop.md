# /compact-loop

Compact the current product-loop context into a durable summary so long-running loops can continue across context-window limits and tool switches.

## How To Interpret

If the user says `/compact-loop`, `compact context`, `summarize context`, or a loop is running for a long time, execute this file directly.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but compact the registered product workspace.

1. `AGENTS.md`
2. `skills/compact-loop/SKILL.md`
3. `memories/MEMORY.md`
4. `DOUBTS.md`
5. `plan/main_plan.md`
6. `plan/`
7. `TASKS.yml`
8. `GATES.yml`
9. `DECISIONS.md`
10. `EVIDENCE_LOG.md`
11. `HANDOFF.md`
12. `.ai/SESSION_LOG.md`

Product-state files must come from the product workspace, not from the reusable `loop-engineer/` repo.

## Loop

```text
READ STATE -> SUMMARIZE -> WRITE COMPACT.md -> UPDATE HANDOFF -> OPTIONALLY NATIVE COMPACT
```

## Steps

1. Read the required state files.
2. Preserve decisions, unresolved doubts, active gates, current task, changed files, and next command.
3. Write or update `COMPACT.md`.
4. Update `HANDOFF.md` with the next action and a pointer to `COMPACT.md`.
5. Append a note to `.ai/SESSION_LOG.md`.
6. If the current tool has native context compaction, use it after `COMPACT.md` is written.

## Optional Script

```bash
python scripts/compact_context.py
```

For a parent workspace setup:

```bash
python loop-engineer/scripts/compact_context.py --workspace product
```

## Output

Return:

1. What was compacted
2. Where the compact summary lives
3. Open doubts
4. Active task/gate
5. Next command
