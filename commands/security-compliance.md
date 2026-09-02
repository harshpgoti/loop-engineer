# /security-compliance

Run the security and compliance review: secrets, sensitive data, tenant
isolation, audit logs, prompt injection, IDOR, dependency exposure, workflow
authorization. Use during planning, development, review, and release. The
skill is wired into the chain; this command is for direct invocation.

## How To Interpret

If the user says `/security-compliance`, `security review`, `compliance check`,
or asks for a security pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/security-compliance/SKILL.md`
3. `skills/safeguard/SKILL.md`
4. `GATES.yml`, `DOUBTS.md`
5. the product source tree
6. the change set under review

## Loop

```text
READ GATES.yml + DOUBTS.md -> ESTABLISH scope and policy threshold -> RUN deterministic checks (secrets, permissions, hooks, MCP, tenant scope) -> EMIT structured findings
```

## Output

- Findings ordered by severity
- Baseline delta, policy outcome, scanner/rule provenance
- Required fixes
- Counsel-needed items
- Gate status for `G-SECURITY-01`, `G-COMPLIANCE-01`, sensitive-data gates

A `fail` outcome is a launch blocker; a `warn` is recorded but does
not block; an `error` outcome (the scan could not establish a
trustworthy result) never becomes a pass.

## Continuation

A failing gate is a Stop Condition; the chain halts; the user resolves
the underlying issue; the chain re-runs. Counsel-needed items are
recorded in `DOUBTS.md` with the user as the named approver.