# /session-end

Always-on memory closeout - run **before stopping** in any tool.

## Agent (mandatory)

After updating `HANDOFF.md`, `DOUBTS.md`, and `memories/MEMORY.md`:

```bash
loop session-end --command "<active-command>" --summary "<one-line progress>"
```

## Default behavior

Memory curation **writes** this workspace's `memories/MEMORY.md` directly. The loop
maintains its own memory; the user is never left with a queue to drain.

Stage for approval instead (only when the user asks):

```bash
loop session-end --stage
```

## Required reads

1. `skills/session-lifecycle/SKILL.md`
2. `plan/SESSION_CLOSEOUT.md` (after script runs)
3. `plan/MEMORY_REVIEW.md`

## Wired into

Every `/plan-loop`, `/develop-product`, `/loop-engine` closeout - always run this last.
