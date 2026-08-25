# Deployment - Shipping, and Knowing What You Created

User-facing operations happen through `/deploy`, `/develop-product`, or natural language.
Shell examples below are internal runtime references for agents and maintainers, not steps
users must chain manually.

## Where deployment sits in the chain

Deployment is a **phase of the build loop**, not a separate tool the user has to remember:

```text
scaffold -> implement -> test -> converge -> evaluate -> release -> deploy
```

`scripts/build_phase.py` routes into `deploy` when three things are true at once:

1. the release gate has passed (or a task is explicitly deployment-phase work),
2. `DEPLOYMENT_PLAN.md` names a real cloud provider - not `TBD`,
3. at least one environment that plan names has **nothing recorded** in
   `plan/CLOUD_INVENTORY.md`.

A product whose environments are all deployed falls through to `converge` instead.
Re-deploying is a request, not a default - which is why `/deploy` exists as a way to ask
for it directly, and why "lets deploy this" routes to the same phase.

| Phase | Ends at |
|---|---|
| `release` | A plan: security, compliance, CI/CD, `DEPLOYMENT_PLAN.md`, release-check verdict |
| `deploy` | Real resources, verified, and every one of them recorded |

## Two rules that make it repeatable

### Never deploy from memory

Cloud CLIs, IAM shapes and service defaults change. A remembered command is a liability
when the failure mode is a real resource, a real bill, or a real outage.

So the deploy phase **reads the provider's current official documentation for every
command it is about to run**, and cites it in the report: `docs.aws.amazon.com`,
`cloud.google.com/docs`, `learn.microsoft.com/azure`, or the provider's own reference.
A step whose docs cannot be reached is a Stop Condition - the command is not improvised.

### Record each resource as it is created

Not at the end. A deploy that fails halfway is exactly when the record matters: whatever
was created is otherwise invisible, and becomes a resource nobody can attribute.

```bash
loop cloud add --env dev --provider aws --service RDS --resource denial-db-dev \
  --purpose "denial engine database" --scope denial --region ca-central-1 \
  --teardown "aws rds delete-db-instance --db-instance-identifier denial-db-dev"
```

## The inventory

`plan/CLOUD_INVENTORY.md` - a markdown table, parsed by column name, grouped by
environment:

```text
## dev

| ID    | Env | Provider | Service | Resource         | Purpose              | Scope  | Region      | Created    | Status | Teardown |
| R-001 | dev | aws      | ECS     | `denial-api-dev` | denial engine API    | denial | ca-central-1| 2026-08-24 | active | aws ecs delete-service … |
```

| Field | Why it exists |
|---|---|
| `Purpose` | The question the file exists to answer. A row without it is a resource nobody can attribute |
| `Scope` | Which sub-product it serves (see [`SCOPES.md`](SCOPES.md)); blank means platform-wide |
| `Env` | Decides whether it is disposable. `dev` is; `prod` and `staging` are not |
| `Teardown` | The removal command, captured while it is still known |
| `Status` | `active`, `deleted` or `failed`. Deleted rows **stay** - that a resource existed and was removed is history |

Recording is idempotent on `(env, provider, resource)`, so a retried deploy step updates
its row rather than adding a second one. Without that, the inventory stops being a count
of what exists.

**Never record a secret.** The name of a parameter or secret, never its value
(`AGENTS.md` #6).

## Dev is temporary, and that is the point

The expensive failure is not a failed deploy. It is a `dev` environment created to try
something, where the trying ended months ago and nobody can now tell which resources were
the experiment.

```bash
loop cloud teardown      # live dev resources, with age and recorded purpose
loop cloud orphans       # live resources with no purpose recorded
loop cloud summary       # counts per environment, and what needs attention
```

Three deliberate limits:

- **Only `dev` is ever suggested.** `prod` and `staging` are excluded by construction.
  Guessing about production is not acceptable when the action is deletion.
- **Staleness is judged on age**, which is a fact - not on whether the work "seems" done.
- **Deleting is a Stop Condition.** The candidates are listed with each purpose, and the
  user decides. After a confirmed deletion, the row is marked, not removed.

## Approval

Creating cloud resources is external, costly and not fully reversible, so it stops and
asks every time (`AGENTS.md` #5, [`CONTINUATION.md`](CONTINUATION.md)). One message with
the whole list and rough costs - never a prompt per resource, and never create-first-
report-after:

```text
Deploying `denial` to AWS dev (ca-central-1). This creates:
  - ECS Fargate service `denial-api-dev`   the API,                  ~$15/mo
  - RDS Postgres `denial-db-dev`           application database,     ~$13/mo
Both are dev and will be listed for teardown. Proceed?
```

Other Stop Conditions in this phase: a missing credential (named, never invented), an
unreachable provider doc, a `TBD` target, and any open launch blocker in
`plan/PROD-GAP.md` when the target is `prod`.

## Internal runtime reference

```bash
loop cloud list [--env dev|staging|prod]
loop cloud add --env <env> --provider <p> --service <s> --resource <r> --purpose <why> [--scope <slug>] [--region <r>] [--teardown <cmd>]
loop cloud mark <id> active|deleted|failed
loop cloud teardown [--stale-days N]
loop cloud orphans
loop cloud summary
```
