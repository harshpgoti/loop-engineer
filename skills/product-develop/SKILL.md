---
name: product-develop
description: Runs product engineering from the approved plan: frontend, backend, database, agent loops, QA, auto-validation, docs, security, compliance, CI/CD, and deployment readiness. Use when the user types /product-develop or asks to start development.
---

# Product Develop

## Purpose

Build the product from `plan/main_plan.md` and `plan/` while respecting gates.

## Command

`/product-develop`

## Read First

1. `plan/SESSION_MANIFEST.md` (after `loop session-start`)
2. `AGENTS.md`
3. `memories/SOUL.md`
4. `memories/USER.md`
5. `memories/MEMORY.md`
6. `DOUBTS.md`
7. `plan/main_plan.md`
8. relevant `plan/step_*.md`
9. `plan/SESSION_RECALL.md`
10. `plan/AUTO_SKILLS.md` (if present)
11. `plan/AUTO_AGENT_SKILLS.md` (if present)
12. `skills/feature-workflow/SKILL.md`
13. `skills/spec-clarify/SKILL.md` (when requirements blocked)
14. `skills/feature-converge/SKILL.md`
15. `skills/frontend-animation/SKILL.md` (when AUTO_SKILLS present)
16. `skills/agent-builder/SKILL.md` (when AUTO_AGENT_SKILLS present or the task involves building an AI agent)
17. `skills/implementation-planner/SKILL.md`
18. `skills/code-reviewer/SKILL.md`
19. `skills/qa-validation/SKILL.md`
20. `skills/security-compliance/SKILL.md`
21. `skills/prod-gap/SKILL.md`
22. `skills/deployment-plan/SKILL.md`
23. `skills/compact-loop/SKILL.md`
24. `skills/memory-review/SKILL.md`
25. `skills/docs/SKILL.md` (Documentation domain — PRDs, ADRs, API specs, runbooks)
26. `skills/model-providers/SKILL.md` (when the LLM provider/model decision is still open)
27. `skills/tool-orchestrator/SKILL.md` (selecting supporting tools — memory, sandboxing, RAG, roles)
28. `TASKS.yml`
29. `GATES.yml`
30. `HANDOFF.md`
31. Active feature: `.loop/active-feature.json` → `spec.md`, `feature-plan.md`, `tasks.md`
32. `skills/session-lifecycle/SKILL.md`
33. product repo instructions if a product repo exists

## Gate Classification

- Planning docs: allowed.
- Reversible synthetic scaffold: allowed when doubts are recorded.
- Production sensitive-data workflow: blocked until relevant gates pass.
- High-risk external action: human approval required unless the product plan says otherwise.

## Build Loop

```text
SESSION-START -> SELECT TASK (from active feature tasks.md + TASKS.yml) -> READ MANIFEST/AUTO-SKILLS -> PLAN DIFF -> BUILD -> TEST -> FEATURE-CONVERGE -> SESSION-END
```

Run `loop session-start --command /product-develop` first and `loop session-end` last. Frontend motion/3D skills and agent-development skills are both auto-detected at session-start and included in the manifest when signals match (`plan/AUTO_SKILLS.md`, `plan/AUTO_AGENT_SKILLS.md`) — re-run `loop auto-agent-skills --write` only if the task description changed after session-start.

## Development Domains

1. Monorepo scaffold
2. Frontend — motion/3D skills auto-selected via `frontend_skill_router.py` → `plan/AUTO_SKILLS.md`
3. Backend
4. Database and migrations
5. Authentication, RBAC, tenant isolation
6. Audit logging
7. Secure file ingestion
8. Deterministic parsers and validators
9. Agent loops with schema validation — see `skills/agent-builder/SKILL.md` when the product itself is/includes an AI agent
10. QA and auto-validation
11. Documentation
12. Security checks
13. Compliance checks
14. CI/CD
15. Deployment readiness

## Required Closeout

- Run relevant tests or record why not.
- Update active feature `tasks.md` checkboxes and `TASKS.yml` status.
- Run `loop feature converge` (or `/feature-converge`) — also runs on `loop session-end` for `/product-develop`.
- Run `prod-gap` after meaningful development work.
- Run `deployment-plan` at loop closeout to write `DEPLOYMENT_PLAN.md`.
- Reuse cloud, LLM, and deployment answers already in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`.
- Ask the user only for unresolved deployment questions.
- Fix safe P0/P1 technical blockers found by `prod-gap` when in scope.
- Add human-required blockers from `prod-gap` to `DOUBTS.md` and `HANDOFF.md`.
- Update `memories/MEMORY.md`, `DOUBTS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, `DEPLOYMENT_PLAN.md`, and `.ai/SESSION_LOG.md`.
- Run `compact-loop` when development is long, many files changed, the user may switch tools, or the context is getting heavy.
- Run `loop session-end --command /product-develop` (mandatory; includes converge + memory-review staging).

## Output

- What was built
- Tests/checks run
- Security/compliance status
- Files changed
- Production gap status
- Deployment plan status
- Human-required blockers
- Compact status
- Next task
