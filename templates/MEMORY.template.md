# Memory

This is the human-mind file for the product loop. Every agent must update it automatically when meaningful progress, blockers, decisions, or next actions change.

## Current Mental State

**Now:** Fresh loop template. Product is not initialized yet.

**Direction:** Unknown until `/plan-loop` gathers product context.

**First step:** Unknown until `/plan-loop` creates `plan/step_01_<slug>.md`.

**Current mode:** Ready for first-run `/plan-loop`.

## What We Did

- Created reusable loop command contracts:
  - `commands/plan-loop.md`
  - `commands/product-develop.md`
  - `commands/loop-engine.md`
- Created canonical cross-tool skill pack in `skills/`.
- Added adapters:
  - `CURSOR.md`
  - `CLAUDE.md`
  - `CODEX.md`
  - `OPENCODE.md`
  - `GROK.md`
  - `API_USAGE.md`
  - `ADAPTERS.md`
- Created `plan/main_plan.md` as an uninitialized product plan template.
- Created `plan/` for future step plans.

## What We Are Doing

- Waiting for the user to run `/plan-loop`.
- On `/plan-loop`, initialize product-specific data automatically.

## What Comes Next

1. Run `/plan-loop`.
2. Ask product initialization questions if needed.
3. Create or update `plan/main_plan.md`.
4. Create `plan/step_01_<slug>.md`.
5. Populate `TASKS.yml`, `GATES.yml`, `DOUBTS.md`, and `HANDOFF.md` for that user's product.

## Operating Memory Rules

- Update this file after every meaningful session.
- Keep this file concise but complete enough for a new agent to understand the product state without asking the user to repeat context.
- Do not duplicate detailed task lists; link to `TASKS.yml`, `HANDOFF.md`, and `DOUBTS.md`.
- If uncertain, write the uncertainty in `DOUBTS.md` and continue only on safe, reversible work.
