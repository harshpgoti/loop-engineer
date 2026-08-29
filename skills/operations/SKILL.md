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
