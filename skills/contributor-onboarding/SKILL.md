---
name: contributor-onboarding
description: Print or open the Loop Engineer contributor onboarding guide for new or returning maintainers. Routes to `docs/LE_ONBOARDING.md` and `docs/SKILL_CONTRACT.md`.
class: read-only
capability: contributor-onboarding
activation:
  - /onboard
owner: contributor-onboarding
---

Inherits `docs/SKILL_CONTRACT.md`. Risk and approval: this skill is
read-only; it does not modify the chain. It points new contributors at the
60-minute plan, the contract, and the audit triad.

# Purpose

`contributor-onboarding` is the entry point for new contributors. It prints or
opens the 60-minute guide (`docs/LE_ONBOARDING.md`) and the canonical contract
every skill must follow (`docs/SKILL_CONTRACT.md`). It does not modify the
chain; it prepares the contributor to do so.

# Read First

- `AGENTS.md` (always)
- `docs/SKILL_CONTRACT.md`
- `docs/LE_ONBOARDING.md`
- `docs/LE_ROADMAP.md`

# Workflow

1. **Confirm the contributor is starting fresh.** If the contributor has
   shipped a PR before, point them at `/doctor` and the audit triad instead.
2. **Print or open the guide.** The full path is `docs/LE_ONBOARDING.md`. The
   guide is self-contained; the command does not need to inline it.
3. **Point to the contract first.** `docs/SKILL_CONTRACT.md` is the rule every
   skill inherits; reading it before any skill edit prevents the most common
   first-day mistakes.
4. **Hand off to the audit triad.** `/self-audit`, `scripts/skill_audit.py`,
   and `scripts/agent_registry.py` are the safety net; the contributor's
   review is the second.

# Output

- The full path of the guide and a one-paragraph first-60-minutes plan:
  - Read `AGENTS.md` end-to-end.
  - Read `docs/SKILL_CONTRACT.md` end-to-end.
  - Skim `docs/LE_ROADMAP.md` to see what has been done.
  - Run `/doctor`, `/self-audit`, and the test suite to confirm health.
  - Read `plan-loop`, `develop-product`, `loop-engine` to understand the chain.
  - Read `manifests/agents.json` to understand the responsibility matrix.

# Anti-Patterns

- **Inlining the onboarding guide into the command.** The guide is a living
  document; the command should reference it, not duplicate it.
- **Skipping `docs/SKILL_CONTRACT.md`.** The contract is the first thing every
  skill edit must respect.
- **Pointing new contributors at deep architecture docs.** The chain's
  architecture is in the contracts; start there.

# Related Skills

- `chain-meta` (the introspection surface every contributor must learn)
- `doctor` (runtime health check for fresh workspaces)
- `revise-skill` (the first PR most contributors will land)