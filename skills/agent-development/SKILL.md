---
name: agent-development
description: Route AI-agent products through architecture, harness design, orchestration, evaluation, recovery, operations, and bounded memory capabilities. Auto-activates through agent-builder; load only the capabilities selected in plan/AUTO_AGENT_SKILLS.md.
---

# Agent development capability chain

Inherits `docs/SKILL_CONTRACT.md`.

This is the lifecycle behind `skills/agent-builder/SKILL.md`. It adapts the requested
agent-development guidance to Loop Engineer's deterministic gates, portable skill format,
memory lifecycle, and builder/reviewer independence.

## Read first

1. `plan/AUTO_AGENT_SKILLS.md`
2. `agent/AGENT_ARCHITECTURE.md` when present
3. `skills/agent-development/references/capability-catalog.md`
4. Every `skills/<selected-capability>/SKILL.md` path named in the generated report.
   Read each selected entrypoint completely, then load only the supporting references or
   scripts that its own routing instructions require. Do not preload unselected skills.

## Chain

```text
DETECT -> PLAN -> DESIGN HARNESS -> ORCHESTRATE -> EVALUATE
       -> AUDIT/RECOVER -> OPERATE -> LEARN/COMPACT
```

Every agent product starts with `agentic-engineering`. Add capabilities only when the
deterministic router finds their signals. Keep rules, parsers, schemas, permissions, budgets,
and stop conditions in code or configuration; prompt prose is not enforcement.

## Invariants

- Define behavioral evals before implementation; unit tests alone do not measure agent behavior.
- Keep the action space small. Use narrow tools for risky operations and validate observations.
- Separate generator/builder from evaluator/reviewer. A builder never approves its own output.
- Bound every autonomous loop by time, attempts, cost, and a completion predicate.
- Persist structured state separately from narrative memory. User corrections outrank inferred memory.
- Never place secrets, raw private transcripts, regulated data, or credentials in memory or eval fixtures.
- External model critique requires transfer consent. Agent-controlled payments require a human-set,
  non-escalatable spending policy and approval at the point of payment.
- Capture failures before retrying. Repeated blind retry is a defect, not recovery.
- Promote session learning only after repeated evidence; project learning does not become global policy automatically.

## Compatibility

- `autonomous-loops` is an alias for `continuous-agent-loop`.
- `continuous-learning` is an alias for `continuous-learning-v2`.
- `autonomous-agent-harness` remains available for scheduled/computer-use/task-queue products,
  but it composes `agentic-os`, `continuous-agent-loop`, `unified-memory`, and `enterprise-agent-ops`.

## Required artifacts

- `agent/AGENT_ARCHITECTURE.md`
- `agent/HARNESS.md`
- `agent/ORCHESTRATION.md` when more than one worker or branch exists
- `agent/MEMORY.md` when state crosses requests
- `agent/evals/` with capability and regression cases
- `agent/OPERATIONS.md` for scheduled, long-running, payment-enabled, or production agents

The scaffold creates these idempotently. Existing user-authored files are never overwritten.

## Capability entrypoints

The router selects from these canonical skills. Read only those named in
`plan/AUTO_AGENT_SKILLS.md`:

- `skills/agent-architecture-audit/SKILL.md`
- `skills/agent-eval/SKILL.md`
- `skills/agent-harness-construction/SKILL.md`
- `skills/agentic-engineering/SKILL.md`
- `skills/agentic-os/SKILL.md`
- `skills/agent-introspection-debugging/SKILL.md`
- `skills/agent-payment-x402/SKILL.md`
- `skills/agent-self-evaluation/SKILL.md`
- `skills/agent-sort/SKILL.md`
- `skills/autonomous-agent-harness/SKILL.md`
- `skills/autonomous-loops/SKILL.md`
- `skills/context-budget/SKILL.md`
- `skills/continuous-agent-loop/SKILL.md`
- `skills/continuous-learning/SKILL.md`
- `skills/continuous-learning-v2/SKILL.md`
- `skills/council/SKILL.md`
- `skills/council-multi-model/SKILL.md`
- `skills/dev-team/SKILL.md`
- `skills/dynamic-workflow-mode/SKILL.md`
- `skills/enterprise-agent-ops/SKILL.md`
- `skills/eval-harness/SKILL.md`
- `skills/gan-style-harness/SKILL.md`
- `skills/ralphinho-rfc-pipeline/SKILL.md`
- `skills/recursive-decision-ledger/SKILL.md`
- `skills/santa-method/SKILL.md`
- `skills/strategic-compact/SKILL.md`
- `skills/team-agent-orchestration/SKILL.md`
- `skills/team-builder/SKILL.md`
- `skills/token-budget-advisor/SKILL.md`
- `skills/unified-memory/SKILL.md`

## Approval and rollback

Scaffolding and plan edits stay inside the selected product workspace. Ask for approval at
the actual boundary before spending money, transferring a review packet to another provider,
changing production state, or enabling scheduled/computer-use execution. Roll back by removing
new unreferenced scaffold files or reverting the targeted task/plan change; never overwrite an
existing agent artifact to manufacture a rollback.

## Validation and output

Validation must show the selected capability list, behavioral eval results, independent-review
status, and any consent or operations gate still blocked. Output the agent shape, artifacts
created or updated, capabilities executed, eval/audit status, budgets and stop conditions, and
the exact next task. At closeout, reconcile `TASKS.yml`, gates, decisions, handoff, and memory.


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
