# /harness-optimizer

Eval-driven harness tuning via pass@k and pass^k. Snapshot before and after
every change. BLOCKED on security-sensitive diffs. Use when the model, prompt,
or tool configuration changes and the impact on golden cases is unknown.

## How To Interpret

If the user says `/harness-optimizer`, `tune the harness`, `compare harness
configs`, `run the eval suite`, or asks to optimize the chain's agent
configuration, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/harness-optimizer/SKILL.md`
3. the active workspace's eval suite
4. the active workspace's golden-case files

## Loop

```text
SNAPSHOT before (pass@1, pass@3, pass^3) -> MAKE one harness change -> SNAPSHOT after -> COMPARE the deltas -> DECIDE (keep, revert, iterate)
```

## Output

A before/after pair of snapshots, the metrics deltas, the cost delta, and
a one-paragraph decision.

## Continuation

The chain halts on any `pass^k` regression on a release-critical path.
Security-sensitive diffs are BLOCKED; the user is the final reviewer.