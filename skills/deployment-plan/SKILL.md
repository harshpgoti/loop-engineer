---
name: deployment-plan
description: Writes or refreshes DEPLOYMENT_PLAN.md at loop closeout, reusing prior cloud, LLM, and deployment decisions from plan/main_plan.md, DECISIONS.md, and DOUBTS.md. Use when /plan, /product-develop, or /loop-engine completes, or when deployment planning is needed.
---

# Deployment Plan

## Purpose

Produce a durable deployment plan when planning or development loops complete. Reuse decisions already captured in `plan/main_plan.md` and planning files. Ask the user only for unresolved deployment choices.

## When To Run

- At closeout of `/plan` once deployment choices are captured or marked TBD
- At closeout of `/product-develop`
- At closeout of `/loop-engine`
- After `/release-check` when preparing production launch
- When the user asks for deployment planning

## Read First

- `plan/main_plan.md`
- `DECISIONS.md`
- `DOUBTS.md`
- `memories/MEMORY.md`
- `plan/PROD-GAP.md`
- `RELEASE_CHECK.md`
- relevant `plan/step_*.md`

## Write

- `DEPLOYMENT_PLAN.md`
- `DOUBTS.md` for unresolved deployment questions
- `HANDOFF.md`
- `.ai/SESSION_LOG.md`

## Questions To Resolve

Ask the user directly when unresolved:

- cloud provider
- single-cloud vs multi-cloud
- production region(s)
- compute model
- database hosting
- LLM provider and model(s)
- embedding provider/model
- agent runtime
- CI/CD platform
- secrets management

## Reuse Rule

If a question was already answered in `DECISIONS.md`, resolved `DOUBTS.md`, `plan/main_plan.md`, or step plans:

1. Reuse the same answer in `DEPLOYMENT_PLAN.md`
2. Mark it under **Confirmed Decisions (Reused)**
3. Inform the user which decisions were reused
4. Do not ask again unless the user wants to change it

## Optional Script

```bash
python scripts/deployment_plan.py --source plan
```

Custom workspace:

```bash
python scripts/deployment_plan.py --workspace ../product
```

Then refine the draft with product-specific infrastructure details.

## Closeout Behavior

1. Write or refresh `DEPLOYMENT_PLAN.md`
2. List reused decisions for user confirmation
3. Ask only unresolved deployment questions
4. Record unresolved items in `DOUBTS.md`
5. Mention deployment follow-ups in `HANDOFF.md`

## Output

- `DEPLOYMENT_PLAN.md` path
- Reused decisions count
- Open deployment questions
- User actions required
