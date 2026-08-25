# Phase: Deploy

> Loaded by `skills/develop-product/SKILL.md` when `BUILD PHASE: deploy` - release
> readiness passed and the product is going onto real infrastructure. Load only this file.

## Purpose

Put the product on the cloud the plan chose, and **write down every resource created**
as it is created.

The release phase ends at a plan. This phase is the part that touches a real account, so
it is the one phase in the loop where the default is to **stop and ask** before acting.

## Read First

1. `DEPLOYMENT_PLAN.md` - the target: provider, region, compute, database, environments
2. `plan/CLOUD_INVENTORY.md` - what already exists, so nothing is created twice
3. `DECISIONS.md` - the cloud decision and anything that constrains it
4. `plan/PROD-GAP.md` - launch blockers still open
5. `skills/deploy/SKILL.md` - the full contract for recording and teardown
6. `skills/cicd-release/SKILL.md`, `skills/security-compliance/SKILL.md`

## Never deploy from memory

Cloud CLIs, IAM shapes and service defaults change, and a wrong flag here creates real
resources that cost real money. **Read the provider's current official documentation for
every command you are about to run** - `docs.aws.amazon.com`, `cloud.google.com/docs`,
`learn.microsoft.com/azure`, or the provider's own reference - and cite what you read in
the deploy report.

If documentation for a step cannot be reached, that step is a Stop Condition. Say which
step and why; do not improvise the command.

## Process

### 1. Establish the target

From `DEPLOYMENT_PLAN.md`. If provider, region or environment is still `TBD`, run the
deployment-plan skill first - deploying against a `TBD` is how a product lands in the
wrong region.

### 2. Confirm the environment

`dev`, `staging` or `prod`. Never infer it:

- **dev** - temporary by default. Everything created here is expected to be torn down.
- **staging** / **prod** - durable. Deletion later requires the same approval as creation.

### 3. Plan the resources, then ask

Produce the list *before* touching anything: every resource, its purpose, its estimated
cost, and whether it already exists in the inventory. Then ask for approval in one
message - not per resource:

> Deploying `denial` to **AWS dev** (ca-central-1). This creates:
> - ECS Fargate service `denial-api-dev` - the API, ~$15/mo
> - RDS Postgres `denial-db-dev` (db.t4g.micro) - application database, ~$13/mo
> - S3 bucket `denial-uploads-dev` - document uploads, ~$1/mo
>
> All three are dev and will be listed for teardown. Proceed?

**This is a Stop Condition** (`AGENTS.md` #5, `docs/CONTINUATION.md` #2). Creating cloud
resources is external, costly and not fully reversible. Prepare and ask - never create
first and report after.

### 4. Execute, recording as you go

For each resource, in order: run the command, verify it succeeded, then **immediately**
record it:

```bash
loop cloud add --env dev --provider aws --service ECS \
  --resource denial-api-dev --purpose "denial engine API" --scope denial \
  --region ca-central-1 --teardown "aws ecs delete-service --service denial-api-dev --force"
```

Record it **when it is created, not at the end**. A deploy that fails halfway is exactly
when the inventory matters most: without it, the half that was created is invisible and
becomes an orphan nobody can attribute.

`--purpose` and `--scope` are not paperwork. They are the two questions the inventory
exists to answer, and a row without them is a resource nobody can safely delete later.

### 5. Verify

Health-check the deployed thing - the endpoint answers, migrations ran, logs are clean.
A resource that exists but does not serve is not a deployment.

### 6. Report

What was created, per environment, with the inventory ids. Name the dev resources
explicitly as temporary, and say how to remove them.

## Secrets

Never write credentials into the inventory, the plan, logs or the report
(`AGENTS.md` #6). Record the *name* of a secret or parameter, never its value. If the
deploy needs a credential the workspace does not have, that is a Stop Condition: name
the credential and how to provide it.

## Tearing down

When the user asks what can be removed, or a dev environment has served its purpose:

```bash
loop cloud teardown      # dev resources that have outlived their reason
loop cloud orphans       # live resources with no purpose recorded
```

Deletion is irreversible, so it is always a Stop Condition: list what would go, with the
purpose recorded for each, and ask. After a confirmed deletion, mark the row
(`loop cloud mark R-004 deleted`) rather than removing it - that the resource existed and
was torn down is part of the account's history.

`prod` and `staging` never appear in teardown candidates. Removing those is a deliberate
request, never a suggestion this phase makes.

## Continue automatically

- **Approved and succeeded** -> verify, record, report, continue to closeout.
- **Approval needed, credential missing, doc unreachable, or a step failed** ->
  Stop Condition. Name what happened, what was already created (with inventory ids), and
  what you need.

## Output

1. Environment and provider deployed to
2. Every resource created, with its inventory id and purpose
3. Verification result per resource
4. Dev resources flagged as temporary, with their teardown commands
5. Anything awaiting a human
