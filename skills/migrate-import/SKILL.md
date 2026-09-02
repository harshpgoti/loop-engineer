---
name: migrate-import
description: Imports memory and skills from an external agent workspace into the active Loop Engineer product workspace. Use when the user types /migrate-import.
---

# Migrate Import

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Copy durable memory and skills from another tool's workspace folder into Loop Engineer paths.

## Command

`/migrate-import`

## Script

```bash
python scripts/migrate_import.py --source /path/to/source --dry-run
python scripts/migrate_import.py --source /path/to/source
loop migrate import --source /path/to/source --scan          # + classify arbitrary files
```

## Scan mode (`--scan`) - different tool, different file structure

When the source tool's files don't use Loop Engineer's names, add `--scan`: every
file in the folder is classified deterministically (filename + content signals -
rules first, no LLM call) and routed:

| Detected as | Goes to |
|-------------|---------|
| user profile / preferences | appended to `memories/USER.md` |
| behavior rules / persona / prompts | appended to `memories/SOUL.md` |
| project memory / notes / logs | appended to `memories/MEMORY.md` |
| how-tos / runbooks / procedures | `skills/imported/<slug>.md` (frontmatter added) |
| plans / roadmaps / PRDs / specs | `plan/imported/` - absorb via `/plan-loop` next session |
| secrets / API keys | **never copied** - warned; re-enter any keys manually |
| binary / unclassifiable | skipped / staged in `.loop/import-review/` for manual review |

Appends carry an `Imported from <path>` marker, so re-running is idempotent.
Dry-run first: `loop migrate import --source <path> --scan --dry-run`.

## Rules

- Require explicit `--source` path.
- Dry-run first unless user approves apply.
- Do not copy secrets automatically.
- Never overwrite core product plan files without user approval.

## One-shot alternative

To import during first-time setup instead of as a separate step, pass `--source` to
`/setup-loop-engine` directly (`loop setup --use-cwd --source /path/to/other-tool`) -
same underlying `scripts/migrate_import.run_import()`, same `--overwrite` semantics.


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
