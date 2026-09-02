# /strategic-compact

Suggest /compact at phase boundaries rather than arbitrary token thresholds.
Reads the transcript usage and proposes the most valuable compact target. Use
when a long session is approaching the context limit, or when switching tools.

## How To Interpret

If the user says `/strategic-compact`, `when should I compact`, `is this a good
time to compact`, or asks for compact advice, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/strategic-compact/SKILL.md`
3. the active session's transcript-usage signal (provided by the harness)

## Loop

```text
READ transcript usage -> CHECK phase boundary -> PROPOSE compact target (or wait)
```

## Output

- A yes/no recommendation: compact now, or wait for the next phase boundary.
- The specific target file to read on resume (e.g. "compact now; the plan is in
  `plan/main_plan.md`; the implementation tasks are in `TASKS.yml`").
- The threshold being used (200k window: 160k; 1M window: 800k).

## Continuation

The user confirms. The harness runs `/compact` (or its tool-specific equivalent).
The chain resumes with a smaller working set.