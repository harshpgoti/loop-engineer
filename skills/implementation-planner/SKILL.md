---
name: implementation-planner
description: Plans implementation like a senior engineer before coding: reads the active task, identifies files/modules, risks, tests, rollout, and rollback. Use inside /product-develop before editing code.
---

# Implementation Planner

## Purpose

Prevent sloppy implementation by planning the smallest safe diff.

## Required Reads

- `TASKS.yml`
- `GATES.yml`
- active `plan/step_*.md`
- `DECISIONS.md`
- `CONTEXT.md` - the repo's own names for things; use them
- `skills/codebase-design/SKILL.md` - module, interface, depth, seam, adapter
- product repo structure

## Planning Checklist

- What behavior changes?
- What files/modules are likely touched?
- **Which seam does this change sit behind, and which seam do its tests observe from?**
  Prefer an existing seam to a new one, and the highest one that reaches the behaviour. Name
  them before writing a test (`skills/tdd/SKILL.md`).
- If frontend motion/3D signals exist: run `python scripts/frontend_skill_router.py --write` and read `plan/AUTO_SKILLS.md`
- What data model or API contracts change?
- What tests must be added or updated?
- What security/risk checks apply?
- What docs must change?
- What rollback path exists?

## Output

Before coding, write a short implementation plan:

- task id
- intended files
- acceptance criteria
- the seams the tests observe from
- test plan
- risks
- rollback/handoff notes

Then implement only that scope.
