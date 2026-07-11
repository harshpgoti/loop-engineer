# Process Architecture

Loop Engineering OS has three command loops.

## `/plan-loop`

```text
detect init
-> ask/infer product + deployment inputs
-> product grill
-> product council
-> evidence log
-> product plan + deployment table in plan/main_plan.md
-> task compiler
-> deployment plan draft
-> output validation
-> memory/handoff
-> compact if needed
```

Key skills:

- `skills/plan-loop/SKILL.md`
- `skills/plan-loop/phases/grill.md`
- `skills/plan-loop/phases/council.md`
- `skills/plan-loop/phases/task-compiler.md`
- `skills/deployment-plan/SKILL.md`

## `/product-develop`

```text
select task
-> implementation plan
-> smallest safe diff
-> tests
-> code review
-> QA validation
-> security/risk check
-> docs
-> prod-gap
-> fix agent-solvable blockers or ask user for human-required blockers
-> memory/handoff
-> compact if needed
```

Key skills:

- `skills/product-develop/SKILL.md`
- `skills/implementation-planner/SKILL.md`
- `skills/code-reviewer/SKILL.md`
- `skills/qa-validation/SKILL.md`
- `skills/security-compliance/SKILL.md`

## `/loop-engine`

```text
read memory/doubts/gates
-> choose route
-> plan / compile / develop / QA / release
-> prod-gap
-> route technical blockers or ask human
-> validate
-> update memory
```

Key skills:

- `skills/loop-engine/SKILL.md`
- `skills/cicd-release/SKILL.md`
- `skills/tool-orchestrator/SKILL.md`
- `skills/compact-loop/SKILL.md`

## `/prod-gap`

```text
read product plan/progress/source
-> compare requirements vs current state
-> classify technical and non-technical gaps
-> prioritize P0/P1/P2
-> write plan/PROD-GAP.md
```

Use when the user asks what is missing, what blocks release, or what gaps remain.

When called from `/product-develop` or `/loop-engine`, P0/P1 technical blockers should be routed back into development when safe. Human-required blockers should be recorded in `DOUBTS.md` and `HANDOFF.md` and asked to the user at loop closeout.

## `/deployment-plan`

```text
read decisions/doubts/plan-loop
-> reuse known cloud/LLM/deployment answers
-> identify open deployment questions
-> write DEPLOYMENT_PLAN.md
-> ask user only for unresolved items
```

Run automatically at closeout of `/product-develop` and `/loop-engine`, and after `/release-check` when preparing launch.

## `/compact-loop`

```text
read state
-> summarize current product context
-> write COMPACT.md
-> update HANDOFF.md
-> optionally use native tool compaction
```

Use before tool switches and during long loops.

## `/upgrade-loop-engineer`

```text
compact-loop
-> detect separate vs embedded setup
-> protect product-state files
-> dry-run upgrade
-> apply only with approval
-> validate
```

Use when updating the reusable loop tool while preserving product data.

## `/status`

```text
read memory/gates/tasks/handoff/prod-gap
-> summarize current workspace
-> write STATUS.md
```

## `/doctor`

```text
check tool files
-> check workspace registration
-> import scripts
-> run validators
-> write DOCTOR.md
```

## `/sync-loop-state`

```text
read memory/handoff/tasks/gates/compact/prod-gap
-> detect drift
-> apply safe fixes
-> write SYNC_REPORT.md
```

## `/release-check`

```text
read gates/prod-gap/source tree
-> check tests/ci/env/secrets/docs/deploy
-> write RELEASE_CHECK.md
```

## Workspace Migrations

```text
detect workspace version
-> apply pending migrations
-> update .loop-workspace-version
```

See `migrations/README.md`.

## Quality Rubrics

- `evals/plan_quality_rubric.md`
- `evals/development_quality_rubric.md`

## Validation

```bash
python scripts/validate_template.py
python scripts/validate_outputs.py
```
