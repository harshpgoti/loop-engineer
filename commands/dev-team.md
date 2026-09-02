# /dev-team

Run a preset four-persona parallel review (PM / Architect / Developer / QA) as analysis-only
subagents. Complements `/council`; same anti-anchoring rule, different voice set.

## How To Interpret

If the user says `/dev-team`, `dev-team`, `pm arch dev qa`, `run the four-lens review`,
`party mode`, or asks for a constructive role-based review (rather than an adversarial
council), execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/dev-team/SKILL.md`
3. `plan/main_plan.md`
4. active `plan/step_*.md` or feature `spec.md`
5. `DOUBTS.md`
6. `EVIDENCE_LOG.md`
7. `DECISIONS.md`
8. `GATES.yml`

## Anti-Anchoring Rule

Each persona receives **only** the question and the minimal context files. The full
conversation history is intentionally withheld. A persona that already saw the conversation
cannot participate.

## Roster

PM / Architect / Developer / QA. Each is analysis-only (Read, Grep, Glob). None may write.

## Loop

```text
RESOLVE QUESTION -> BUILD CONTEXT BUNDLE -> FAN-OUT (anti-anchored) -> COLLECT POSITIONS -> SYNTHESIZE (agreements + tensions) -> LOCK OUTPUT SCHEMA
```

## Output Schema (locked)

```markdown
## Dev Team: <short title>
**PM / Architect / Developer / QA:**:** <1-2 sentence position each>
### Agreements
### Tensions
### Recommendation
### Confidence
- per-persona + overall
```

## Continuation

`Recommendation` lands as a concrete next step:
- a task in `TASKS.yml` for code changes,
- an ADR via `architecture-decision-records` for long-lived system policy,
- a doubt in `DOUBTS.md` for questions only the user can settle.

The chain continues from there. Never end a turn telling the user to run the next stage.

## Output

1. `plan/DEV_TEAM.md` path
2. Per-persona position
3. Agreements + tensions + recommendation
4. Next action (task / ADR / doubt / proceed)