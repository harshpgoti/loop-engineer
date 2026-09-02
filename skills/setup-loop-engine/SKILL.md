---
name: setup-loop-engine
description: First-time setup with global (~/.loop-engineer/data/) or local (<product-folder>/.loop-engineer/) memory. Local data dirs are auto-detected on return. Use when the user types /setup-loop-engine.
---

# Setup Loop Engine

Inherits `docs/SKILL_CONTRACT.md`.

## Memory modes

| Mode | Path | Command |
|------|------|---------|
| Global (default) | `~/.loop-engineer/data/` | `loop setup` |
| Local | `<product-folder>/.loop-engineer/` | `loop setup --use-cwd` |

## Auto-detection

After local setup, `/plan-loop` and `/loop-engine` auto-use the product folder when loop data exists there.

## Commands

```bash
loop setup
loop setup --use-cwd --name qeautoai
loop setup --memory-mode local --workspace H:/POC/QEAutoAI --name qeautoai
loop setup --interactive
```

## Importing memory/data from another tool during setup

Pass `--source <path>` to import an external tool's `memories/MEMORY.md`, `memories/USER.md`, `memories/SOUL.md`,
and `skills/` in the same step - no separate `/migrate-import` call needed:

```bash
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --dry-run
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --scan
```

`--scan` handles tools with a **different file structure**: dump everything in one
folder and each file is classified by content and routed to the right home
(profile -> `memories/USER.md`, rules -> `memories/SOUL.md`, notes ->
`memories/MEMORY.md`, how-tos -> `skills/imported/`, plans -> `plan/imported/`;
secrets never copied). See `skills/migrate-import/SKILL.md` for the full table.

- Fresh workspace: the imported files supersede Loop Engineer's own starter
  placeholders automatically (there is nothing real to protect yet).
- Existing workspace: real content is protected - pass `--overwrite` to replace it.
- To import later instead, use `skills/migrate-import/SKILL.md` (`/migrate-import`)
  standalone - same underlying `run_import()`, same `--overwrite` semantics.

See `docs/DATA_LAYOUT.md`.


## Stop Conditions and Rollback

A mutating skill declares when to halt and how to revert, before it runs. This section
is required by the canonical skill contract (`docs/SKILL_CONTRACT.md` "Risk and approval")
and is the E3 pattern adopted in round 4.

### When to stop

- **Three failed attempts at the same step.** Retrying past three means the
  hypothesis is wrong, not the execution. Stop, record what was tried, and
  escalate to the user as a doubt.
- **A change introduces more errors than it resolves.** Net negative progress
  is a regression, not a fix. Revert the change; record the failure mode.
- **A gate fails that the plan said must pass.** A gate is a contract; a
  failing gate is the chain telling you the work is not done. Stop and resolve.
- **The active task's `acceptance` criteria become unreachable** because of
  upstream changes. The plan is no longer valid; the task needs re-design,
  not more attempts.
- **Cost drift outside the budget.** A skill that consumes tokens or dollars
  unboundedly is a runaway; stop and report.

### When to escalate to the user

- **High-risk external actions** (publish, deploy, spend, destructive,
  privileged) require explicit user approval per `AGENTS.md` #5. The skill
  prepares the change, names the risk, and waits.
- **A blocker that is human-owned.** The blocker is a question only the
  user can answer (a stakeholder's call, a missing credential, a sign-off).
  Record it in `DOUBTS.md` and `HANDOFF.md`; do not invent an answer.
- **A goal-direction change.** The plan no longer matches what the user
  wants. The chain halts; the user re-plans.

### Rollback path

- **A single-task rollback** is `git revert <task-sha>` (or `git restore` for
  staged-only changes) followed by re-running the active feature's
  `converge-report` to confirm the rollback did not regress the rest of
  the build.
- **A multi-task rollback** is a feature-level revert: identify the feature
  commit range from `.loop/active-feature.json`, revert the range, then run
  `feature-converge` to confirm the surface is clean.
- **A state-only rollback** (files, configs, but no code) is a `git restore
  <path>` + `git clean -fd <path>` for the recorded paths. The skill's
  output records which paths it touched; the rollback reverses exactly
  those.
- **A data-only rollback** is database- and tenant-scoped; record the
  affected rows in the change record, run the inverse migration, and
  verify the diff matches the change record before declaring done.
- **A deploy rollback** is the prior version's artifact promoted through
  the same path the deploy took; `cicd-release/SKILL.md` carries the
  per-deploy rollback procedure.

A rollback that cannot be performed in one step is a planning problem.
Stop and re-plan; do not chain partial rollbacks.
