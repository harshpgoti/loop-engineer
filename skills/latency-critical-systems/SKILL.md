---
name: latency-critical-systems
description: Design and validate latency-critical systems. Defines p99 budgets, hot-path profiling discipline, batching strategies, caching, performance regression detection. Use when a product has a user-visible latency SLO, when building a high-throughput service, or when investigating a performance regression.
---

# Latency-Critical Systems

Inherits `docs/SKILL_CONTRACT.md`.

Latency-critical systems are those where a user-visible delay is part of the
product's value proposition. A web search that takes 200ms is a product; one
that takes 2s is broken. A checkout that takes 1s is a product; one that
takes 10s is abandoned. The skill is the discipline for keeping the latency
budget honest.

## When to use

- A product has a user-visible latency SLO (p50, p95, p99, or all three).
- A new feature is being designed that adds to an existing hot path.
- A performance regression is suspected and the chain needs to triage
  before fixing.
- A queue, cache, or batch system is being scaled and the tail-latency
  story is not yet known.
- A migration or refactor is planned and the latency impact must be
  measured before cutover.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A product with no user-visible latency SLO | `operations` |
| A one-off benchmark | `agent-eval` |
| A CPU/GPU-bound ML serving layer | `ml-engineering` |
| A generic performance bug | `diagnose-loop` |

## Required method

1. **State the latency budget explicitly.** p50, p95, p99, p99.9, in
   milliseconds, per user-visible request. A budget the team cannot
   state is a budget the team cannot enforce.
2. **Identify the hot path.** A hot path is the route or pipeline
   that contributes the most to user-visible latency under load.
   Naming the hot path turns "the system is slow" into "this
   transition is slow."
3. **Measure before optimising.** A profile is the only proof that the
   change targets the actual bottleneck. Cite the profile in the
   commit message.
4. **Batching amortises cost; latency cost is the queue.** Batching
   10 requests into one round trip cuts service cost by 10x but
   adds a queue-wait latency tax. The right batch size is the one
   that fits the budget; cite the math.
5. **Caching amortises reads; staleness is the cost.** A cache hit
   cuts latency; a stale cache serves wrong answers. The cache's
   staleness budget is a product decision; cite it.
6. **Concurrency is parallelism, not latency.** Concurrency cuts
   throughput, not response time. A concurrent fetch that fans out to
   5 services takes the max of the 5, not the sum. A serial fetch
   takes the sum. The two are different latency profiles.
7. **Measure after optimising.** A second profile, in the same
   harness, in the same scenario, is the only proof the change
   worked. A before/after diff in the commit message is the
   durable record.

## Validation

- **Hot-path profile** before and after, with the same load, the same
  scenario, the same harness.
- **p99 budget test** that runs in CI and fails the build on
  regression. A budget that is not in CI is a budget that does
  not exist.
- **Cold-start vs warm-path** split. The first request is always
  slower; the budget's "warm" component is what the user
  experiences; the "cold" component is what the operator
  monitors.
- **Tail-latency test** (p99.9 or p99.99) at the user's expected
  load. The p50 is the typical case; the p99.9 is the
  abandonment case.
- **Backpressure test** that confirms the system degrades
  gracefully when the queue grows. A latency-critical system
  that melts under load is not a latency-critical system.

## Output

Return:

- The latency budget (p50, p95, p99, p99.9) and the user-visible
  operation it applies to.
- The hot path: route, function, or pipeline.
- The profile: before and after, with the same harness.
- The batching and caching decisions, with the math.
- The regression test that lives in CI.
- The expected degradation under load, with the
  backpressure story.
- Findings (with the Pre-Report Gate applied).
- Rollback path.

## Anti-Patterns

- **A "performance fix" without a profile.** A change that targets a
  guess is a change that may not have helped. Cite the profile.
- **A p50 budget that ignores the tail.** The p50 is fine; the p99 is
  the user-facing failure. Optimise for the tail.
- **Batching without queue math.** "Batch 100" is a number; "batch
  100 with a 10ms queue cap" is a design. The queue cap is the
  latency budget's worst-case.
- **Caching without a staleness budget.** A cache that serves stale
  data is a bug. The staleness budget is a product decision.
- **A latency-critical design that "averages out."** The user
  experiences the tail, not the mean. Optimise for the worst
  case the user sees.
- **A regression test that runs on the developer's machine.** The
  user's machine is faster than production. The latency test
  must run in the same environment as production.
- **A "performance review" that is a one-shot profile.** A profile
  is a snapshot; a regression is a trend. Track the latency
  over time.

## Related Skills

- `operations` - the runtime review; this skill is the latency
  subset.
- `diagnose-loop` - the debugging discipline; this skill is the
  design discipline.
- `eval-loop` - the golden-case scoring; the latency regression test
  is a golden case.
- `agent-eval` - the head-to-head agent comparison; useful for
  measuring the latency cost of a model switch.