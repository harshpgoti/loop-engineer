---
name: continuous-learning
description: "[DEPRECATED - use continuous-learning-v2] Legacy v1 stop-hook skill extractor. v2 is a strict superset with instinct-based, project-scoped, hook-reliable learning. Do not invoke v1: when continuous learning, session learning, or pattern extraction is requested, route to continuous-learning-v2 instead."
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
# Continuous Learning Skill - DEPRECATED

> **DEPRECATED 2026-04-28.** Use `continuous-learning-v2` instead. v2 is a strict superset: stop-hook observation becomes PreToolUse/PostToolUse observation, full skills become atomic instincts with confidence scoring, and global-only storage becomes project-scoped plus global promotion.
>
> This file is kept for archival reference and backward compatibility with existing installs.

---

## Original v1 Documentation (archival)

Automatically evaluates agent harness sessions on end to extract reusable patterns that can be saved as learned skills.

## When to Activate

- Setting up automatic pattern extraction from agent harness sessions
- Configuring the Stop hook for session evaluation
- Reviewing or curating learned skills in `<agent-config-root>/skills/learned/`
- Adjusting extraction thresholds or pattern categories
- Comparing v1 (this) vs v2 (instinct-based) approaches

## Status

This v1 skill is still supported, but `continuous-learning-v2` is the preferred path for new installs. Keep v1 when you explicitly want the simpler Stop-hook extraction flow or need compatibility with older learned-skill workflows.

## How It Works

This skill runs as a **Stop hook** at the end of each session:

1. **Session Evaluation**: Checks if session has enough messages (default: 10+)
2. **Pattern Detection**: Identifies extractable patterns from the session
3. **Skill Extraction**: Saves useful patterns to `<agent-config-root>/skills/learned/`

## Configuration

Edit `config.json` to customize:

```json
{
  "min_session_length": 10,
  "extraction_threshold": "medium",
  "auto_approve": false,
  "learned_skills_path": "<agent-config-root>/skills/learned/",
  "patterns_to_detect": [
    "error_resolution",
    "user_corrections",
    "workarounds",
    "debugging_techniques",
    "project_specific"
  ],
  "ignore_patterns": [
    "simple_typos",
    "one_time_fixes",
    "external_api_issues"
  ]
}
```

## Pattern Types

| Pattern | Description |
|---------|-------------|
| `error_resolution` | How specific errors were resolved |
| `user_corrections` | Patterns from user corrections |
| `workarounds` | Solutions to framework/library quirks |
| `debugging_techniques` | Effective debugging approaches |
| `project_specific` | Project-specific conventions |

## Hook Setup

Add to your `<agent-config-root>/settings.json`:

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "<agent-config-root>/skills/continuous-learning/evaluate-session.sh"
      }]
    }]
  }
}
```

## Why Stop Hook?

- **Lightweight**: Runs once at session end
- **Non-blocking**: Doesn't add latency to every message
- **Complete context**: Has access to full session transcript

## Related

- Loop Engineer's own continuous learning system (v1).
- `/learn` command - Manual pattern extraction mid-session

---

## v1 Design Rationale

The v1 design uses a Stop hook at session end because it is lightweight, non-blocking, and has access to the full session transcript. The trade-off is that observation is probabilistic (fires only at session end, not on every tool call), patterns are saved as full skills (rather than atomic instincts), and there is no confidence scoring, no background observer, and no instinct promotion pipeline. This simplicity keeps the v1 skill easy to install but limits how reliably it captures learning. See: `<product-root>/docs/continuous-learning-v2-spec.md` for the v2 direction.


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
