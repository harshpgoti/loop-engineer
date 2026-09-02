---
name: tool-orchestrator
description: Selects supporting capabilities for the current loop phase in Loop Engineer's own terms - memory synthesis, reusable skills, spec-driven task discipline, role-based review, sandboxed execution, RAG. Use when choosing tools, workflows, evals, memory, sandboxing, or production agent patterns.
---

# Tool Orchestrator

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Select supporting capabilities for the current loop phase without hard-coding one vendor or agent runtime. Describe what the loop needs functionally; implement it however fits the product's stack. Named external tools/repos for each capability live in `tools/registry.md` - link there, don't re-list names here.

## Capability Map

| Capability | Use In Loop |
|------------|-------------|
| Cross-session memory synthesis | Retrieval, synthesis, gap analysis, citation memory across many sessions - beyond `memories/MEMORY.md`/`state.db` |
| Reusable agent skills | Shared skill patterns, review closeout, handoff - see `skills/agent-builder/SKILL.md` for the product's own skills |
| Spec-driven task discipline | Phased development from idea to build tasks - see `plan/features/`, `skills/plan-loop/phases/task-compiler.md` |
| Skill packaging conventions | Progressive disclosure, portable instructions - the `SKILL.md` frontmatter format Loop Engineer already uses |
| Role-based review | Strategy, PM, design, engineering, QA, security, release perspectives - see `skills/plan-loop/phases/council.md` |
| Sandboxed execution | Long-running or higher-risk agent execution: network policy, resource limits, safer runtime |
| Retrieval-augmented generation | Ingestion, hybrid retrieval, reranking, eval, guardrails - only when retrieval is actually needed |

## Selection Rules

- Use cross-session memory synthesis when the problem is long-horizon context, citations, interviews, or gap analysis.
- Use reusable-skill patterns when the problem is repeatable workflows or review closeout.
- Use spec-driven task discipline when moving from idea to build tasks.
- Use role-based review when separating strategy, PM, engineering, QA, security, and release responsibilities.
- Use sandboxed execution for long-running or higher-risk agent execution.
- Use RAG patterns only when retrieval is needed; do not add RAG to MVP if deterministic parsers solve the job.

## Output

- Capability selected
- Why it helps this phase
- What not to use yet
- Any setup or security caveat

## See also

`tools/registry.md` - the named external tool/repo for each capability above.


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
