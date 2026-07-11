# /deployment-plan

Write or refresh `DEPLOYMENT_PLAN.md` for the active product workspace. Reuse prior cloud, LLM, and deployment decisions when already recorded. Ask the user only for unresolved choices.

## How To Interpret

If the user says `/deployment-plan`, `deployment plan`, or a development loop is completing and deployment targets are not documented, execute this file directly.

This command is also invoked automatically at closeout of `/product-develop` and `/loop-engine`.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files in the registered product workspace.

1. `AGENTS.md`
2. `skills/deployment-plan/SKILL.md`
3. `plan/main_plan.md`
4. `DECISIONS.md`
5. `DOUBTS.md`
6. `memories/MEMORY.md`
7. `plan/PROD-GAP.md`
8. `RELEASE_CHECK.md`
9. relevant `plan/step_*.md`

## Loop

```text
READ PRIOR DECISIONS -> REUSE KNOWN ANSWERS -> IDENTIFY OPEN QUESTIONS -> WRITE DEPLOYMENT_PLAN.md -> UPDATE DOUBTS/HANDOFF -> ASK USER IF NEEDED
```

## Reuse Rule

If cloud provider, multi-cloud strategy, LLM provider/manage-model, or related deployment choices were already discussed:

- copy the same answer into `DEPLOYMENT_PLAN.md`
- mark it as reused
- inform the user instead of asking again

## Optional Script

```bash
python scripts/deployment_plan.py
```

Custom workspace:

```bash
python scripts/deployment_plan.py --workspace ../product
```

## Output

Return:

1. `DEPLOYMENT_PLAN.md` path
2. Reused decisions
3. Open deployment questions
4. Whether the user must answer now
