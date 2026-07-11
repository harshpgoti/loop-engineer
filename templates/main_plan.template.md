# Main Plan - {{PRODUCT_NAME}}

Status: **INITIALIZED**

## Product

- **Name:** {{PRODUCT_NAME}}
- **One-line description:** {{ONE_LINE_DESCRIPTION}}
- **Target user:** {{TARGET_USER}}
- **Buyer / decision-maker:** {{BUYER}}
- **Problem:** {{PROBLEM}}
- **First product step:** {{FIRST_STEP}}
- **Constraints:** {{CONSTRAINTS}}
- **Sensitive data / compliance:** {{SENSITIVE_DATA}}
- **Preferred stack:** {{PREFERRED_STACK}}

## Deployment & Infrastructure

Captured during `/plan-loop`. Reused by `/deployment-plan` unless the user changes it.

| Item | Choice |
|------|--------|
| Cloud provider | {{CLOUD_PROVIDER}} |
| Cloud strategy | {{CLOUD_STRATEGY}} |
| Primary region(s) | {{REGIONS}} |
| Compute model | {{COMPUTE_MODEL}} |
| Database hosting | {{DATABASE_HOSTING}} |
| LLM provider | {{LLM_PROVIDER}} |
| LLM model(s) | {{LLM_MODELS}} |
| Embedding provider/model | {{EMBEDDING_MODEL}} |
| Agent runtime | {{AGENT_RUNTIME}} |
| CI/CD platform | {{CICD_PLATFORM}} |
| Secrets management | {{SECRETS_MANAGEMENT}} |

## Product Thesis

{{PRODUCT_THESIS}}

## Step Plan Index

| Step | File | Status |
|------|------|--------|
| 01 | `plan/step_01_{{STEP_SLUG}}.md` | Planning |

## Plan scale

| Field | Value |
|-------|-------|
| Scale | `convenient` or `platform` - see `plan/PLAN_SCALE.md` |
| Platform map | `plan/PRODUCT_MAP.md` when scale is platform |
| Ultraplan tracker | `plan/ULTRAPLAN_STATUS.md` when scale is platform |

Run `loop plan-loop scale --write` after capturing the user's idea.

## Operating Principles

- Evidence before major product decisions.
- Ask hard questions before building.
- Build the smallest useful first step.
- Keep reusable logic out of product-specific files.
- Treat sensitive data carefully and define gates before using it.

## Current Product State

| Area | State |
|------|-------|
| Product | {{PRODUCT_NAME}} |
| Product repo | {{PRODUCT_REPO_STRATEGY}} |
| Customer/user evidence | {{EVIDENCE_STATUS}} |
| Sensitive data policy | {{SENSITIVE_DATA_POLICY}} |
| Next command | `/plan-loop` |

## Open Strategy Questions

See `DOUBTS.md`.

## Tooling References

See `tools/registry.md`.
