# /hookify-rules

Turn a one-off hook event into a reusable rule. When a transcript shows the
agent doing the wrong thing repeatedly and a hook would have caught it,
distill the hook into a rule file, verify the rule fires, and confirm it does
not break the existing rule set.

## How To Interpret

If the user says `/hookify-rules`, `make a rule from this mistake`, `add a
hook for X`, or asks to turn a recurring agent error into a permanent rule,
execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/hookify-rules/SKILL.md`
3. the transcript or session showing the failure pattern
4. the harness's rules directory (via `harness_adapters`)

## Loop

```text
IDENTIFY failure pattern (recurring + causal + deterministic) -> DESIGN rule (trigger, scope, action, message) -> WRITE rule file -> VERIFY (positive, negative, regression) -> REPORT
```

## Output (locked)

```markdown
# Hookify Rules Report: <pattern>

## Pattern
- Recurring: <count>
- Causal: <action>
- Deterministic: <trigger>

## Rule
- file: <path>
- trigger: <regex or pattern>
- action: <warn | block | correct>
- message: <text>

## Verification
- positive: <pass/fail>
- negative: <pass/fail>
- regression: <pass/fail>

## Recommendation
- Adopt: all three checks pass.
- Refine: <which failed; how to fix>.
- Defer: the pattern is not yet concrete enough.
```

## Continuation

Adopt → the rule is in place; the harness loads it; future sessions
honour it. Refine → the rule is rewritten and re-verified. Defer → the
pattern is parked in `DOUBTS.md` until it recurs enough to write a
concrete rule.