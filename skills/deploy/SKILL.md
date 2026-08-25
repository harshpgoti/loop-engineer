---
name: deploy
description: Deploy the product to its chosen cloud and keep a record of every resource created - what it serves, which environment and product scope it belongs to, and how to remove it. Use when the user types /deploy, says "lets deploy this", asks to ship to a cloud, asks what was created in their cloud account, or asks what can safely be deleted or torn down.
---

# Deploy

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
