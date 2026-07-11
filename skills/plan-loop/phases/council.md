# Phase: Product Council

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: council` - run before PRD/architecture lock, major pivots, and development gates.

## Purpose

Make planning decisions sharper by forcing multiple senior perspectives before the agent commits to a roadmap or architecture.

## Required Reads

- `plan/main_plan.md`
- active `plan/step_*.md`
- `DOUBTS.md`
- `EVIDENCE_LOG.md`
- `DECISIONS.md`
- `GATES.yml`

## Council Roles

| Role | Focus |
|------|-------|
| Founder / CEO | Market, urgency, wedge, distribution, kill/keep |
| Product Manager | ICP, workflow, scope, PRD, acceptance criteria |
| CTO / Architect | architecture, data model, integrations, scalability, build/buy |
| Distinguished Engineer | simplicity, failure modes, testability, maintainability |
| Design Reviewer | user flow, onboarding, friction, trust, empty states |
| QA Lead | test plan, regressions, golden cases, release confidence |
| Security / Risk Lead | sensitive data, abuse cases, access control, compliance |
| Release Manager | CI/CD, deployment, rollback, observability |

## Process

1. Read current plan and evidence.
2. For each role, list:
   - strongest concern
   - must-fix before build
   - nice-to-have later
3. Produce a unified recommendation:
   - proceed
   - proceed with constraints
   - block and ask user
   - kill or rethink
4. Add open questions to `DOUBTS.md`.
5. Add durable decisions to `DECISIONS.md`.

## Output

- Council verdict
- Role-by-role concerns
- Required changes
- Open questions
- Gate recommendation

## Next phase

- **Platform scale** (`plan/PLAN_SCALE.md` = platform) → `ultraplan` for the active step.
- **Convenient scale** → create the feature spec, then `spec-clarify`.
