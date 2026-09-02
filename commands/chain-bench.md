# /chain-bench

Run a benchmark of the chain's own state. Emits a Markdown report with skills,
commands, roles, plan, tests, and state metrics. Use to track chain health
over time, to spot regressions, or to populate a release-readiness dashboard.

## How To Interpret

If the user says `/chain-bench`, `measure the chain`, `how big is the chain`,
`chain metrics`, or asks for a chain-state benchmark, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/chain-bench/SKILL.md`
3. `scripts/chain_bench.py`

## Loop

```text
READ manifests + skills + commands + plan + state.db + tests -> EMIT Markdown (and JSON with --json)
```

## Script

```bash
python scripts/chain_bench.py --workspace <le-app-or-product-ws>
python scripts/chain_bench.py --workspace <le-app-or-product-ws> --json
```

## Output

A Markdown report with sections: Skills (total, by class), Commands (total,
by capability), Roles (total, by class), Plan (main plan, step files,
feature specs, open doubts), Tests (test file count), State (`state.db`
existence, total sessions, recent 5).

## Continuation

Save the JSON output under `benchmarks/<date>.json` at the end of each
round. Diff consecutive benchmarks. A growing skill count is expected;
growing duplicate activation paths is a sign of drift.