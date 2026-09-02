# /gateguard

Enforce a release gate as a Stop hook. Checks a configurable set of
machine-verifiable conditions; blocks the agent from finishing if any condition
fails. Use at the boundary between a build loop and a "we are done" claim.

## How To Interpret

If the user says `/gateguard`, `enforce the gate`, `add a stop hook`, or asks to
make a release condition non-bypassable, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/gateguard/SKILL.md`
3. `.loop/gates.yml` (the gate configuration)
4. the harness adapter for the active tool

## Loop

```text
READ .loop/gates.yml -> RUN EACH CHECK -> BLOCK OR ALLOW
```

## Output

A blocked gate produces:

```text
GATE FAILED: <gate id>
- <check name>: <failure details>
  remediation: <how to fix>
```

A passing gate is silent; the agent is allowed to finish.

## Continuation

A blocked gate is a Stop Condition. The chain halts; the user fixes the
underlying problem; the chain re-runs. The hook re-runs on every chain
completion.