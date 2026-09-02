# /code-simplifier

Read-then-edit refactor that preserves behavior. Targets complexity, dead
branches, and unclear names. Use after a feature lands and tests pass, or
when an assurance review flags a complexity smell.

## How To Interpret

If the user says `/code-simplifier`, `simplify the code`, `refactor for clarity`,
or asks to clean up a diff that is larger than necessary, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/code-simplifier/SKILL.md`
3. the current diff or the file under review
4. the test runner configuration

## Loop

```text
READ the diff or the file -> IDENTIFY complexity that does not earn its keep -> PROPOSE minimal edits (tests before and after must pass) -> COMMIT per edit
```

## Output

A list of proposed edits, each with the file, line range, the smell being
addressed, the proposed change, and the test that proves behavior is
preserved.

## Continuation

The chain halts on any test failure; the user is the final reviewer for
public API renames. The next `/code-reviewer` or `/qa-evaluator` run
verifies the change.