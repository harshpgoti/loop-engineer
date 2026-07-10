---
name: plan
description: Runs product planning: initialize a fresh product plan, brainstorm, grill, validate evidence, draft PRD/architecture/ADRs, capture deployment targets early, and prepare implementation tasks. Use when the user types /plan or asks to prepare product development.
---

# Plan

## Purpose

Turn a product idea into a validated, buildable plan. On a fresh clone, initialize product-specific files automatically and capture deployment choices early.

## Command

`/plan`

## Read First

1. `AGENTS.md`
2. `memories/SOUL.md`
3. `memories/USER.md`
4. `memories/MEMORY.md`
5. `DOUBTS.md`
6. `plan/main_plan.md`
7. `plan/`
8. `TASKS.yml`
9. `GATES.yml`
10. `EVIDENCE_LOG.md`
11. `DECISIONS.md`
12. `HANDOFF.md`
13. `templates/plan_deployment_questions.md`
14. `skills/session-lifecycle/SKILL.md`
15. `skills/feature-workflow/SKILL.md`
16. `skills/spec-clarify/SKILL.md`
17. `skills/spec-checklist/SKILL.md`
18. `skills/deployment-plan/SKILL.md`
19. `skills/session-recall/SKILL.md`
20. `skills/memory-review/SKILL.md`
21. `skills/product-council/SKILL.md`
22. `skills/product-grill/SKILL.md`
23. `skills/task-compiler/SKILL.md`
24. `skills/compact-loop/SKILL.md`
25. `skills/ultraplan/SKILL.md`
26. `skills/agent-builder/SKILL.md` (when the product is/includes an AI agent)
27. `skills/research-search/SKILL.md`
28. `skills/model-providers/SKILL.md` (every product needs an LLM provider decision, not just agent-shaped ones)
29. `skills/tool-orchestrator/SKILL.md` (selecting supporting tools/patterns — memory, roles, spec discipline)

## Loop

```text
SESSION-START -> SCALE DETECT -> [CONVENIENT: STEP + FEATURE] | [PLATFORM: MAP -> ULTRAPLAN/step -> FEATURE] -> TASKS -> SESSION-END
```

## Instructions

0. Run `loop session-start --command /plan --text "<user idea>"` (or `loop plan "<idea>"`) and read `plan/PLAN_BOOTSTRAP.md`.
1. `session-start` auto-detects agent-development signals — if `plan/AUTO_AGENT_SKILLS.md` was written, read it and `skills/agent-builder/SKILL.md` before drafting architecture.
3. If **`platform`**: follow bootstrap next step — `skills/ultraplan/SKILL.md` (one step per session). Do not shallow-plan all modules.
4. If **`convenient`**: follow steps below (single step + feature spec).
2. If uninitialized, ask for product name, target user, problem, first product step, constraints, sensitive data, preferred stack, and deployment targets.
3. During planning, capture deployment choices in `plan/main_plan.md` → **Deployment & Infrastructure**:
   - cloud provider
   - single-cloud vs multi-cloud
   - primary region(s)
   - compute model
   - database hosting
   - LLM provider and model(s)
   - embedding provider/model
   - agent runtime
   - CI/CD platform
   - secrets management
4. **Reuse rule:** if a deployment answer already exists in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`, reuse it, inform the user, and do not ask again unless they want to change it.
5. If the user is unavailable, record missing inputs in `DOUBTS.md` and do not invent product-specific facts.
6. Restate the product state from `memories/MEMORY.md` and `plan/main_plan.md`.
7. Review `DOUBTS.md`; ask user questions if available.
8. Validate claims with sources before adding them to product decisions. For research-grounded claims (architecture pattern, eval methodology, benchmark), use `skills/research-search/SKILL.md` (`loop research "<query>"`) and cite the result in `EVIDENCE_LOG.md`.
9. Update `plan/main_plan.md` with product-level strategy and deployment table.
10. Create or update `plan/step_XX_<name>.md` for each product step/module.
11. Create or update active feature spec: `loop feature new "<title>" --step plan/step_XX_<name>.md`, fill `spec.md`, run `/spec-clarify` and `/spec-checklist`, then `feature-plan.md`.
12. Run `skills/task-compiler/SKILL.md` — sync active feature `tasks.md` with `TASKS.yml`.
13. Update `GATES.yml`, `DECISIONS.md`, and `EVIDENCE_LOG.md` as needed.
14. Draft `DEPLOYMENT_PLAN.md` with `python scripts/deployment_plan.py --source plan`.
15. Update `memories/MEMORY.md`, `DOUBTS.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.
16. Run `memory-review` at closeout with `--stage` by default (`loop memory review --stage`).
17. Run `compact-loop` when planning is long, many files changed, the user may switch tools, or the context is getting heavy.
18. Run `loop session-end --command /plan` (mandatory closeout).

## Optional Initializer

```bash
python scripts/init_product.py --name "<product>" --first-step "<step>" --cloud-provider "<cloud>" --cloud-strategy "<single|multi>" --llm-provider "<provider>" --llm-models "<models>"
```

## Output

- Product plan summary
- Deployment decisions captured or reused
- Open user questions
- Evidence added
- Step files created/updated
- Active feature spec status (`plan/features/`)
- Plan scale and ultraplan status (`plan/PLAN_SCALE.md`, `plan/ULTRAPLAN_STATUS.md`)
- `DEPLOYMENT_PLAN.md` draft status
- Gate status
- Compact status
- Next command

## Stop Conditions

Stop and ask if:

- A decision changes the product direction
- Sensitive or regulated data is requested before the relevant gate passes
- The product repo should be created but product/repo strategy is unresolved
- Evidence is too weak for a major architecture or product decision
- Cloud or LLM vendor choice has major cost, compliance, or lock-in impact and is still unresolved
