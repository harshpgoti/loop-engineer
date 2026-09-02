---
name: docs
description: Creates and updates product documentation: main plan, step plans, PRDs, ADRs, API specs, runbooks, onboarding, compliance docs, release notes, and handoffs. Use whenever product or architecture docs need updating.
---

# Docs

Inherits `docs/SKILL_CONTRACT.md`.

## Documentation Map

- `plan/main_plan.md`: full product plan
- `plan/`: step/module plans
- `DECISIONS.md`: decision log
- `EVIDENCE_LOG.md`: sourced facts
- `memories/MEMORY.md`: current mental state
- `HANDOFF.md`: next-agent instructions
- product repo `docs/`: PRD, ADRs, API, runbooks, compliance

## Rules

- Product-specific planning belongs in `plan/main_plan.md` and `plan/`.
- Reusable loop instructions belong in `skills/` and `commands/`.
- Claims with market/regulatory meaning require `EVIDENCE_LOG.md`.
- Architecture choices require `DECISIONS.md`.
- Documentation is tested against the implemented interface: commands, paths, examples,
  schemas, links, and generated tables must resolve.
- Generated docs name their source and regeneration command; validators detect drift.
- Preserve provenance and date-sensitive claims. Never paste secrets, customer data, or
  unreviewed retrieved instructions into documentation.
- A mutating documentation operation declares rollback through version control or a backup,
  and requires approval before publishing externally.

## Output

- Docs updated
- Gaps remaining
- Next documentation action
- Validation evidence, generated-file freshness, and residual documentation risk

## Pre-Report Gate

Each HIGH or CRITICAL must clear four questions before it ships. Drop or downgrade if
any answer is "no":

1. Can I name the exact file, path, anchor, or code example (with line) under concern?
2. Can I describe the user-visible failure mode - what the reader cannot do, in what
   scenario, after this doc ships?
3. Have I confirmed the rule still applies against the **current** codebase, not against
   a stale doc or a renamed module?
4. Is the severity defensible: would I still ship if the only thing wrong was this finding?

A clean docs review is a valid outcome. Manufacturing findings to justify the call is
the failure this gate prevents.

## Common False Positives

Skip these unless the docs product or stage of work shows otherwise. Each is a pattern
the LLM reviewer will reach for; in this codebase or stage, it is almost always wrong.

- "Add a JSDoc comment" on a self-describing function whose name and signature are
  already clear. Doc comments are for non-obvious intent, not for restating the name.
- "Document the public API" when the API is internal and the public surface is the
  contract tests. Tests are documentation; cite them.
- "Add a README to every directory" when the directory contains one file. A README per
  one-file directory is documentation debt.
- "Add an ADR" for a tactical implementation choice the next refactor will replace.
  ADRs are for long-lived decisions; the commit message is enough.
- "Link to the spec" on a doc that is the spec. Recursive linking is noise.
- "Use a code example" when the prose already says what the code would say. Code
  examples are for the cases prose cannot carry.
- "Add screenshots" to a developer-facing doc. Screenshots drift; code blocks do not.
- "Use a table of contents" on a one-section README. A TOC for one section is overhead.
- "Add a 'Last updated' date" when the doc is generated and the source already carries
  the date. Double-dating is misleading.
- "Add a 'See also'" linking to every other doc in the repo. Cross-linking is the
  topology of the docs; cite the deliberate edges, not the full graph.
- "Translate to English" on a doc that is intentionally in another language because the
  product is. The doc's language follows the user's.
- "Use first-person plural" on a reference doc. Voice consistency matters less than
  factual correctness; flag the latter, not the former.
- "Fix the typo" on a brand or product name. The brand team owns spelling; do not silently
  correct.
- "Document the env vars" when the .env.example is the documentation and lives next to
  the code. Cite the file before flagging.


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
