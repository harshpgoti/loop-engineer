# /conversation-analyzer

Mine a session transcript for behavioral patterns. Three buckets:
corrections (user corrected the agent), repeated mistakes (same failure
twice or more), prompt-injection attempts (untrusted content steered the
agent). Read-only. Use at /session-end to feed continuous-learning-v2 and
learn-curator.

## How To Interpret

If the user says `/conversation-analyzer`, `analyze the session`, `what did I
correct`, or asks to mine a transcript for patterns, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/conversation-analyzer/SKILL.md`
3. the session transcript (in `state.db` or the session log)
4. the active workspace's learning rules

## Loop

```text
READ the transcript -> CLASSIFY each pattern (Correction / Repeated mistake / Prompt-injection attempt) -> EMIT a report
```

## Output

A Markdown report with the three-bucket classification and a per-pattern
list with transcript position and recommendation.

## Continuation

The chain hands the report to `learn-curator` for promotion. The
`continuous-learning-v2` skill turns the corrections into rules.