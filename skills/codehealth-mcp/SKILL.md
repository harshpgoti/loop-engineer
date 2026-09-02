---
name: codehealth-mcp
description: Stand up a small MCP-style code-health server that exposes a project's quality signals (lint debt, test coverage, churn, dependency freshness) on a single, queryable surface. Use when the chain needs a structured health snapshot of the active project before a release, a refactor, or a `/prod-gap` review.
---

# Code-Health MCP

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline that turns a workspace's quality
signals (lint debt, test coverage, file churn, dependency freshness)
into a single, queryable, **deterministic** surface. The discipline is
MCP-style (the user can ask: "what's the churn in module X?"); the
runtime is a small Python script that reads the workspace and emits a
JSON snapshot. No LLM call.

## When to use

- Before a release: get a single health snapshot to feed into
  `/prod-gap` or `/release-check`.
- Before a refactor: identify the files with the highest churn +
  lowest coverage.
- During a planning phase: get a list of `lint_debt` items so
  `/plan-loop` knows what's already a known issue.
- As a periodic maintenance signal: weekly `/codehealth-mcp` run that
  shows the trend.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A code review | `code-reviewer` |
| A pre-deploy quality gate | `gateguard` |
| A real MCP server deployment | this skill (the runtime is a script) |
| A performance profile | `latency-critical-systems` |

## The Five Signals

| Signal | Source | Use |
|---|---|---|
| **lint_debt** | per-language linter output (ruff, eslint, golangci-lint) | the count of `warning|error` lines, broken down by file |
| **test_coverage** | per-language coverage tool (coverage.py, istanbul) | the line + branch coverage of changed files |
| **churn** | `git log --since=<window> --name-only` | the files with the most commits in the last N days |
| **dep_freshness** | per-language lock file + registry | the count of outdated major-version pins |
| **doc_coverage** | a static walk of `docs/` and a measure of which public surface the docs cover | the percentage of public modules with at least one doc reference |

The five signals are measured deterministically; the output is a JSON
snapshot. The discipline is that *any* consumer (the chain, an agent,
a maintainer) can re-run the script and get the same numbers.

## Workflow

### 1. Run the snapshot

```bash
python scripts/codehealth.py --workspace <ws> --out plan/CODEHEALTH.json
```

The script walks `<ws>/` and emits a single JSON file with the five
signals. No LLM call. The output is small (under 50 KB for most
projects) and JSON-shaped for downstream consumption.

### 2. Bind to a release

`/release-check` reads `plan/CODEHEALTH.json` (when present) and treats
`lint_debt > threshold` or `test_coverage < threshold` as release
blockers. The thresholds are configurable per workspace.

### 3. Compare over time

Append the JSON snapshot to `plan/CODEHEALTH_HISTORY/<date>.json`.
A spike in `churn` without a corresponding `lint_debt` drop is a sign
that the project is moving fast but not paying the debt.

## Output

A single JSON file with the following schema:

```json
{
  "version": 1,
  "workspace": "/abs/path/to/ws",
  "timestamp": 1234567890,
  "signals": {
    "lint_debt": {"total": 23, "by_file": {"src/foo.py": 5, "src/bar.py": 18}},
    "test_coverage": {"lines_pct": 78.3, "branches_pct": 65.1, "by_file": {"src/baz.py": 41.0}},
    "churn": {"window_days": 30, "by_file": {"src/foo.py": 12}},
    "dep_freshness": {"outdated_major": 4, "outdated_minor": 11},
    "doc_coverage": {"public_modules": 22, "documented": 19, "pct": 86.4}
  },
  "release_blockers": ["lint_debt > 0 on src/bar.py: 18 warnings"]
}
```

The `release_blockers` list is the script's verdict: it combines the
signals with the configured thresholds and emits a machine-readable
list of reasons. The chain can block on this list.

## Anti-Patterns

- **A health snapshot that becomes a vanity metric.** The signals are
  inputs to a release decision, not a leaderboard. A project with
  green signals but no users is still a bad project.
- **A snapshot that runs at every commit.** The snapshot is
  expensive (it walks the whole tree). Run it on release, on demand,
  and weekly — not on every push.
- **A snapshot that hides the source of a signal.** The script must
  cite the file + line + reason for every finding. A signal with no
  source is a guess; cite the evidence or drop the signal.
- **A snapshot that over-trusts the linter.** Linters disagree;
  a low `lint_debt` does not mean a low bug rate. The snapshot is
  a starting point, not a verdict.

## Related Skills

- `release-check` - the consumer of the snapshot; treats
  `release_blockers` as Stop Conditions.
- `prod-gap` - the production-readiness report; uses the same
  signals but at the deploy boundary, not the change boundary.
- `qa-validation` - the test suite half; the snapshot is the meta
  view, the test run is the immediate view.
- `living-docs-governance` - the docs side of the same idea; a doc
  drift report is a different kind of health signal.