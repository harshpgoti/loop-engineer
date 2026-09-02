# /handoff

Read or write the HANDOFF.md at any chain transition. The hand-off is the durable
record that survives session boundaries, tool switches, and model resets. Use
when a chain run ends, a sub-task hands off to its caller, or a session
resumes.

## How To Interpret

If the user says `/handoff`, `write the handoff`, `what's next`, `update
HANDOFF.md`, or asks to read or write the chain's hand-off, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/handoff/SKILL.md`
3. `HANDOFF.md` (the active workspace)
4. `state.db`, `.loop/active-feature.json`
5. the in-flight `TASKS.yml` task

## Loop

```text
READ the current state (active feature, task, doubts) -> WRITE HANDOFF.md with the 7 fields -> UPDATE state.db
```

## Output

A single `HANDOFF.md` file with the canonical 7 fields. A hand-off
without all seven fields is incomplete; the audit (via
`/self-audit`) flags it.

## Continuation

The next session reads `HANDOFF.md` before any other state. A hand-off
that does not name the receiver or the next concrete action is a
TODO, not a hand-off; the next session cannot continue.