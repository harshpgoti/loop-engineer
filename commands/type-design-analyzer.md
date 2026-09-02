# /type-design-analyzer

Score type design on four axes: Encapsulation, Invariant Expression,
Usefulness, Enforcement. Read-only. Use in code review, before a public
API change, or as a periodic design-quality signal.

## How To Interpret

If the user says `/type-design-analyzer`, `score the type design`, `is this
type well-designed`, or asks for a design-quality review, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/type-design-analyzer/SKILL.md`
3. the type or interface under review
4. the type's callers

## Loop

```text
READ the type and its callers -> SCORE each of 4 axes (Encapsulation, Invariant Expression, Usefulness, Enforcement) -> EMIT a report with score, findings, and remediation
```

## Output

A Markdown report with the four scores, the total, and a per-finding list
with file, line, axis, and one-line remediation.

## Continuation

The chain produces a report; the maintainer acts on the findings. A low
score is a finding, not a stop condition.