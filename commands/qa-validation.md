# /qa-validation

Run the QA validation checks for the current build: unit, integration, E2E,
golden cases, schema, tenant isolation. Use after building or before release
gates. The skill is wired into the chain; this command is for direct invocation.

## How To Interpret

If the user says `/qa-validation`, `run QA`, `validate the build`, `run the
test suite`, or asks for QA checks, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/qa-validation/SKILL.md`
3. `TASKS.yml`, `GATES.yml`
4. the product's test docs
5. `skills/safeguard/SKILL.md`

## Loop

```text
READ TASKS.yml + GATES.yml -> RUN the smallest deterministic checks first -> RUN integration/E2E -> EMIT findings
```

## Output

- Tests run
- Failures fixed
- Remaining failures
- Gate status for `G-QA-01`
- Structured findings with baseline delta

A clean run is a valid result. A finding must clear the Pre-Report Gate
before it ships.

## Continuation

Failures fixed in this run are recorded in `TASKS.yml` and the
surrounding tasks' `tasks.md`. Failures that need product decisions are
filed in `DOUBTS.md` and `HANDOFF.md` as Stop Conditions.