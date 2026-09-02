---
name: ml-engineering
description: Designs and validates ML datasets, training, evaluation, model registry, inference, monitoring, and rollback. Use when a product trains, selects, serves, or monitors learned models.
---

# ML Engineering

Inherits `docs/SKILL_CONTRACT.md`.

## Required method

1. Version dataset, code, configuration, environment, seed, and artifact provenance.
2. Separate train, validation, and test data; detect leakage and duplicated entities.
3. Define baseline, task and slice metrics, thresholds, and failure costs before training.
4. Record reproducibility limits and distinguish measured evidence from inference.
5. Stage deployment with shadow or canary evaluation, monitoring, and tested rollback.
6. Require human approval for high-impact decisions and sensitive-data use.

## Validation

- Frozen-dataset evaluation or a documented nondeterminism budget
- Leakage, drift, subgroup, robustness, latency, and cost checks where relevant
- Model-card, provenance, online/offline agreement, and rollback evidence

## Output

Return experiment identity, metrics versus baseline, slice results, provenance, validation
evidence, structured findings, deployment decision, and rollback conditions.

## Pre-Report Gate

Each HIGH or CRITICAL must clear four questions before it ships. Drop or downgrade if
any answer is "no":

1. Can I name the exact experiment id, dataset version, model checkpoint, and slice?
2. Can I describe the user-visible failure mode - which decision goes wrong, for whom, in
   what slice, at what threshold?
3. Have I confirmed the rule still applies after the current model/prompt/dataset change,
   not against a stale baseline?
4. Is the severity defensible at this stage of the product, not just in principle?

A clean run is a valid outcome. Stating "no findings" beats manufacturing one to look
thorough.

## Common False Positives

Skip these unless the ML system or stage of work shows otherwise. Each is a pattern the
LLM reviewer will reach for; in this codebase or stage, it is almost always wrong.

- "Use accuracy" on an imbalanced task. Accuracy on 99% class-A data is 99% trivial; cite the
  class distribution and the cost matrix that justify the metric.
- "Add more data" without naming the failure mode. More data fixes coverage gaps, not label
  noise, not spec ambiguity, not the wrong loss function.
- "Fine-tune the model" when a prompt change or retrieval fix solves the same problem at 1/100
  the cost. Fine-tune is the last lever, not the first.
- "Switch to a larger model" without a measurement of latency and cost. Larger models can
  regress both; cite the score, the cost, and the latency budget.
- "Add cross-validation" on a dataset that is temporal or has entity-level leakage. K-fold
  here hides leakage; time-based or group-based split is the right answer.
- "Drop the rare class" because it is small. Rare is a feature of the world; downsampling to
  inflate a metric is selection bias.
- "Use F1" without naming which class is the positive. F1 of class A and F1 of class B are
  different metrics; "the F1" of a multi-class problem is a category error.
- "Train longer" without a learning-curve diagnostic. Training past the optimum overfits;
  cite the validation curve.
- "Normalize the features" on a tree-based model. Trees are scale-invariant; the reviewer
  missed the model type.
- "Add a regularization term" without a measured overfitting gap. Regularization fixes
  variance, not bias; cite the gap.
- "Set the random seed for reproducibility" when the upstream library is non-deterministic
  on the chosen hardware (some GPU ops). Cite the determinism budget, not just the seed.
- "Use the latest model checkpoint" - the reviewer missed the registry policy. The registry
  decides; do not bypass it.
- "Online eval disagreeing with offline" - the reviewer named the gap but not the cause. Name
  the slice, the population shift, and the time window before calling this a finding.


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
