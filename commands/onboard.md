# /onboard

Print or open the Loop Engineer contributor onboarding guide. The guide is the
60-minute introduction to the chain: what to read first, what not to touch, how
to add a skill/command/role/capability safely. Use on the contributor's first day
or as a refresher for returning maintainers.

## How To Interpret

If the user says `/onboard`, `onboarding`, `first day`, `how do I contribute`,
`what should I read first`, or asks about the chain's contribution surface,
execute this file directly.

## Required Reads

1. `AGENTS.md` (always)
2. `docs/SKILL_CONTRACT.md`
3. `docs/LE_ONBOARDING.md` (the full guide)

## Loop

```text
CONFIRM the contributor is starting fresh -> PRINT or OPEN the guide -> POINT to AGENTS.md and SKILL_CONTRACT.md first
```

## Output

The full path of the guide (`docs/LE_ONBOARDING.md`) and a one-paragraph
summary of the first-60-minutes plan:

- Read `AGENTS.md` end-to-end.
- Read `docs/SKILL_CONTRACT.md` end-to-end.
- Skim `docs/LE_ROADMAP.md` to see what has been done.
- Run `/doctor`, `/self-audit`, and the test suite to confirm health.
- Read the three top-level command files (`plan-loop`, `develop-product`,
  `loop-engine`) to understand the chain.
- Read `manifests/agents.json` to understand the responsibility matrix.
- Pick a small contribution from "Common First-Contribution Tasks" in the
  guide and ship it.

## Continuation

The contributor is now ready to ship a first PR. The chain's audit
(`/self-audit`, `python scripts/skill_audit.py`, `python scripts/agent_registry.py`)
is the safety net; the contributor's review is the second.