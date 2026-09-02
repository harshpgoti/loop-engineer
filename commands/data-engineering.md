# /data-engineering

Run the data engineering review: data models, migrations, pipelines, quality
controls, lineage, retention, tenant-safe access. Use when work changes
stored, transformed, imported, exported, or analytical data. The skill is
wired into the chain; this command is for direct invocation.

## How To Interpret

If the user says `/data-engineering`, `data review`, `migration check`, or asks
for a data pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/data-engineering/SKILL.md`
3. `GATES.yml`, `DOUBTS.md`
4. the migrations and schema files
5. the pipeline definitions

## Loop

```text
READ schema + migrations + pipeline -> STATE source, owner, classification, schema, freshness, volume, retention -> EMIT findings (completeness, uniqueness, validity, consistency, timeliness)
```

## Output

- Schema/migration changes
- Validation evidence (forward/recovery, idempotency, replay, compatibility)
- Data-quality thresholds with explicit failure routing
- Access-control, retention, deletion, tenant-isolation tests
- Lineage and retention impact
- Findings (with the Pre-Report Gate applied)
- Rollback or recovery path
- Remaining approval requirements

## Continuation

A migration is forward-only in production; expand-contract is the
default. A migration that cannot be rolled back is a planning problem,
not a build-time surprise — escalate to the user.