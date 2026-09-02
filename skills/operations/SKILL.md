---
name: operations
description: Designs and validates production operations, observability, SLOs, incident response, backups, capacity, cost, and recovery. Use for runtime reliability and operational readiness.
---

# Operations

Inherits `docs/SKILL_CONTRACT.md`.

## Required method

1. Define owner, critical journey, SLI, SLO, alert threshold, and error budget.
2. Instrument actionable metrics, logs, and traces without secrets or sensitive payloads.
3. Define capacity, scaling limits, quotas, cost guardrails, and degradation behavior.
4. Test backup restoration, failover, rollback, and dependency outage behavior.
5. Create runbooks for detection, triage, containment, recovery, communication, and review.
6. Require approval before production mutation, spend, traffic shift, or destructive recovery.

## Validation

- Health, readiness, alert, and synthetic-journey checks
- Restore and rollback evidence tied to environment and artifact version
- Failure exercise evidence plus on-call ownership and escalation verification

## Output

Return changes, SLO and monitoring coverage, validation evidence, structured findings,
rollback or recovery path, approval status, and residual reliability risk.

## Pre-Report Gate

Each HIGH or CRITICAL must clear four questions before it ships. Drop or downgrade if
any answer is "no":

1. Can I name the exact SLI, SLO, alert, runbook step, or operational artifact (with
   path and version) under concern?
2. Can I describe the user-visible failure mode - what breaks, for whom, for how long,
   in what scenario?
3. Have I confirmed the rule still applies against the current deployment shape, not
   against a stale runbook or a forgotten staging environment?
4. Is the severity defensible at this stage of the product, not just in principle?

A clean operations review is a valid outcome. Stating "no findings" beats manufacturing
one to look thorough.

## Common False Positives

Skip these unless the production system or stage of work shows otherwise. Each is a
pattern the LLM reviewer will reach for; in this codebase or stage, it is almost always
wrong.

- "Add a circuit breaker" on a synchronous call between services in the same region with
  a 50ms timeout. Circuit breakers are for cross-region / external calls; the reviewer
  missed the locality.
- "Cache everything" when the data is per-user, real-time, and not read-mostly. Caching
  fixes a measured hot-path; cite the access pattern.
- "Add retries" on an idempotent operation that already has retry-with-jitter and
  exponential backoff in its SDK. The reviewer missed the existing config.
- "Add monitoring" on a metric that is already exported via the platform's standard
  collector (Cloud Run metrics, Prometheus scrape, etc.). Verify the alert exists before
  flagging.
- "Define SLO" on a one-shot internal CLI that runs once per build. SLOs are for
  always-on user-facing journeys.
- "Add a runbook" when the failure mode is "the build broke" and the runbook is the CI
  pipeline's own retry / red-build workflow. The reviewer missed the existing automation.
- "Increase timeout" when the dependency's documented SLA is below the current timeout;
  raising it past the SLA just moves the failure downstream.
- "Add a health check" when the platform already provides one (Kubernetes liveness,
  Cloud Run startup probe). Cite the probe before flagging.
- "Add rate limiting" on an internal API that is only reachable from the same VPC. Public
  rate limiting is the right answer; internal shaping is a different decision.
- "Encrypt data in transit" on a connection that is already HTTPS / mTLS by default. The
  reviewer should cite the actual cipher before flagging.
- "Back up this table" when the table is regenerated from source data on every deploy.
  Backups are for state that is not reconstructible.
- "Add audit logging" on an internal admin action that already emits an audit event via
  the platform's structured-logging pipeline. Cite the event before flagging.
- "Failover to another region" without naming the latency cost, the data residency
  implications, and the cost of running hot standby. Multi-region is a paid decision.
- "Set the on-call rotation" when the team is one person or the rotation is already
  configured in the incident tool. The reviewer should cite the current config.


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
