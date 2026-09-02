---
name: chain-bench
description: Run a benchmark of the chain's own state and surface the numbers as a Markdown report. Use to track chain health over time, to spot regressions, and to populate a release-readiness dashboard. Run on a clean workspace to get a stable baseline; run after a feature to see the delta.
---

# Chain Bench

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic benchmark that reads the chain's own state
(`manifests/`, `skills/`, `commands/`, `state.db`, `plan/`) and emits
a Markdown report. The report is the single source of truth for "how
big is the chain right now?"

## When to use

- After a feature ships, to confirm the chain's surface area is what
  you expect.
- As a release-readiness signal — a chain that has grown by 30%
  in a single round deserves review.
- As a baseline before a refactor — capture the metrics, do the
  refactor, re-run, compare.
- As a periodic maintenance signal — weekly or monthly, to spot
  drift.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A product-level benchmark | `benchmark` (in the active product) |
| A performance test | `latency-critical-systems` |
| A single number, not a chain snapshot | direct `python scripts/chain_bench.py --json` |

## Workflow

### 1. Run the benchmark

```bash
python scripts/chain_bench.py --workspace <le-app-or-product-ws>
```

The script reads:

- `manifests/skill_policy.json` — skills per class.
- `manifests/capabilities.json` — commands per capability.
- `manifests/agents.json` — roles per class.
- `skills/` — on-disk skill inventory.
- `commands/` — on-disk command inventory.
- `plan/` — main plan, step files, feature specs, open doubts.
- `state.db` — recent session history (if present).
- `scripts/test_*.py` — test file count.

### 2. Interpret the report

A small report (under 20 lines) is the goal. A 100-line report means
the chain has grown past the point where one person can hold it in
their head. The right response is to consolidate, not to celebrate.

### 3. Compare over time

Run the benchmark at the end of each round, save the JSON output under
`benchmarks/<date>.json`, and diff. A growing skill count is expected;
growing duplicate activation paths or overlapping roles is a sign
of drift.

## Output

A Markdown report with the following sections:

- **Skills** — total, by class.
- **Commands** — total, by capability.
- **Roles** — total, by class.
- **Plan** — main plan existence + size, step files, feature specs,
  open doubts.
- **Tests** — test file count.
- **State** — `state.db` existence, total sessions, recent 5.

## Anti-Patterns

- **A benchmark that becomes a vanity metric.** The benchmark is a
  signal, not a goal. The goal is a coherent chain; the benchmark
  tells you when the chain has stopped being coherent.
- **A benchmark that runs on a polluted state.** A workspace with
  a half-written `state.db` produces a half-true report. The
  benchmark assumes the state is consistent.
- **A benchmark that includes subjective scores.** The benchmark
  measures counts and sizes; it does not score "quality" because
  quality is what the audit is for.
- **A benchmark that runs on every commit.** The benchmark is a
  periodic signal, not a CI gate. Run it weekly, on release, and
  after a feature.

## Related Skills

- `latency-critical-systems` - the latency discipline; the benchmark
  is the count discipline.
- `agent-sort` - the DAILY vs LIBRARY classification; the benchmark
  shows the totals that classification should reduce.
- `eval-loop` - the per-feature scoring; the benchmark is the
  chain-level scoring.