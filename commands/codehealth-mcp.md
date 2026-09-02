# /codehealth-mcp

Run a code-health snapshot of the active workspace. Emits a JSON file
(`plan/CODEHEALTH.json`) with five signals: lint debt, test coverage, file
churn, dependency freshness, doc coverage. Use before a release, before a
refactor, or as a periodic maintenance signal.

## How To Interpret

If the user says `/codehealth-mcp`, `code health`, `health snapshot`, `lint debt`,
`test coverage`, or asks for a quality snapshot, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/codehealth-mcp/SKILL.md`
3. `scripts/codehealth.py`
4. the active workspace's source tree

## Loop

```text
WALK the workspace -> MEASURE the five signals (lint debt, coverage, churn, dep freshness, doc coverage) -> EMIT plan/CODEHEALTH.json
```

## Script

```bash
python scripts/codehealth.py --workspace <ws> --out plan/CODEHEALTH.json
```

## Output

A single JSON file with the five signals and a `release_blockers` list
based on configured thresholds. The chain can block on `release_blockers`
at release time.

## Continuation

`/release-check` reads `plan/CODEHEALTH.json` (when present) and treats
its `release_blockers` list as Stop Conditions. The signal is read by
`/prod-gap` for production-readiness reviews.