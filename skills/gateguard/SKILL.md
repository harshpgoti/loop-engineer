---
name: gateguard
description: Enforce a release gate as a Stop hook. The hook checks a configurable set of machine-verifiable conditions (test exit code, file mtime, build artifact, lint, security scan) and blocks the agent from finishing if any condition fails. Use at the boundary between a build loop and a "we are done" claim.
---

# Gate Guard

Inherits `docs/SKILL_CONTRACT.md`.

A Stop hook that enforces a release gate. The hook runs at the end of a
chain run; if the gate's conditions are not satisfied, the agent is
blocked from finishing until they are. The chain's terminus is the
gate; the gate is the proof that the terminus has been reached.

## When to use

- A release is being claimed. "We are done" must be machine-verifiable, not
  asserted.
- A gate's conditions are scattered across multiple scripts (test,
  lint, build, security) and the chain has to coordinate them.
- A previous release was claimed "done" but was not actually ready, and
  the fix is to add an explicit gate.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A human-review gate | `release-check` + explicit user approval |
| A single-script check | run the script; the gate is the script |
| A gate that requires subjective judgement | `release-check` (a different shape) |

## Configuration

The gate is configured per workspace at `.loop/gates.yml`:

```yaml
gates:
  - id: G-RELEASE-01
    name: tests-and-lint
    description: tests pass, lint clean
    checks:
      - name: tests
        command: "npm test"
        exit_code: 0
        on_failure: block
      - name: lint
        command: "npm run lint"
        exit_code: 0
        on_failure: block
      - name: build
        command: "npm run build"
        exit_code: 0
        on_failure: block
      - name: artifact-present
        path: dist/index.js
        exists: true
        on_failure: block
      - name: no-secrets
        command: "<your secrets-scan command>"
        exit_code: 0
        on_failure: block
```

Each check is machine-verifiable:

- `command: <shell command>` runs the command; `exit_code` is the
  expected exit code.
- `path: <path>` checks the file exists; `exists: true` is the assertion.
- `on_failure: block` is the policy. The gate is a Stop hook; "block" is
  the default. (Future: `warn` may be added.)

The gate is the only thing that may claim "the gate passed." A check that
is not in `.loop/gates.yml` is not part of the gate.

## Hook Wiring

The gate is wired as a Stop hook in the harness. The hook:

1. Reads `.loop/gates.yml`.
2. For each gate, runs each check.
3. If any check fails, blocks the agent with the failure message + the
   command to re-run after fixing.
4. If all checks pass, allows the agent to finish.

The hook is run by the harness, not by the agent. The agent cannot
disable the hook; the user cannot either (without editing the harness
config).

## Failure Format

A failed gate produces:

```text
GATE FAILED: G-RELEASE-01
- tests: exit 1 (expected 0)
  output: 5 failing tests in src/foo.test.ts
  remediation: run `npm test`; fix the failing tests; re-run /release-check
- lint: skipped (preceding check failed)
```

The agent is blocked; the chain halts; the user sees the gate failure as
the chain's last output. The user fixes the underlying problem and
re-runs the chain; the hook re-runs; if the gate passes, the agent is
allowed to finish.

## Anti-Patterns

- **A gate the agent can disable.** A gate in code that the agent
  controls is not a gate. The gate lives in the harness.
- **A gate with subjective checks.** "The code is good" is not a check.
  The gate is machine-verifiable or it is not a gate.
- **A gate that runs forever.** Each check has a timeout. A check that
  hangs blocks the agent indefinitely. Configure timeouts.
- **A gate that exists but is not wired.** A `.loop/gates.yml` that no
  hook reads is documentation, not enforcement.
- **A gate that lies.** A check that returns 0 even on failure is worse
  than no check. Verify the gate's own correctness before relying on it.

## Related Skills

- `release-check` - the human-readable report; this skill is the hook
  that enforces it.
- `verification-loop` - the deterministic check sequence (build, types,
  lint, tests, security, diff).
- `delivery-gate` - the upstream pattern this skill consolidates.
- `delivery` - the capability that owns release-readiness.