# /performance-optimizer

Algorithmic complexity + Web Vitals + bundle analysis. Targets O(n^2) -> O(n),
Core Web Vitals budgets, and bundle-size regressions. Use when a hot path is
slow, when a page-load budget is breached, or when a bundle-size alert fires.

## How To Interpret

If the user says `/performance-optimizer`, `profile this`, `why is it slow`,
`bundle is too big`, or asks for a performance fix, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/performance-optimizer/SKILL.md`
3. the active workspace's source tree
4. the project's profiling tools (cProfile, Lighthouse, bundle analyzer)

## Loop

```text
STATE the budget (p99 < 10ms, LCP < 2.5s, etc.) -> PROFILE the hot path -> CHANGE one thing at a time -> RE-PROFILE -> RECORD the before/after in the commit
```

## Output

A before/after pair of profiles, the bottleneck identified, the change
made, the new budget met (yes/no), and the CI test that catches a
regression.

## Continuation

The chain halts on any test failure or budget regression. The next
`/latency-critical-systems` run verifies the system-wide budgets.