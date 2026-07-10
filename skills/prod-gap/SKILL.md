---
name: prod-gap
description: Analyzes product requirements, current progress, implementation, gates, tasks, evidence, and docs to produce production-readiness technical and non-technical gaps in plan/PROD-GAP.md. Use when the user types /prod-gap or asks what is missing before launch.
---

# Product Gap Analysis

## Purpose

Create a clear production-readiness gap report between:

- what the product plan requires
- what has been built
- what evidence supports the plan
- what gates still block progress
- what is missing technically and non-technically
- what the agent can fix
- what requires the user or another human

## Read First

- `commands/prod-gap.md`
- `plan/main_plan.md`
- `plan/`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `TASKS.yml`
- `GATES.yml`
- `CURRENT_STATE.md`
- `DECISIONS.md`
- `EVIDENCE_LOG.md`
- `HANDOFF.md`
- Product source tree, if present

## Write

Write or update:

- `plan/PROD-GAP.md`
- `DOUBTS.md` for human-required blockers/questions
- `HANDOFF.md`
- `memories/MEMORY.md`
- `.ai/SESSION_LOG.md`

## Gap Types

### Non-Technical

- unclear ICP/user
- weak problem statement
- missing evidence
- missing pricing/distribution
- unclear success metrics
- open decisions
- unresolved risks
- missing docs or handoff
- legal/contracts/vendor signup/API account/pricing/support/process issues that require a human

### Technical

- missing architecture
- missing data model
- missing APIs
- missing UI flows
- missing tests
- missing CI/CD
- missing security controls
- missing observability
- missing release/rollback path
- implementation does not match plan
- production config, credentials, deploy, monitoring, rollback, performance, data migration, or operational readiness gaps

## Severity

- `P0`: blocks planning, development, release, or safe operation
- `P1`: important gap that should be scheduled soon
- `P2`: useful improvement or later cleanup

## Ownership

- `agent-solvable`: technical or documentation work the agent can perform.
- `human-required`: needs user action such as signing an agreement, creating an account, choosing a vendor, approving spend, providing credentials, legal review, or business decision.
- `shared`: agent can prepare artifacts, but user must approve or complete final step.

## Output Format

`plan/PROD-GAP.md` must include:

- Executive summary
- Current product status
- P0 gaps
- P1 gaps
- P2 gaps
- Technical gaps
- Non-technical gaps
- Agent-solvable blockers
- Human-required blockers
- Gate impact
- Recommended next tasks
- Open questions

## Optional Script

Use `scripts/prod_gap.py` to create a structured draft. The script also scans the product source tree for missing tests, CI, env examples, README, deploy artifacts, TODO/FIXME markers, and secret-like patterns. Then improve the draft with actual product and code analysis.

## Closeout

After writing `plan/PROD-GAP.md`:

1. Add technical P0/P1 blockers to `TASKS.yml`.
2. Add human-required P0/P1 blockers to `DOUBTS.md` and `HANDOFF.md`.
3. If called from `/product-develop` or `/loop-engine`, continue fixing agent-solvable P0/P1 technical blockers when safe.
4. Ask the user for human-required blockers at the end of the loop.
