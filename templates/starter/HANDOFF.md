# Handoff

**Updated:** 2026-06-30  
**For:** Next agent session (any tool)

## Continue Here

This is a fresh loop OS template. Product data is not initialized.

Primary commands:

- `/plan-loop`
- `/product-develop`
- `/loop-engine`

Do **not** scaffold a product repo until `/plan-loop` initializes `plan/main_plan.md` and `plan/`.

## Immediate Next Task

Run `/plan-loop` to initialize product-specific planning.

Deliverables:

1. Ask or infer product name, target user, problem, first product step, constraints, and sensitive data policy.
2. Update `plan/main_plan.md`.
3. Create `plan/step_01_<slug>.md`.
4. Update `memories/MEMORY.md`, `DOUBTS.md`, `TASKS.yml`, `GATES.yml`, and this file.

## After Initialization

| Order | Task ID | Action |
|-------|---------|--------|
| 2 | TASK-002 | Fact-check product assumptions → `EVIDENCE_LOG.md` |
| 3 | TASK-003 | Draft product risk/compliance checklist |
| 4 | TASK-004 | PRD + architecture for first product step |
| 5 | TASK-005 | Product repo bootstrap or connection after `G-ARCH-01` |

## Context For Agents

- Use `/plan-loop` for Step 1.
- Use `/product-develop` for Step 2.
- Use `/loop-engine` for all-in-one gated operation.
- Always update `memories/MEMORY.md`, `DOUBTS.md`, and this file automatically.
- Keep reusable logic in `skills/` and `commands/`.
- Keep product data in `plan/main_plan.md`, `plan/`, `TASKS.yml`, `DECISIONS.md`, and `EVIDENCE_LOG.md`.

## Do Not Do Yet

- Invent product details without user input unless explicitly asked.
- Use real sensitive data before the relevant gate passes.
- Claim product work is complete without tests and gate checks.

## Last Session Summary

Template reset for open-source use. Product-specific data removed. The loop uses tool-neutral canonical skills plus adapters:

- `CURSOR.md`
- `CLAUDE.md`
- `CODEX.md`
- `OPENCODE.md`
- `GROK.md`
- `API_USAGE.md`

Canonical files:

- `skills/`
- `commands/`
- `plan/main_plan.md`
- `plan/`
