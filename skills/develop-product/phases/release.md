# Phase: Release

> Loaded by `skills/develop-product/SKILL.md` when `BUILD PHASE: release` - the build is
> complete and the remaining work is getting it shippable. Load only this file.

## Purpose

Close the production gaps: security, compliance, deployment, CI/CD.

## Read First

1. `plan/BUILD_CONTEXT.md`
2. `skills/security-compliance/SKILL.md`
3. `skills/prod-gap/SKILL.md`
4. `skills/deployment-plan/SKILL.md`
5. `skills/cicd-release/SKILL.md`
6. `plan/PROD-GAP.md`, `DEPLOYMENT_PLAN.md`

This is the only phase that loads these four skills - which is why they are not in the
other phases' read lists.

## Process

1. **Run the gap analysis**: `loop prod-gap`. Work its P0s, then P1s.
2. **Security and compliance** via `skills/security-compliance/SKILL.md`. Secrets,
   tenant isolation, dependency audit. Nothing regulated moves before
   `G-SENSITIVE-DATA` passes.
3. **Deployment plan** - `loop deployment-plan`. Reuse cloud/LLM answers already in
   `DECISIONS.md` - every scope reads the same file, so nothing is inherited across a boundary.
4. **CI/CD** via `skills/cicd-release/SKILL.md`.
5. **Release readiness**: `loop release-check`. `error` findings are launch blockers,
   including unresolved findings in any sub-product.

## Human approval

Deploying, spending, publishing and anything irreversible or external needs explicit
user approval (`AGENTS.md` #5). Prepare the change and ask - do not execute it and report.

## Continue automatically

- **Gaps closed, no approval needed** -> continue through the checklist.
- **An action needs approval, or a blocker is human-owned** -> Stop Condition. Name the
  action, what it will do, and what you need from the user.

## Output

Gaps closed, scan results, deployment plan state, release-check verdict, and the exact
list of things awaiting a human.
