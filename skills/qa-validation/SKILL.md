---
name: qa-validation
description: Runs product QA and auto-validation: unit tests, integration tests, E2E tests, golden cases, schema checks, tenant isolation checks, and post-development validation. Use after building or before release gates.
---

# QA Validation

## Required Checks

- Unit tests
- Integration tests
- API contract tests
- Database migration tests
- Frontend type/lint/test
- E2E smoke tests
- Golden cases and evals
- Tenant isolation tests
- No-sensitive-data-in-logs tests

## Instructions

1. Read `TASKS.yml`, `GATES.yml`, and product test docs.
2. Run relevant checks for the changed area.
3. Add missing tests when behavior changes.
4. Do not mark work complete without validation.
5. Record failures and gaps in `memories/MEMORY.md` and `HANDOFF.md`.

## Output

- Tests run
- Failures fixed
- Remaining failures
- Gate status for `G-QA-01`
