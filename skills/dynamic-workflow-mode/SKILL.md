---
name: dynamic-workflow-mode
description: Design a task-local harness for a non-trivial recurring task using the {Objective, Inputs, Loop, Eval, Handoff} template. Decide whether the task stays inline, becomes a local harness, becomes a new skill, or needs a control pane and human gate. Use when the same multi-step work keeps recurring without an obvious skill or command to attach to.
---

# Dynamic Workflow Mode

Inherits `docs/SKILL_CONTRACT.md`.

Some tasks are too big to inline once and too specific to deserve a permanent skill. They
live in the middle ground: repeated multi-step work that needs structure, evaluation, and
a handoff but is not a product feature. This skill designs the harness for that
middle-ground task.

## When to use

- the same multi-step work recurs across sessions without a clear skill or command;
- the work has a clear input shape, an observable success state, and a clear next step;
- the work benefits from a deterministic shell (loop + eval + handoff) but not from a
  full product feature spec;
- the user wants to formalise a recurring exploration without committing to a permanent
  skill yet.

## When NOT to use

| Instead of dynamic-workflow | Use |
|---|---|
| A one-shot exploration | just do the work |
| A feature that ships to users | `feature-workflow` / `feature-new` |
| A permanent skill candidate (already known) | promote to a skill |
| Cross-team coordination | `team-builder` or `team-agent-orchestration` |

## The Harness Template

Every dynamic workflow has six fields. Fill each one explicitly; do not leave any blank.

```yaml
objective: <one sentence - what "done" means for one run>
inputs: <what this run needs to start; concrete files, queries, decisions>
loop: <the deterministic steps; numbered, each with success criterion>
eval: <how a run is scored; pass@k, pass^k, or a fixed rubric>
handoff: <what the run produces; the next consumer, file, or command>
human_gate: <if any, what blocks the chain from continuing automatically>
```

If any field cannot be filled, the work is not yet a workflow - it is still a one-shot.
Keep the work inline until the structure sharpens.

Before locking the design, run the five-failure-mode review in
`skills/loop-design-check/SKILL.md` - a harness that cannot fail, fall back, or anchor
itself to something external is not a loop yet.

## Decision Tree: where the harness lives

```
Is the task a single focused change?
  +-- Yes -> do it inline; no harness
  +-- No  -> is there a written spec or RFC?
            +-- Yes -> is parallel implementation valuable?
                      +-- Yes -> ralphinho-rfc-pipeline / team-agent-orchestration
                      +-- No  -> continuous-agent-loop / develop-product
            +-- No  -> do many variations of the same thing matter?
                      +-- Yes -> infinite-loop with eval gate
                      +-- No  -> sequential with a de-sloppify pass
```

The decision tree above decides **which** harness, not **whether** to use one. This
skill is the place that picks the harness and writes the harness file. Use it before
the work recurs a third time.

## Workflow

### 1. Identify the recurring task

The candidate tasks for a dynamic workflow have three properties:
- they recur (at least twice in `state.db` or in session notes);
- they have a measurable output (file, decision, scored run);
- they have a clear handoff to a downstream consumer.

If the task has not recurred, **stop** and do the work inline. The workflow is premature
at this stage.

### 2. Fill the template

For each candidate, write the six fields explicitly. Empty fields fail the harness check.

### 3. Pick the harness shape

Use the decision tree above. Each shape has an associated LE capability and existing skill:

| Shape | LE capability | Existing skill to invoke |
|---|---|---|
| One-shot inline | none | | direct execution |
| RFC DAG | `agent-systems` | `ralphinho-rfc-pipeline` |
| Sequential with de-sloppify | `quality` | `continuous-agent-loop` |
| Parallel Kanban | `agent-systems` | `team-agent-orchestration` |
| Eval-gated loop | `quality` | `eval-harness` |
| Adversarial closed loop | `quality` | `gan-style-harness` |

### 4. Write the harness file

The harness file lives at `<workspace>/.loop/harnesses/<name>.md` (never inside the app
repo). It contains the filled template + the picked shape + the link to the existing
skill that executes it.

### 5. Decide stop conditions

A harness that runs forever is a bug. Name:
- max iterations (typical: 5 for adversarial, 20 for sequential);
- max cost in tokens or dollars;
- max wall-clock duration;
- a **completion signal** - what observable event declares "done";
- a **fail signal** - what observable event declares "stop, escalate to user."

A harness without stop conditions cannot be promoted to a skill later.

## Output

- A filled `{Objective, Inputs, Loop, Eval, Handoff, Human_gate}` template.
- The picked harness shape and the existing LE skill that runs it.
- Stop conditions with named observable signals.
- The path of the harness file (typically `<workspace>/.loop/harnesses/<name>.md`).

## Anti-Patterns

- A harness that describes *what the agent should think* rather than what it should *do*.
  A harness is operational, not aspirational.
- Empty fields. Every field is filled or the harness does not exist.
- Implicit stop conditions. "Run until good" is not a stop condition.
- A harness that depends on a tool or MCP server that is not in `capabilities.json`. The
  harness fails open the first time it runs.
- A harness that bypasses the chain. The harness is a stage inside an existing chain, not a
  replacement for `/plan-loop` or `/develop-product`.

## Related Skills

- `continuous-agent-loop` - the canonical loop-pattern catalog;
- `ralphinho-rfc-pipeline` - DAG decomposition for spec-driven work;
- `eval-harness` - capability vs regression evals with `pass@k / pass^k`;
- `team-agent-orchestration` - parallel Kanban for multi-agent work;
- `gan-style-harness` - adversarial closed loop;
- `team-builder` - interactive picker for composing ad-hoc teams.


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
