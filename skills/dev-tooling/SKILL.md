---
name: dev-tooling
description: Workspace-scoped developer tooling that runs the project's linter, formatter, and test suite as configured in `.loop/dev_config.json`. Composes `/lint`, `/format`, `/test`, and `/commit` so a workspace's gate checks share one routing layer (`scripts/dev.py`).
class: stateful
capability: developer-tooling
activation:
  - /lint
  - /format
  - /test
  - /commit
owner: developer-tooling
---

Inherits `docs/SKILL_CONTRACT.md`. Risk and approval: `/lint` / `/test` /
`/format` are read-only-equivalent; `/commit` mutates the workspace repo
(staging + commit). Approve the structured message before running; the chain
continues only when the gate is green.

# Purpose

`dev-tooling` is the single skill that fronts the four workspace-scoped developer
commands (`/lint`, `/format`, `/test`, `/commit`). Every command reads
`<workspace>/.loop/dev_config.json`, runs the configured script, and emits a
structured result. The four commands do not own their own behaviour — they own
the *contract*; `scripts/dev.py` owns the execution.

# Read First

- `AGENTS.md` (always)
- `commands/lint.md`, `commands/format.md`, `commands/test.md`, `commands/commit.md`
- `scripts/dev.py`

# Workflow

1. **Read `<workspace>/.loop/dev_config.json`.** If missing, guide the workspace
   to add one (`scripts/dev.py` emits a clear "no config" message).
2. **Route to the configured command.** `lint.command`, `format.command`,
   `test.command`, or the conventional-commits template for `commit`.
3. **Validate the result.** A failing lint, format check, or test is a Stop
   Condition. A passing result returns 0 and the chain continues with the next
   action in `HANDOFF.md`.
4. **Commit only on green.** `/commit` expects `/lint`, `/test`, and `/format`
   to have passed before it runs; the commit config is stack-agnostic.

# Output

1. The configured command's stdout + exit code (per command)
2. A structured commit message validation result (for `/commit`)
3. The git commit hash + summary (for `/commit`)

# Anti-Patterns

- **Embedding stack-specific commands in the skill.** The skill is
  stack-agnostic; the *workspace* chooses the stack via `.loop/dev_config.json`.
- **Treating `/lint` / `/test` / `/format` as four separate skills.** They
  share `scripts/dev.py`; splitting them creates four skills with one-line
  workflows that all delegate to the same script.
- **Running `/commit` before `/lint` `/test` `/format` pass.** A commit that
  breaks the gate undoes the gate.

# Related Skills

- `develop-product` (the chain that produces the gates)
- `qa-validation` (deeper test review)
- `code-reviewer` (post-edit review)
- `tdd` (when writing tests for new code)