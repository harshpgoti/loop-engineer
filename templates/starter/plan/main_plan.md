# Main Plan

Status: **UNINITIALIZED**

This file will become the product-specific master plan for whoever downloads this loop OS.

Reusable loop mechanics live in `skills/`, `commands/`, and adapter files. Product-specific planning belongs here and in `plan/`.

## First-Run Rule

When `/plan-loop` runs and this file is still uninitialized, the agent must:

1. Ask the user for product name, target user, problem, first step, constraints, desired build stack, and deployment targets (cloud provider, single vs multi-cloud, LLM provider/model).
2. If the user is unavailable, write questions to `DOUBTS.md`.
3. Replace this template with the user's product plan.
4. Use `templates/main_plan.template.md` and `templates/step_plan.template.md` as structure.
5. Create `plan/step_01_<slug>.md`.
6. Capture deployment choices in `plan/main_plan.md` and `DECISIONS.md`.
7. Update `TASKS.yml`, `GATES.yml`, `memories/MEMORY.md`, `CURRENT_STATE.md`, and `HANDOFF.md`.

## Product

- **Name:** TBD
- **One-line description:** TBD
- **Target user:** TBD
- **Buyer / decision-maker:** TBD
- **Problem:** TBD
- **First product step:** TBD
- **Constraints:** TBD
- **Sensitive data / compliance:** TBD
- **Preferred stack:** TBD

## Deployment & Infrastructure

| Item | Choice |
|------|--------|
| Cloud provider | TBD |
| Cloud strategy | TBD |
| Primary region(s) | TBD |
| Compute model | TBD |
| Database hosting | TBD |
| LLM provider | TBD |
| LLM model(s) | TBD |
| Embedding provider/model | TBD |
| Agent runtime | TBD |
| CI/CD platform | TBD |
| Secrets management | TBD |

## Product Thesis

TBD.

## Step Plan Index

No product steps created yet. First `/plan-loop` should create:

```text
plan/step_01_<slug>.md
```

## Operating Principles

- Evidence before major product decisions.
- Ask hard questions before building.
- Build the smallest useful first step.
- Keep product-specific data out of reusable `skills/` and `commands/`.
- Treat sensitive data carefully and define compliance gates before using it.
- Human approval for risky external actions unless the product plan explicitly allows otherwise.

## Planning Workflow

When `/plan-loop` runs:

1. Update this file for product-level strategy.
2. Create/update `plan/step_XX_<module>.md` for module-level detail.
3. Add evidence to `EVIDENCE_LOG.md`.
4. Add decisions to `DECISIONS.md`.
5. Add tasks to `TASKS.yml`.
6. Add doubts to `DOUBTS.md`.
7. Select tools from `tools/registry.md` only when useful.

## Current Product State

| Area | State |
|------|-------|
| Product | Uninitialized |
| Product repo | TBD |
| Customer/user evidence | None |
| Sensitive data policy | TBD |
| Next command | `/plan-loop` |

## Development Workflow

When `/product-develop` runs:

1. Select the active step file from `plan/`.
2. Use `TASKS.yml` and `GATES.yml`.
3. Build only the next safe task.
4. Validate with QA/security/compliance skills.
5. Update memory and handoff.

## Open Strategy Questions

See `DOUBTS.md`.

## Tooling References

See `tools/registry.md`.
