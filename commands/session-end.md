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

## How To Interpret

If the user says `/session-end`, the user invokes the chain's closeout, or a coding agent reaches the natural end of a session, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `commands/session-end.md` (this file)
3. `skills/session-lifecycle/SKILL.md`
4. `state.db`, the active feature pointer, the in-flight task

## Loop

1. RUN `memory-review` (default staged mode for production workspaces)
2. RUN `compact-loop` if the session was long or the context is heavy
3. APPEND a one-line entry to `state.db` summarising the session
4. UPDATE `HANDOFF.md` with the next concrete action

## Output

1. `state.db` row appended
2. `HANDOFF.md` updated
3. `plan/MEMORY_REVIEW.md` written (or staged)
4. Next command

## Continuation

A session that ended in a Stop Condition is resumed by `/session-start`. A session that ended cleanly is a natural place to start a new chain run.
