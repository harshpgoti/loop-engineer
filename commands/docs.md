# /docs

Create or update product documentation: main plan, step plans, PRDs, ADRs, API
specs, runbooks, onboarding, compliance docs, release notes, handoffs. The skill
is wired into the chain; this command is for direct invocation.

## How To Interpret

If the user says `/docs`, `update the docs`, `write the runbook`, or asks for a
documentation pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/docs/SKILL.md`
3. `plan/main_plan.md`, `plan/step_*.md`
4. `DECISIONS.md`, `EVIDENCE_LOG.md`
5. `CONTEXT.md`
6. the current state of the docs

## Loop

```text
READ existing docs -> READ code the docs describe -> WRITE the diff (only what is wrong) -> EMIT under plan/ or docs/ as appropriate
```

## Output

- Docs updated
- Gaps remaining
- Next documentation action
- Validation evidence, generated-file freshness, residual documentation risk

A documentation update is tested against the implemented interface:
commands, paths, examples, schemas, links, and generated tables must
resolve. Generated docs name their source and regeneration command;
validators detect drift.

## Continuation

Claims with market/regulatory meaning require an `EVIDENCE_LOG.md` entry.
Architecture choices require a `DECISIONS.md` entry. A documentation
update is a mutating action; the rollback path is version control.
Sensitive data is never pasted into documentation.

## Related Skills

- `living-docs-governance` - the drift detector; this skill is the
  writer.
- `architecture-decision-records` - the canonical artifact for an
  architecture decision that needs durable memory.
- `safeguard` - the prompt-level defence applied to user input.