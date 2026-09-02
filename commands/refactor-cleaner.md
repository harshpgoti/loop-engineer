# /refactor-cleaner

Dead-code hunter. Uses knip / depcheck / ts-prune to find unused exports,
unused dependencies, and unreachable branches. SAFE / CAREFUL / RISKY
classification. Removes one category at a time, commits after each batch.
Read-then-edit. Use after a feature lands or as a periodic maintenance
signal.

## How To Interpret

If the user says `/refactor-cleaner`, `remove dead code`, `prune unused deps`,
or asks to clean up a codebase, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/refactor-cleaner/SKILL.md`
3. the active workspace's source tree
4. the project's static analysis tool (knip, depcheck, ts-prune, etc.)

## Loop

```text
RUN the static analysis tool -> CLASSIFY each finding (SAFE / CAREFUL / RISKY) -> REMOVE one category at a time -> RE-RUN the tool -> RE-RUN the test suite
```

## Output

A list of findings, each with the file, line, category, severity, and
proposed change. After each category is removed, the re-run of the
static analysis tool reports zero for that category.

## Continuation

The chain halts on any test failure. The next `/code-reviewer` or
`/qa-evaluator` run verifies the cleanup.