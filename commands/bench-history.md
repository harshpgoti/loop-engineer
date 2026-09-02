# /bench-history

Record and diff chain benchmarks over time. Wraps /chain-bench to append each run
to benchmarks/<date>.json and emit a trend delta against the prior snapshot. Use
to track chain health across releases, to spot regressions, and to feed a
release-readiness dashboard.

## How To Interpret

If the user says `/bench-history`, `track benchmarks`, `chain trend`, `compare
benchmarks`, or asks to record or diff a chain benchmark, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/bench-history/SKILL.md`
3. `scripts/bench_history.py`
4. `scripts/chain_bench.py` (the snapshot source)
5. the active workspace's `benchmarks/` directory (when present)

## Loop

```text
READ the latest benchmarks/ snapshot -> RUN chain-bench -> APPEND to benchmarks/<date>.json (--append) | READ two snapshots and EMIT a trend delta (--diff)
```

## Script

```bash
python scripts/bench_history.py --workspace <ws> --append
python scripts/bench_history.py --workspace <ws> --diff
python scripts/bench_history.py --workspace <ws> --diff --since-days 7
```

## Output

A single Markdown diff table comparing baseline vs latest, or an
appended snapshot under `benchmarks/<date>.json`.

## Continuation

`/release-check` calls `/bench-history --append` as part of the
release protocol. The trend delta is surfaced to the maintainer as the
single signal of "is the chain getting better or worse?"