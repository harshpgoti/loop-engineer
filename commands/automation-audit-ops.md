# /automation-audit-ops

Run an audit of every automation the chain runs (CI workflows, scheduled
jobs, hooks, scripts, harnesses). Surface dead, broken, or unowned
automations. Use during a release, after adding a new hook, or as a periodic
maintenance signal.

## How To Interpret

If the user says `/automation-audit-ops`, `audit automations`, `find dead hooks`,
`is this CI still running`, or asks for an automation health check, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/automation-audit-ops/SKILL.md`
3. `scripts/automation_audit.py`
4. the LE app's manifests, hooks, harnesses, scripts, and CI

## Loop

```text
WALK the LE app's automation surface -> CLASSIFY each automation (healthy / stale / unowned / risky) -> EMIT plan/AUTOMATION_AUDIT.md
```

## Output

A single Markdown report with the four categories and a per-automation
list. The report is read-only; the maintainer triages.

## Continuation

Stale or risky automations become Stop Conditions in the next release
check. Unowned automations require the maintainer to assign an owner
before the next audit.