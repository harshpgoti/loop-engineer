---
name: agent-builder
description: Design and scaffold an AI agent (or agentic/dynamic workflow) as the product itself - architecture, tool/skill authoring convention, model provider, guardrails, and evals. Auto-activates during /plan-loop and /develop-product when agent-development signals are present; also runs for /agent-builder directly.
---

# Agent builder

Inherits `docs/SKILL_CONTRACT.md`.

Loop Engineer helps build **any product**; this skill activates when that product is, or includes, an AI agent - a chatbot, autonomous workflow, tool-using assistant, multi-agent system, or dynamic/branching automation. It is not about Loop Engineer's own operational skills (`skills/` at repo root) - it is about the agent **the user is building**.

## When this activates

Auto-detected by `scripts/agent_skill_router.py` from `TASKS.yml`, `plan/`, `HANDOFF.md`, `DECISIONS.md`, and the current user message. Signals: "AI agent," "agentic," "workflow automation," "dynamic workflow," "chatbot," "copilot," "multi-agent," "tool-use," "RAG," "cron agent," and similar. See `plan/AUTO_AGENT_SKILLS.md` after running `loop auto-agent-skills --write`.

Also runs directly on `/agent-builder`.

## Read first

1. `plan/AUTO_AGENT_SKILLS.md` (if present)
2. `skills/agent-development/SKILL.md`
3. `agent/AGENT_ARCHITECTURE.md` (if present - reuse decisions already recorded)
4. `DECISIONS.md`
5. `skills/research-search/SKILL.md`
6. `skills/qa-validation/SKILL.md`

## Workflow

1. Run `loop auto-agent-skills --write` (usually already done by `/plan-loop` or `/develop-product`) and read `plan/AUTO_AGENT_SKILLS.md` for the detected agent shape.
2. If `agent/AGENT_ARCHITECTURE.md` does not exist yet, run `loop agent scaffold` - creates `agent/AGENT_ARCHITECTURE.md`, `agent/skills/`, `agent/tools/`, `agent/evals/` from `templates/agent_architecture.template.md` and `templates/agent_skill.template.md`.
3. Execute the ordered capability chain in `plan/AUTO_AGENT_SKILLS.md`; load only selected capability guidance from `skills/agent-development/references/capability-catalog.md`.
4. Fill `agent/AGENT_ARCHITECTURE.md`: agent type (single/multi/workflow), trigger, tools, memory, guardrails, model provider, eval plan. Reuse anything already answered in `DECISIONS.md` - don't re-ask.
5. Choose the agent product's model provider and model - record the choice in `agent/AGENT_ARCHITECTURE.md` and `DECISIONS.md`. This is a product decision; the coding agent's own model runs the loop.
6. For each distinct capability the agent needs, author a skill under `agent/skills/<name>/SKILL.md` (copy `agent/skills/_template/SKILL.md`). One skill = one trigger + one job - don't build a mega-skill.
7. For any tool the agent can call, document it under `agent/tools/` with its JSON schema and whether it is destructive. Destructive/high-risk tools require human approval per **AGENTS.md rule 5** - say so explicitly.
8. When a design choice is non-obvious (an eval methodology, a safety pattern, a memory architecture), ground it with `skills/research-search/SKILL.md` (arXiv / Research Square) and cite the source in `EVIDENCE_LOG.md` - don't assert it from vibes.
9. Optionally research comparable skill patterns in the agent skill hubs listed in `tools/registry.md` via `WebFetch` - **read-only reference, never vendor or install their packages.** Loop Engineer's own agent-skill format (SKILL.md frontmatter) is deliberately a portable shape so patterns transfer without a dependency.
10. Wire evals with `skills/eval-loop/SKILL.md` - golden cases under `agent/evals/`, tied into `skills/qa-validation/SKILL.md` - an agent PR should not merge on code review alone if agent *behavior* is what changed.
11. Update `TASKS.yml`, `DECISIONS.md`, `HANDOFF.md` with what was decided/built.

## Rules

- **No vendoring.** Do not install, clone, or import any external agent runtime's or marketplace's packages into the product. The skill hubs in `tools/registry.md` are inspiration, not a dependency.
- **Reuse, don't re-ask.** If `agent/AGENT_ARCHITECTURE.md` or `DECISIONS.md` already answers a question (model provider, agent type, guardrails), reuse it.
- **Human approval for destructive tools** - ties directly to AGENTS.md rule 5. Never let an agent auto-approve its own high-risk action.
- **Evidence for non-obvious claims** - architecture/eval/safety claims grounded in published work go through `skills/research-search/SKILL.md` and into `EVIDENCE_LOG.md`, not asserted from memory.
- **Same skill format Loop Engineer itself uses** (SKILL.md frontmatter: `name` + `description`) - the agent being built should be able to author, discover, and load its own skills the same way this repo does.
- **Tests required** - an agent's tool-calling behavior is code; it needs the same test/eval bar as everything else in AGENTS.md rule 10.

## Output

- `agent/AGENT_ARCHITECTURE.md` status (created/updated)
- Agent type + shape (single/multi-agent, RAG, scheduled, dynamic workflow)
- Model provider chosen
- Skills authored under `agent/skills/`
- Tools documented under `agent/tools/`, flagged destructive/approval-required ones
- Eval status
- Next command


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
