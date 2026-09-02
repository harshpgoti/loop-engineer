---
name: deploy
description: Deploy the product to its chosen cloud and keep a record of every resource created - what it serves, which environment and product scope it belongs to, and how to remove it. Use when the user types /deploy, says "lets deploy this", asks to ship to a cloud, asks what was created in their cloud account, or asks what can safely be deleted or torn down.
---

# Deploy

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Two jobs, and the second is what makes the first safe to repeat:

1. **Deploy** the product to the cloud `DEPLOYMENT_PLAN.md` chose.
2. **Record** every resource created, with the thing it serves, so the account stays
   readable and a temporary environment can be found and removed later.

The expensive failure this exists to prevent is not a failed deploy. It is a `dev`
environment created to try something, where the trying ended months ago and nobody can
now tell which resources were the experiment.

## Read First

- `commands/deploy.md`
- `skills/develop-product/phases/deploy.md` - the phase this skill backs
- `DEPLOYMENT_PLAN.md`, `plan/CLOUD_INVENTORY.md`, `plan/PROD-GAP.md`, `DECISIONS.md`

## This is part of the build chain

`/develop-product` reaches this phase itself once the release gate passes and the plan
names a real provider with an environment that has nothing recorded yet. The user does
not have to know that - "lets deploy this" and `/deploy` route to the same place.

Which means: do not treat a deploy request as a fresh start. Read what is already in the
inventory first, or you will create a second copy of something that exists.

## Never deploy from memory

Cloud CLIs, IAM shapes and service defaults change often enough that a remembered command
is a liability. **Read the provider's current official documentation for each command you
are about to run**, and cite it in the report:

| Provider | Documentation |
|---|---|
| AWS | `docs.aws.amazon.com` - service guide plus the CLI reference for the exact subcommand |
| Google Cloud | `cloud.google.com/docs` and the `gcloud` reference |
| Azure | `learn.microsoft.com/azure` and the `az` reference |
| Others (Fly, Render, Vercel, Cloudflare, Supabase, …) | that provider's own current docs |

A step whose documentation cannot be reached is a Stop Condition. Say which step, and do
not improvise the command - an invented flag creates a real resource or a real outage.

## The order that matters

1. **Target** from `DEPLOYMENT_PLAN.md`. A `TBD` provider or region means the deployment
   plan is not finished; run that first rather than choosing on the user's behalf.
2. **Environment** stated explicitly - `dev`, `staging`, `prod`. Never inferred.
3. **Existing resources** from `loop cloud list --env <env>`, so a re-run updates rather
   than duplicates.
4. **Plan every resource** with purpose and rough cost - then ask, once, in one message.
5. **Create and record, one at a time.** Record immediately, never in a batch at the end.
6. **Verify** each one actually serves - endpoint answers, migrations ran, logs clean.
7. **Report** with inventory ids, and name the dev resources as temporary.

## Recording

```bash
loop cloud add --env dev --provider aws --service ECS \
  --resource denial-api-dev --purpose "denial engine API" --scope denial \
  --region ca-central-1 --teardown "aws ecs delete-service --service denial-api-dev --force"
```

| Field | Why it is required |
|---|---|
| `--purpose` | The question the inventory exists to answer. A row without it is a resource nobody can attribute |
| `--scope` | Which sub-product it serves (see `skills/scope/SKILL.md`). Blank means platform-wide |
| `--env` | Decides whether it is temporary. `dev` is; `prod` and `staging` are not |
| `--teardown` | The command that removes it, captured while you still know it |

Recording is idempotent on `(env, provider, resource)`, so a retried step updates its row
instead of adding a second one.

**Never record a secret.** The name of a parameter or secret is fine; its value is not
(`AGENTS.md` #6).

## Approval is not optional

Creating cloud resources is external, costly and not fully reversible, so it is a Stop
Condition every time (`AGENTS.md` #5, `docs/CONTINUATION.md`). Prepare the full list and
ask once:

> Deploying `denial` to **AWS dev** (ca-central-1). This creates:
> - ECS Fargate service `denial-api-dev` - the API, ~$15/mo
> - RDS Postgres `denial-db-dev` (db.t4g.micro) - application database, ~$13/mo
>
> Both are dev and will be listed for teardown. Proceed?

Never create first and report after. Never ask per resource - one question, one answer.

## Answering "what can I delete?"

```bash
loop cloud teardown      # live dev resources, with age and recorded purpose
loop cloud orphans       # live resources with no purpose recorded
loop cloud summary       # counts per environment
```

- Only `dev` is ever suggested. `prod` and `staging` are excluded by construction -
  guessing about production is not acceptable when the action is deletion.
- Staleness is judged on **age**, which is a fact, not on whether the work "seems" done.
- Deleting is its own Stop Condition: list what would go with each purpose, and ask.
- After a confirmed deletion, `loop cloud mark <id> deleted` - the row stays. That a
  resource existed and was removed is part of the account's history.

## Failure mid-deploy

Stop and report what was **already created**, with inventory ids. That list is the whole
reason recording happens per resource rather than at the end: a half-finished deploy that
was not recorded leaves resources nobody can find.

Do not roll back automatically - deleting is a Stop Condition in both directions. Say
what exists, what it cost to create, and ask.

## Rules

- Read the official docs for every command; cite them.
- Ask before creating. Ask before deleting.
- Record each resource as it is created, with purpose and scope.
- Never write a credential into the inventory, the plan, the logs, or the report.
- `prod` deploys stop on any open launch blocker in `plan/PROD-GAP.md`.
- The `loop cloud` lines here are yours to run, never to print. Report what they say.


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
