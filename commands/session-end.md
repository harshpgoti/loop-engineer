# /session-end

Always-on memory closeout — run **before stopping** in any tool.

## Agent (mandatory)

After updating `HANDOFF.md`, `DOUBTS.md`, and `memories/MEMORY.md`:

```bash
loop session-end --command "<active-command>" --summary "<one-line progress>"
```

## Default behavior

Memory curation **stages** writes for approval (`loop pending list` / `loop pending approve --all`).

Direct apply (only when user asks):

```bash
loop session-end --apply
```

## Required reads

1. `skills/session-lifecycle/SKILL.md`
2. `plan/SESSION_CLOSEOUT.md` (after script runs)
3. `plan/MEMORY_REVIEW.md`

## Wired into

Every `/plan`, `/product-develop`, `/loop-engine` closeout — always run this last.
