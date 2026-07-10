---
name: docs
description: Creates and updates product documentation: main plan, step plans, PRDs, ADRs, API specs, runbooks, onboarding, compliance docs, release notes, and handoffs. Use whenever product or architecture docs need updating.
---

# Docs

## Documentation Map

- `plan/main_plan.md`: full product plan
- `plan/`: step/module plans
- `DECISIONS.md`: decision log
- `EVIDENCE_LOG.md`: sourced facts
- `memories/MEMORY.md`: current mental state
- `HANDOFF.md`: next-agent instructions
- product repo `docs/`: PRD, ADRs, API, runbooks, compliance

## Rules

- Product-specific planning belongs in `plan/main_plan.md` and `plan/`.
- Reusable loop instructions belong in `skills/` and `commands/`.
- Claims with market/regulatory meaning require `EVIDENCE_LOG.md`.
- Architecture choices require `DECISIONS.md`.

## Output

- Docs updated
- Gaps remaining
- Next documentation action
