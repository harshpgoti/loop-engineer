---
name: agent-sort
description: Classify the canonical skills, commands, agents, rules, and hooks in a workspace as DAILY (load every session) or LIBRARY (keep accessible, do not auto-load). Run parallel subagent review passes over each surface and write an evidence_table. Use when adopting Loop Engineer on a project, or as a periodic audit to keep the loaded set small.
---

# Agent Sort

Inherits `docs/SKILL_CONTRACT.md`.

A classification pass that splits the loop's surface into **DAILY** (loaded
every session) and **LIBRARY** (kept accessible, do not auto-load). The
goal is the smallest possible working set; everything else is a tax on
context and focus.

## When to use

- Loop Engineer is being adopted on a project; the default skill set is
  too large to load every session.
- A periodic audit reveals the working set has drifted (a skill is being
  loaded that no one uses; a skill that everyone needs is not loaded).
- A capability addition introduced skills that should be LIBRARY.

## When NOT to use

- The project is tiny and a single load is fine.
- The audit is per-skill; sort the whole surface, not one skill.

## The Five Parallel Review Passes

Five surfaces, five parallel subagent reviews. Each surface produces an
`evidence_table` row:

```text
| path | type | bucket | evidence | justification |
```

`path` is the surface element (skill name, command, agent id, rule path,
hook event). `type` is one of: `skill`, `command`, `agent`, `rule`,
`hook`, `extra`. `bucket` is `DAILY` or `LIBRARY`. `evidence` is the grep
or file-content snippet that proves the classification. `justification`
is the one-sentence reason.

The five passes:

| Pass | What is reviewed |
|---|---|
| Skills | `skills/*/SKILL.md` |
| Commands | `commands/*.md` |
| Agents | `manifests/agents.json` |
| Rules | any `*.rules.md` or `CLAUDE.md` rule blocks |
| Hooks + Extras | any `harnesses/`, `tools/`, `templates/`, `evals/` |

Each pass is a parallel subagent with the same prompt shape:

```text
You are reviewing the <SURFACE> surface of the Loop Engineer installation
in <WORKSPACE>. For each element, classify it as DAILY (load every
session) or LIBRARY (keep accessible, do not auto-load).

DAILY: <def - every session needs this; central to the chain's default loop>
LIBRARY: <def - useful but only when explicitly triggered; rare in practice>

Cite grep evidence. Do not classify without evidence. Output an
evidence_table with one row per element.
```

## Output Format

```markdown
# Agent Sort Report: <workspace>

## Summary
- Skills scanned: <n> | DAILY: <n> | LIBRARY: <n>
- Commands scanned: <n> | DAILY: <n> | LIBRARY: <n>
- Agents scanned: <n> | DAILY: <n> | LIBRARY: <n>
- Rules scanned: <n> | DAILY: <n> | LIBRARY: <n>
- Hooks + Extras scanned: <n> | DAILY: <n> | LIBRARY: <n>

## Per-surface evidence tables
### Skills
| skill | bucket | evidence | justification |
| ... |

### Commands
...

### Agents
...

### Rules
...

### Hooks + Extras
...

## Recommended action
- Default working set: <list of DAILY skill/command/agent ids>
- DAILY-by-exception: <list of LIBRARY items that should be loaded conditionally>
- DAILY-by-evidence-of-use: <list of DAILY items that no evidence supports; move to LIBRARY>
```

## Default Working Set

The "DAILY" set is what the chain auto-loads. The "LIBRARY" set is
discoverable but not loaded. The chain's `loop auto-skills` or equivalent
honours the split; a user-invoked command always loads regardless of
its bucket.

## Anti-Patterns

- **A DAILY set that is too small.** A DAILY set that excludes something
  the chain uses every session forces a reload mid-flow. The set is
  the working memory; it is large enough to cover the common cases.
- **A LIBRARY set that is too small.** A LIBRARY set that is missing
  something the user wants to invoke means the chain cannot find it.
  LIBRARY is "not auto-loaded," not "doesn't exist."
- **No evidence.** A classification without a grep citation is a
  guess. The whole point of agent-sort is to replace vibes with
  evidence; an ungrounded sort is worse than no sort.
- **A sort that runs forever.** The sort is a one-shot per workspace,
  not a continuous classification. Re-run when the surface changes
  (a new skill, a new command), not on every commit.
- **A DAILY set determined by a single user.** The sort is evidence-
  based; the user's gut is one input, not the only input.

## Related Skills

- `skill-scout` - the audit before the sort (find what exists).
- `skill-stocktake` - the periodic verdict on each skill's quality.
- `codebase-onboarding` - the trigger for a first-time sort.
- `harness` - the per-coding-agent loader that honours the DAILY set.


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
