# /release-check

Run a focused pre-production release readiness check before launch or release-gate approval.

## How To Interpret

If the user says `/release-check`, `release check`, `ready for production`, `pre-release`, or `launch checklist`, execute this file directly.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files in the registered product workspace.

1. `AGENTS.md`
2. `skills/release-check/SKILL.md`
3. `skills/deployment-plan/SKILL.md`
4. `plan/main_plan.md`
4. `TASKS.yml`
5. `GATES.yml`
6. `plan/PROD-GAP.md`
7. `docs/TEST_PLAN.md`
8. Product source tree

## Loop

```text
READ PLAN/GATES/PROD-GAP -> SCAN SOURCE TREE -> CHECK TESTS/CI/ENV/SECRETS/DOCS/DEPLOY -> WRITE RELEASE_CHECK.md -> UPDATE DEPLOYMENT_PLAN.md
```

## Checks

- tests
- CI
- env examples
- secrets-like patterns
- docs
- deploy artifacts
- rollback readiness
- monitoring/ops gaps when visible
- P0 blockers from `plan/PROD-GAP.md`
- unresolved deployment questions in `DEPLOYMENT_PLAN.md`

## Optional Script

```bash
python scripts/release_check.py
```

Custom workspace:

```bash
python scripts/release_check.py --workspace ../product
```

## Output

Return:

1. `RELEASE_CHECK.md` path
2. Release status
3. Blockers and warnings
4. Deployment plan status
5. Next recommended command
