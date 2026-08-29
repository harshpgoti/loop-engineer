---
name: data-engineering
description: Designs and validates data models, migrations, pipelines, quality controls, lineage, retention, and tenant-safe access. Use when work changes stored, transformed, imported, exported, or analytical data.
---

# Data Engineering

Inherits `docs/SKILL_CONTRACT.md`.

## Required method

1. State source, owner, classification, schema, freshness, volume, and retention contracts.
2. Design migrations for compatibility, safe retry, validation, and rollback.
3. Check completeness, uniqueness, validity, consistency, and timeliness.
4. Preserve lineage from source through transformations to every consumer.
5. Scope tenant-owned access on the server and test cross-tenant denial.
6. Use synthetic or de-identified fixtures; keep sensitive data out of tests and prompts.

## Validation

- Migration forward/recovery, idempotency, replay, and compatibility tests
- Data-quality thresholds with explicit failure routing
- Access-control, retention, deletion, and tenant-isolation tests where applicable

## Output

Return changes, validation evidence, lineage and retention impact, findings, rollback or
recovery path, and remaining approval requirements.
