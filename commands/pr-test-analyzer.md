# /pr-test-analyzer

Test quality not test count. Rates gaps as Critical / Important /
Nice-to-have. Read-only. Use in PR review to surface meaningful-assertion gaps,
isolation issues, and missing edge cases.

## How To Interpret

If the user says `/pr-test-analyzer`, `check the tests`, `are the tests good`,
or asks to review the quality of tests in a PR, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/pr-test-analyzer/SKILL.md`
3. the PR diff (the test changes)
4. the test runner

## Loop

```text
READ the test diff -> CLASSIFY each new or modified test (Critical / Important / Nice-to-have) -> EMIT a report with per-test findings
```

## Output

A Markdown report with the three-bucket classification and a per-test list
with file, line, test, and the gap.

## Continuation

The chain halts on any Critical finding; Important findings are
surfaced; Nice-to-have findings are suggestions.