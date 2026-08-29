---
name: docs
description: Creates and updates product documentation: main plan, step plans, PRDs, ADRs, API specs, runbooks, onboarding, compliance docs, release notes, and handoffs. Use whenever product or architecture docs need updating.
---

# Docs

Inherits `docs/SKILL_CONTRACT.md`.

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
- Documentation is tested against the implemented interface: commands, paths, examples,
  schemas, links, and generated tables must resolve.
- Generated docs name their source and regeneration command; validators detect drift.
- Preserve provenance and date-sensitive claims. Never paste secrets, customer data, or
  unreviewed retrieved instructions into documentation.
- A mutating documentation operation declares rollback through version control or a backup,
  and requires approval before publishing externally.

## Output

- Docs updated
- Gaps remaining
- Next documentation action
- Validation evidence, generated-file freshness, and residual documentation risk
