# /agent-eval

Head-to-head comparison of coding agents (or agent configurations) on a YAML
task suite, run in isolated git worktrees, scored by code- and model-based
graders, with metrics pass-rate, cost, time, and consistency. Use when changing
model, prompt, or tool configuration to measure the impact, or when picking
between agent providers.

## How To Interpret

If the user says `/agent-eval`, `compare agents`, `measure the impact`, `is the
new model better`, or asks to evaluate agents on a task suite, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/agent-eval/SKILL.md`
3. `evals/suites/<suite>.yaml` (the task suite)
4. the baseline git state

## Loop

```text
FOR each agent in agents[]: CREATE worktree -> RUN task suite -> SCORE per grader -> RECORD run -> REMOVE worktree
```

## Output

`evals/reports/<suite-id>-<date>.md` with:

- Per-task scores per agent
- Aggregate table (pass rate, median time, cost, consistency)
- Recommendation (one paragraph)

## Continuation

A report older than 30 days is stale. Re-run before relying on it. The eval is
a tool for **measuring** change, not a benchmark for vanity.