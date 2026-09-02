# /latency-critical-systems

Run the latency-critical design review. Use when a product has a user-visible
latency SLO, when designing a hot path, when investigating a regression, or
when scaling a queue/cache/batch system.

## How To Interpret

If the user says `/latency-critical-systems`, `latency review`, `p99 budget`,
`hot-path review`, or asks for a latency pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/latency-critical-systems/SKILL.md`
3. `GATES.yml`, `DOUBTS.md`
4. the current profile (if any) and the latency budget
5. the load model (requests/sec, concurrency, payload size)

## Loop

```text
READ budget + hot path + profile -> STATE the budget explicitly -> MEASURE before optimising -> OPTIMISE batching / caching / concurrency -> MEASURE after -> CI regression test
```

## Output

- The latency budget (p50, p95, p99, p99.9) and the user-visible operation
- The hot path: route, function, or pipeline
- The profile: before and after, with the same harness
- Batching and caching decisions, with the math
- The regression test that lives in CI
- The expected degradation under load
- Findings (with the Pre-Report Gate applied)
- Rollback path

## Continuation

A latency budget that is not in CI is a budget that does not exist. The
chain files a `TASKS.yml` entry for the regression test. A regression
that exceeds the budget is a Stop Condition.