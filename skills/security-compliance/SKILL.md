---
name: security-compliance
description: Reviews product work for security, privacy, sensitive-data handling, tenant isolation, audit logs, secrets, prompt injection, and human approval boundaries. Use during planning, development, review, and release.
---

# Security Compliance

Inherits `docs/SKILL_CONTRACT.md`.

## Hard Rules

- No real sensitive or regulated data until the relevant gate passes.
- No sensitive data in logs, fixtures, screenshots, or third-party prompts.
- All tenant data is server-scoped by `org_id`.
- High-risk external actions require human approval in v1.

## Review Areas

- Product-specific regulatory requirements
- Vendor/subprocessor risk
- Secrets management
- Encryption
- Audit logging
- IDOR and tenant isolation
- Prompt injection
- Workflow authorization
- Incident response

## Instructions

1. Read `GATES.yml`, `DOUBTS.md`, and relevant docs.
2. Establish scan scope, policy threshold, baseline, trusted roots, and excluded generated/vendor paths before scanning.
3. Run deterministic checks first: secrets, permissions, hooks, MCP/tool configuration,
   instruction injection, unsafe execution, dependency exposure, tenant scope, and sensitive-data flows.
4. Emit structured findings using `docs/SKILL_CONTRACT.md`: stable rule ID and fingerprint,
   severity, confidence, location, evidence, remediation, and provenance.
   Use `scripts/assurance_findings.py` for baseline deltas, policy verdicts, and SARIF.
5. Deduplicate by fingerprint. Mark baseline findings as unchanged/new/resolved; never erase
   an issue because it was known. Exceptions require owner, rationale, scope, and expiry.
6. Verify high-severity findings independently and fail closed when required evidence or
   scanner provenance is missing.
7. Mark counsel-needed issues in `DOUBTS.md` and update compliance evidence and memory.

## Policy outcome

- `pass`: no finding crosses the active policy threshold.
- `warn`: evidence is complete but non-blocking risk remains.
- `fail`: a threshold is crossed, required evidence is missing, or verification failed.
- `error`: the scan itself could not establish a trustworthy result; never convert this to pass.

## Output

- Findings ordered by severity
- Baseline delta, policy outcome, scanner/rule provenance, and evidence-pack location
- Required fixes
- Counsel-needed items
- Gate status for `G-SECURITY-01`, `G-COMPLIANCE-01`, and sensitive-data gates
