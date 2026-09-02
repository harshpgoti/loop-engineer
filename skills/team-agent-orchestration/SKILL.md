---
name: team-agent-orchestration
description: "Run team-based orchestration for agent squads using work items, ownership, agent Kanban, merge gates, and control pane handoffs. Use when coordinating an agent squad with work items, ownership, Kanban, and merge gates."
metadata:
  origin: Loop Engineer
---
## Loop Engineer integration

Inherits `docs/SKILL_CONTRACT.md`.

This capability is selected by `scripts/agent_skill_router.py` and executed through
`skills/agent-development/SKILL.md`. Record its concrete decisions and outputs in the
appropriate `agent/` artifact (`AGENT_ARCHITECTURE.md`, `HARNESS.md`,
`ORCHESTRATION.md`, `MEMORY.md`, `OPERATIONS.md`, or `evals/`) and reconcile tasks,
gates, decisions, and handoff before closeout.

Loop Engineer rules override provider-specific examples below. Examples naming a
particular model, CLI, hook system, scheduler, MCP server, or agent host are adapters,
not mandatory dependencies. Prefer deterministic local mechanisms already present in
the active product. Installing software, transferring context to another provider,
enabling background execution, spending money, or changing external state requires the
authorization that action normally requires. Never place secrets or sensitive data in
prompts, traces, fixtures, memory, or reports.

**Approval:** obtain it immediately before any high-risk external action. **Rollback:**
record how generated state, schedules, configuration, or code can be reverted before
mutation. **Validation:** verify the capability through its public interface and required
behavioral evals. **Output:** report artifacts changed, evidence, test/eval results, budgets,
remaining gates, and the next action.
# Team Agent Orchestration

Use this skill when agents are being managed like a team rather than a single assistant. The purpose is to make team-based orchestration reliable: clear work items, explicit ownership, agent Kanban state, branch isolation, control pane visibility, and merge gates.

## When To Activate

- The task spans multiple agents, tools, harnesses, branches, or worktrees.
- The user mentions team orchestration, agent Kanban, squad, conductor, control pane, manager, or multi-agent work.
- A project needs shared workflow state across people and agents.
- Existing agent fan-out is producing output but not mergeable product.

## Operating Model

Treat every agent as a teammate with a narrow contract:

- **Owner**: the person or agent accountable for the work item.
- **Scope**: files, branch, tool surface, and forbidden areas.
- **State**: backlog, ready, running, review, blocked, merged, or archived.
- **Evidence**: tests, screenshots, logs, review notes, or eval reports.
- **Merge gate**: the exact condition that allows integration.

## Agent Kanban

Use agent Kanban when work must be visible across sessions.

| Column | Meaning | Exit Criteria |
| --- | --- | --- |
| Backlog | Candidate work item, not yet shaped | Acceptance criteria written |
| Ready | Shaped and assignable | Owner and branch/worktree assigned |
| Running | Agent is actively working | Handoff artifact and changed files exist |
| Review | Work is complete but not merged | Tests, diff review, and risk check pass |
| Blocked | Needs external input or failed gate | Blocker has owner and next action |
| Merged | Integrated into mainline | PR merged or local main updated |
| Archived | No longer relevant | Reason recorded |

Each card should fit this schema:

```json
{
  "id": "agent-card-001",
  "title": "Build dynamic workflow skill",
  "owner": "codex",
  "state": "running",
  "branch": "product/dynamic-workflow-team-orchestration",
  "worktree": ".",
  "acceptance": [
    "Skill exists",
    "Tests cover required concepts",
    "Content artifact contains video and article angles"
  ],
  "merge_gate": "lint, focused tests, and catalog check pass",
  "handoff": "path/to/handoff.md"
}
```

## Team-Based Orchestration Flow

1. **Shape the board**: convert fuzzy ambition into work items with owners and merge gates.
2. **Pick execution mode**: single-agent, dynamic workflow mode, dmux/tmux, worktree fan-out, or external desktop orchestrator.
3. **Assign boundaries**: one owner per card, clear file scope, and no overlapping writes without an integrator.
4. **Run agents**: each agent writes evidence and handoff notes, not just code.
5. **Review in sequence**: tests first, then diff review, then security/risk checks, then content/product polish.
6. **Merge deliberately**: one integrator resolves conflicts and updates the control pane or status artifact.
7. **Extract reusable skill**: if the card pattern repeats, promote it into `skills/`.

## Control Pane Requirements

A useful control pane for team orchestration should show:

- Active work items and their agent Kanban state.
- Owner, harness, branch, worktree, and last heartbeat.
- Links to handoff artifacts, tests, screenshots, and PRs.
- Blockers grouped by owner and unblock action.
- Merge readiness by gate, not vibes.
- Reusable workflow candidates that should become shared skills.

Do not add more automation until the operator can answer: who owns this, what changed, what gate failed, and what can safely merge?

## Dynamic Workflow Compatibility

When a card needs dynamic workflow mode:

- Put the task-local harness under the card owner.
- Store inputs and outputs on the card.
- Require an eval before moving from Running to Review.
- Promote the harness to a shared skill only after repeat use.

## Failure Modes To Watch

- **Agent soup**: many agents running, no owner or merge gate.
- **Invisible work**: useful output exists only in a chat transcript.
- **Board theater**: a Kanban board exists but cards have no acceptance criteria.
- **Overlapping writes**: parallel agents edit the same files without worktrees.
- **No product artifact**: the process produces docs but no runnable or publishable surface.

## Output Standard

Finish each orchestration pass with:

- Board/card changes.
- Merged or pending branches.
- Tests and eval evidence.
- Blockers with owner and next action.
- New shared skill candidates.


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
