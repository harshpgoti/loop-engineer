---
name: hookify-rules
description: Turn a one-off hook event into a reusable rule. When a transcript shows the agent doing the wrong thing repeatedly and a hook would have caught it, distill the hook into a rule file, add it to the harness's rules directory, and verify the rule fires. Use when the chain's mistake pattern is clear and a single rule would prevent it.
---

# Hookify Rules

Inherits `docs/SKILL_CONTRACT.md`.

A small workflow that converts a recurring failure into a permanent
rule. The rule is a declarative file (typically `*.rules.md` or
`CLAUDE.md`-block) the harness loads and applies; the failure stops
recurring because the rule stops the agent before the mistake.

## When to use

- A transcript shows the same agent mistake happening two or more
  times in a session, or three or more times across sessions.
- A hook event exists that would have caught the mistake.
- The mistake is preventable by a static rule (not a learned
  behaviour that requires context).

## When NOT to use

| Instead of this skill | Use |
|---|---|
| The mistake is rare or one-off | a single comment, not a rule |
| The mistake is context-dependent | a skill, not a rule |
| The user wants to teach the agent a preference | `learn` (continuous-learning-v2) |
| The rule already exists in the harness | the rule is broken; fix it |

## The Workflow

### 1. Identify the failure pattern

A clear failure pattern has three properties:

- **Recurring** - it has happened at least twice in this transcript or
  three times across recent sessions.
- **Causal** - a specific action preceded the failure; the agent
  doing the action causes the failure.
- **Deterministic** - the rule can recognise the trigger reliably
  (regex, path pattern, command class); it is not "vibes."

A pattern that fails any of the three is a `learn` candidate, not a
hookify-rules candidate.

### 2. Design the rule

A rule has four fields:

```yaml
trigger: <regex or path pattern or command class>
scope: <which harness loads the rule>
action: warn | block | correct
message: <what the user sees when the rule fires>
```

`action: warn` lets the agent continue with a visible warning. `block`
stops the agent until the rule is satisfied. `correct` is for rules
that can rewrite the offending input safely (rare).

### 3. Locate the rule file

The harness's rules directory is harness-specific:

- Claude Code: `.claude/rules/` or blocks in `CLAUDE.md`
- Cursor: `.cursor/rules/`
- Codex: `AGENTS.md` blocks
- Generic: `*.rules.md` in repo root

The skill writes the rule to the right location; if the harness's
rules directory is not yet known, the skill uses the chain's
`harness_adapters` registry to look it up.

### 4. Wire the rule

Adding a rule file is not enough; the harness must load it. Most
harnesses auto-load rules from the rules directory. The skill verifies
the rule is loaded by re-running the transcript's failure trigger and
observing the rule fire.

### 5. Verify the rule

The rule is verified by:

- a positive case: the rule fires on the original trigger;
- a negative case: the rule does **not** fire on an unrelated trigger
  (false-positive check);
- a regression check: the rule does not break any existing rule or
  behaviour.

A rule that fires on the wrong trigger is worse than no rule. The
verify step is required.

## Output

```markdown
# Hookify Rules Report: <pattern>

## Pattern
- Recurring: <count>
- Causal: <action that precedes>
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
- Adopt: the rule passes all three checks.
- Refine: <which check failed; how to fix>.
- Defer: the pattern is not yet concrete enough.
```

## Anti-Patterns

- **A rule that fires too often.** A rule that fires on every
  Edit because the user "might be editing the wrong file" is a rule
  the user disables within a day. Specificity matters.
- **A rule that blocks the agent from doing the right thing.** A
  block rule must have a clear bypass; otherwise the agent cannot
  make progress on the legitimate case.
- **A rule that duplicates a skill.** If a skill already says "do
  not edit this file," a rule that blocks the same edit is
  duplication. The skill is the documentation; the rule is the
  enforcement. Pick one.
- **A rule that fires on a prompt-injection attempt.** The
  `safeguard` skill is the prompt-level defense. Hookify-rules is
  for the agent's own mistakes, not the user's input.
- **A rule with no message.** A rule that fires silently is a rule
  the user cannot understand. The message is the user-facing surface.

## Related Skills

- `learn` (continuous-learning-v2) - the project-scoped instinct
  system for patterns that need context, not rules.
- `safeguard` - the prompt-level defense; this skill is the agent-
  level enforcement.
- `codebase-onboarding` - the workflow that triggers hookify-rules
  when a project has recurring failure patterns.