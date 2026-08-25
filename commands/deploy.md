# /deploy

Deploy the product to the cloud the plan chose, recording every resource created and what it serves - and later, say which of them can safely be removed.

## How To Interpret

If the user says `/deploy`, `deploy`, `lets deploy this`, `ship it to AWS`, `put this on the cloud`, `deploy to staging`, `what did we create in AWS`, `what can I delete`, or `tear down dev`, execute this file directly.

This is the same phase `/develop-product` reaches on its own once the release gate passes; typing it is a way of asking for it now.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read and write product-state files in the **active workspace**.

1. `AGENTS.md`
2. `skills/deploy/SKILL.md`
3. `skills/develop-product/phases/deploy.md`
4. `DEPLOYMENT_PLAN.md` - provider, region, compute, database, environments
5. `plan/CLOUD_INVENTORY.md` - what already exists
6. `plan/PROD-GAP.md` - launch blockers still open
7. `DECISIONS.md`
8. `skills/security-compliance/SKILL.md`, `skills/cicd-release/SKILL.md`

## Loop

```text
SESSION-START -> RESOLVE SCOPE -> READ TARGET -> PLAN RESOURCES -> **ASK** -> CREATE + RECORD EACH -> VERIFY -> REPORT
```

## Rules

- **Read the provider's current official docs before running any command.** Cloud CLIs
  and service defaults change; a wrong flag creates real resources that cost real money.
  Cite what you read. If the docs cannot be reached for a step, stop on that step.
- **Ask before creating anything.** One message listing every resource, its purpose and
  its rough cost - not a prompt per resource. Creating cloud resources is external,
  costly and not fully reversible (`AGENTS.md` #5).
- **Record each resource the moment it is created**, not at the end. A deploy that fails
  halfway is exactly when the inventory matters: whatever was created is otherwise
  invisible.
- **`--purpose` and `--scope` are required.** A row without them is a resource nobody can
  attribute or safely delete later.
- **Never record a secret.** The name of a parameter or secret, never its value
  (`AGENTS.md` #6).
- **`dev` is temporary; `prod` and `staging` are not.** Teardown suggestions only ever
  cover dev. Removing anything else is a deliberate request.
- **Deletion is a Stop Condition too.** List what would go, with each purpose, and ask.

## Scripts

Internal runtime the **agent** runs (`docs/INTERNAL_RUNTIME.md`). Never print these as
steps for the user:

```bash
loop cloud summary                    # what exists, per environment
loop cloud list --env dev
loop cloud add --env dev --provider aws --service RDS --resource denial-db-dev \
  --purpose "denial engine database" --scope denial --region ca-central-1 \
  --teardown "aws rds delete-db-instance --db-instance-identifier denial-db-dev"
loop cloud mark R-004 deleted
loop cloud teardown                   # dev resources that have outlived their reason
loop cloud orphans                    # live resources with no purpose recorded
```

## Continuation

Terminus: the chosen environment is deployed, verified, and every resource recorded.

Cascades. After a successful deploy, verify each resource, report the inventory, and
continue to closeout in the same run.

**Stop Conditions** - name which one fired and what you need:

1. **Approval to create** - always, before the first resource.
2. **Approval to delete** - always, before removing anything.
3. **A missing credential** - name it and how to provide it. Never guess or invent one.
4. **Unreachable provider documentation** for a step you are about to run.
5. **`TBD` target** - provider or region unresolved; run the deployment-plan phase first.
6. **An open launch blocker** in `plan/PROD-GAP.md` when the target is `prod`.

## Output

Return:

1. Environment and provider deployed to
2. Every resource created, with its inventory id, purpose and cost estimate
3. Verification result per resource
4. Dev resources flagged as temporary, with how to remove them
5. Anything awaiting a human, and which Stop Condition it is
