---
name: cicd-release
description: Builds and validates CI/CD and release readiness: GitHub Actions, Docker, migrations, staging deploys, smoke tests, rollback, monitoring, and release gates. Use for deployment and release work.
---

# CI/CD Release

## Scope

- GitHub Actions
- Docker and Docker Compose
- Database migration checks
- Build artifacts
- Staging deployment
- Smoke tests
- Rollback plan
- Monitoring checks
- Release checklist

## Gates

- `G-QA-01`
- `G-SECURITY-01`
- `G-COMPLIANCE-01`
- `G-RELEASE-01`
- `G-PILOT-01`

## Rules

- CI must run tests and security checks before deployment.
- Staging uses synthetic data until sensitive-data gates pass.
- Every deployment needs rollback instructions.
- Release status must be reflected in `memories/MEMORY.md`, `HANDOFF.md`, and `DEPLOYMENT_PLAN.md`.

## Output

- Pipeline changes
- Checks run
- Deployment status
- Rollback path
- Deployment plan updates
- Gate status
