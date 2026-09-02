# /operations

Run the production operations review: observability, SLOs, incident
response, backups, capacity, cost, recovery. Use for runtime reliability and
operational readiness. The skill is wired into the chain; this command is
for direct invocation.

## How To Interpret

If the user says `/operations`, `ops review`, `SLO check`, `runbook check`, or
asks for an operations pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/operations/SKILL.md`
3. `GATES.yml`, `DOUBTS.md`
4. the production environment, monitoring, alerting

## Loop

```text
READ critical journey + SLO + alert -> INSTRUMENT actionable metrics without secrets -> TEST backup, failover, rollback -> EMIT findings
```

## Output

- SLO and monitoring coverage
- Validation evidence (health, readiness, alert, synthetic-journey, restore, rollback, failure exercise)
- Failure-exercise evidence plus on-call ownership
- Rollback or recovery path
- Approval status
- Residual reliability risk
- Findings (with the Pre-Report Gate applied)

## Continuation

A deploy without tested rollback is a Stop Condition. An alert that
fires for nothing is a finding; an alert that does not fire is a
finding. The chain halts on either.