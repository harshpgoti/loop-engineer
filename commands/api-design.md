# /api-design

Apply REST/HTTP API design conventions. Use when designing, reviewing, or migrating an
API surface. Stack-agnostic.

## How To Interpret

If the user says `/api-design`, `api design`, `design the API`, `REST conventions`,
`endpoint naming`, or asks about HTTP status codes, error envelopes, pagination, or
rate-limit headers, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/api-design/SKILL.md`
3. `plan/main_plan.md` (existing API surface)
4. `DECISIONS.md` (any recorded deviation from conventions)
5. `codebase-design` if the surface is part of a product

## Loop

```text
READ EXISTING SURFACE -> CHECK DEVIATIONS FROM DECISIONS.MD -> APPLY CONVENTIONS -> WRITE API SPEC
```

## Output (locked)

The skill's conventions are deterministic. A reviewer's output is:

```text
## API Design: <surface>

### Resources
- <resource>: <method> <path> -> <status code>, <envelope shape>

### Deviations from conventions
- <deviation> at <endpoint>: <reason, citation to DECISIONS.md>

### Open questions
- <question for the user>
```

## Continuation

A non-conforming surface is a `DECISIONS.md` candidate, not a silent exception. If the
chain makes the surface conform, no ADR is needed; if it intentionally deviates, write
a one-line `DECISIONS.md` entry citing the reason.

## Output

1. The review or design output
2. Resource list
3. Deviations from conventions (with reason)
4. Open questions
5. Next action (apply, deviate-with-reason, or ask)