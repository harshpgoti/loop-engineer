---
name: release-check
description: Runs a focused pre-production release readiness check and writes RELEASE_CHECK.md. Use when the user types /release-check or asks if the product is ready to launch.
---

# Release Check

## Purpose

Provide a launch-focused gate review before production release or `G-RELEASE-01` approval.

## Read First

- `commands/release-check.md`
- `skills/deployment-plan/SKILL.md`
- `plan/main_plan.md`
- `TASKS.yml`
- `GATES.yml`
- `plan/PROD-GAP.md`
- `docs/TEST_PLAN.md`
- product source tree

## Write

- `RELEASE_CHECK.md`
- `DEPLOYMENT_PLAN.md`
- `.ai/SESSION_LOG.md`

## Checks

- tests
- CI
- env examples
- secrets-like patterns
- docs
- deploy artifacts
- rollback path
- monitoring/ops gaps when visible
- P0 blockers from prod gap analysis

## Optional Script

Use `scripts/release_check.py` for a structured draft, then refine with product-specific release requirements. Run `scripts/deployment_plan.py` to refresh deployment targets and ask only unresolved cloud/LLM questions.

## Closeout

If not ready, route technical blockers to `/product-develop` and human blockers to `DOUBTS.md` and `HANDOFF.md`. Refresh `DEPLOYMENT_PLAN.md` and inform the user about reused vs unresolved deployment decisions.
