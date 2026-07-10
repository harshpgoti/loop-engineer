---
name: security-compliance
description: Reviews product work for security, privacy, sensitive-data handling, tenant isolation, audit logs, secrets, prompt injection, and human approval boundaries. Use during planning, development, review, and release.
---

# Security Compliance

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
2. Identify risks with severity.
3. Mark counsel-needed issues in `DOUBTS.md`.
4. Update compliance docs and `memories/MEMORY.md`.

## Output

- Findings ordered by severity
- Required fixes
- Counsel-needed items
- Gate status for `G-SECURITY-01`, `G-COMPLIANCE-01`, and sensitive-data gates
