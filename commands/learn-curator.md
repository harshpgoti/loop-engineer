# /learn-curator

Promote eligible observations to the recursive-decision ledger or to
skill/command proposals. Use at /session-end when learning candidates exist;
complements the existing continuous-learning-v2 documentation skill.

## How To Interpret

If the user says `/learn-curator`, `promote observation`, `curate learnings`,
`/learn` (the v2-runtime version), or asks to surface learning candidates, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/learn-curator/SKILL.md`
3. `skills/continuous-learning-v2/SKILL.md`
4. `.loop/learning/observations.jsonl` (the active workspace)
5. `memories/MEMORY.md`, `state.db`

## Loop

```text
READ observations -> COMPUTE candidates (3+ sessions, 0.8+ confidence) -> APPLY promotion gate -> SURFACE eligible candidates (one at a time) -> STAGE record under .loop/pending/
```

## Output

- One Stop Condition with multiple-choice options per eligible candidate
  (recommended answer: stage the promotion).
- A staged record at `.loop/pending/learning-<fingerprint>.json`.
- A short digest at `plan/LEARN_DIGEST.md`.

## Continuation

The next `/memory-review` reads the staged records and either commits
to `memories/MEMORY.md` (project-scope) or rejects with a reason. A
candidate that the user defers or rejects stays in
`observations.jsonl` and is re-evaluated on the next curator run.

## Related Skills

- `continuous-learning-v2` - the v2 model documentation; this
  command is the runtime.
- `memory-review` - the consumer of the staged records.
- `recursive-decision-ledger` - the analogous skill for architecture
  decisions.