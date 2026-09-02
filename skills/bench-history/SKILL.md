---
name: bench-history
description: Record /chain-bench snapshots over time. Append each run to a benchmarks/<date>.json history file and emit trend deltas. Use to track chain health across releases, to spot regressions, and to feed a release-readiness dashboard.
---

# Bench History

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for tracking the chain's own
benchmarks over time. The `chain-bench` command emits a single
snapshot; this skill records the snapshot as a dated file in
`benchmarks/` and emits a delta against the prior benchmark.

## When to use

- After every chain release: append the post-release benchmark to
  `benchmarks/<release-date>.json`.
- After every feature that adds 5+ skills or 5+ commands: append a
  pre/post benchmark pair.
- Monthly, as a maintenance signal: run the chain, append the
  benchmark, diff against the prior.
- Before a release decision: see whether the chain has been growing
  or shrinking in scope.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A single benchmark | `/chain-bench` |
| A per-feature eval | `eval-loop` |
| A user-facing dashboard | `/dashboard-builder` (this skill feeds it) |

## The Two Outputs

### 1. Append to `benchmarks/<date>.json`

```bash
python scripts/bench_history.py --workspace <le-app> --append
```

The script reads the latest `benchmarks/<date>.json` (if any), runs
`chain_bench.py --workspace <le-app> --json`, merges the new snapshot
into the history, and writes the result. The history file is a JSON
array of snapshots sorted by timestamp.

### 2. Emit a trend delta

```bash
python scripts/bench_history.py --workspace <le-app> --diff
```

The script compares the latest snapshot to the snapshot from N days
ago (default: 30) and emits a Markdown table with the deltas. The
table is the input to a release-readiness review.

## Anti-Patterns

- **A history that grows unbounded.** The chain ships more skills every
  round; the history file grows monotonically. A history beyond 100
  snapshots is suspect — compress or move to a database.
- **A history that nobody reads.** The trend delta is the value; the
  history file is the artefact. A history with no deltas emitted is
  dead weight.
- **A history that conflates releases and dev runs.** Each snapshot
  should be tagged with `kind: "release" | "dev"`. The trend delta
  filters by kind.
- **A history that includes PII or secrets.** Snapshots are summaries;
  they do not include user input. If a snapshot ever contains PII, the
  history is leaked.

## Related Skills

- `chain-bench` - the single-snapshot command; this skill is the
  history wrapper.
- `dashboard-builder` - the consumer of the trend delta; the
  dashboard can render a "skills over time" sparkline.
- `release-check` - the trigger for appending a release benchmark.