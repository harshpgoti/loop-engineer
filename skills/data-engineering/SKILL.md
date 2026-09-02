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

## Pre-Report Gate

Each HIGH or CRITICAL must clear four questions before it ships. Drop or downgrade if
any answer is "no":

1. Can I name the exact column, query, table, or file under concern, with the diff or
   migration reference?
2. Can I describe the user-visible failure mode - what data ends up wrong, missing, or
   exposed, and to whom?
3. Have I confirmed the rule still applies after the migration / pipeline change, not
   against a stale schema or cached fixture?
4. Is the severity defensible at this stage of the product, not just in principle?

A clean data-engineering run is a valid outcome. Stating "no findings" beats manufacturing
one to look thorough.

## Common False Positives

Skip these unless the data product or stage of work shows otherwise. Each is a pattern the
LLM reviewer will reach for; in this codebase or stage, it is almost always wrong.

- "Add an index" on a table that is read <10 times/day. Indexes are a build cost; add them when
  a query plan proves they pay back, not because they sound right.
- "Use UUID instead of auto-increment PK" without naming the multi-region or distributed-write
  reason. Single-region, single-writer apps are fine with serial PKs.
- "Denormalize for performance" when the join is on a foreign key with an existing index.
  Denormalization fixes hot-path latency, not every slow query.
- "Add a soft-delete column" when the data is regulated and must be erased on request, not
  marked deleted. Soft delete is a UX choice; erasure is a compliance one.
- "Add a `created_at`/`updated_at` on every table" when no consumer reads them and no audit
  trail is in scope. Columns are a maintenance cost.
- "Use a separate read replica" at <1k daily active users. Read replicas pay back at scale;
  premature replication is operational drag.
- "Switch to `bigint` IDs" on a table that will not exceed 2^31 rows in the product's lifetime.
  `int` is fine; cite the growth plan that proves otherwise.
- "Add row-level security" when the product is single-tenant. RLS is the right answer for
  multi-tenant; for single-tenant it adds a filter the query planner may not optimize.
- "Add a cache layer" when the read path is sub-100ms and the dataset fits in memory.
  Caching fixes a measured latency budget, not a vague worry.
- "Migration is irreversible" on a forward-only expand-contract migration that already has a
  rollback contract in `DECISIONS.md`. Reuse the recorded policy.
- "Foreign key missing" on a polymorphic association or an event-log row that intentionally
  has no FK. The reviewer missed the design.
- "Add a unique constraint" on a column whose duplicates are a known feature (audit log of
  retries, idempotency keys, time-series samples). Cite the product rule that proves uniqueness.
- "Schema column should be `NOT NULL`" when the column represents optional metadata by design
  (e.g., a soft `deleted_at`). Nullability is a product decision.
- "Add a database view for query X" when X is used once and the join is six lines. Views are a
  reuse boundary; premature views are documentation debt.


## Stop Conditions and Rollback

A mutating skill declares when to halt and how to revert, before it runs. This section
is required by the canonical skill contract (`docs/SKILL_CONTRACT.md` "Risk and approval")
and is the E3 pattern adopted in round 4.

### When to stop

- **Three failed attempts at the same step.** Retrying past three means the
  hypothesis is wrong, not the execution. Stop, record what was tried, and
  escalate to the user as a doubt.
- **A change introduces more errors than it resolves.** Net negative progress
  is a regression, not a fix. Revert the change; record the failure mode.
- **A gate fails that the plan said must pass.** A gate is a contract; a
  failing gate is the chain telling you the work is not done. Stop and resolve.
- **The active task's `acceptance` criteria become unreachable** because of
  upstream changes. The plan is no longer valid; the task needs re-design,
  not more attempts.
- **Cost drift outside the budget.** A skill that consumes tokens or dollars
  unboundedly is a runaway; stop and report.

### When to escalate to the user

- **High-risk external actions** (publish, deploy, spend, destructive,
  privileged) require explicit user approval per `AGENTS.md` #5. The skill
  prepares the change, names the risk, and waits.
- **A blocker that is human-owned.** The blocker is a question only the
  user can answer (a stakeholder's call, a missing credential, a sign-off).
  Record it in `DOUBTS.md` and `HANDOFF.md`; do not invent an answer.
- **A goal-direction change.** The plan no longer matches what the user
  wants. The chain halts; the user re-plans.

### Rollback path

- **A single-task rollback** is `git revert <task-sha>` (or `git restore` for
  staged-only changes) followed by re-running the active feature's
  `converge-report` to confirm the rollback did not regress the rest of
  the build.
- **A multi-task rollback** is a feature-level revert: identify the feature
  commit range from `.loop/active-feature.json`, revert the range, then run
  `feature-converge` to confirm the surface is clean.
- **A state-only rollback** (files, configs, but no code) is a `git restore
  <path>` + `git clean -fd <path>` for the recorded paths. The skill's
  output records which paths it touched; the rollback reverses exactly
  those.
- **A data-only rollback** is database- and tenant-scoped; record the
  affected rows in the change record, run the inverse migration, and
  verify the diff matches the change record before declaring done.
- **A deploy rollback** is the prior version's artifact promoted through
  the same path the deploy took; `cicd-release/SKILL.md` carries the
  per-deploy rollback procedure.

A rollback that cannot be performed in one step is a planning problem.
Stop and re-plan; do not chain partial rollbacks.
