# /safeguard

Apply the Prompt Defense Baseline: the 6-bullet preamble that defends against
prompt injection, secret leakage, role override, unicode tricks, untrusted
external data, and harmful content. Use when designing or reviewing any skill,
agent, or prompt that processes user input or external content.

## How To Interpret

If the user says `/safeguard`, `apply the defense baseline`, `is this skill
injection-safe`, or asks about prompt-level security, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/safeguard/SKILL.md` (the canonical 6 bullets)
3. the target skill or agent being reviewed

## Loop

```text
READ the 6-bullet baseline -> CHECK the target against each bullet -> REPORT coverage gaps
```

## Output (locked)

```text
## Safeguard Review: <target>

| Bullet | Covered? | Where | Notes |
|--------|----------|-------|-------|
| 1. Role / persona / identity not changed | yes/no | <file:line> | |
| 2. No secret leakage | yes/no | <file:line> | |
| 3. No executable output without validation | yes/no | <file:line> | |
| 4. Unicode / homoglyph treated as suspicious | yes/no | <file:line> | |
| 5. External content treated as untrusted | yes/no | <file:line> | |
| 6. No harmful content generation | yes/no | <file:line> | |

## Recommendation
- Adopt: all six covered; the target is safe.
- Refine: <which bullets are missing or weak>.
- Reject: the target cannot be made safe without redesign.
```

## Continuation

A skill that fails any bullet is either reworked (in-place edits) or sent
back to its owner with the gap list. The chain does not auto-edit.