# /prod-gap

Analyze product requirements, current progress, implementation state, and production readiness. Write all technical and non-technical launch blockers to `plan/PROD-GAP.md` in the registered product workspace.

## How To Interpret

If the user says `/prod-gap`, `product gap`, `gap analysis`, `production gap`, `launch readiness`, `find gaps`, or asks what is missing before production launch, execute this file directly.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files in the registered product workspace.

1. `AGENTS.md`
2. `skills/prod-gap/SKILL.md`
3. `plan/main_plan.md`
4. `plan/`
5. `memories/MEMORY.md`
6. `DOUBTS.md`
7. `TASKS.yml`
8. `GATES.yml`
9. `CURRENT_STATE.md`
10. `DECISIONS.md`
11. `EVIDENCE_LOG.md`
12. `HANDOFF.md`
13. `COMPACT.md`
14. Product source tree, if present

## Loop

```text
READ PLAN -> READ PROGRESS -> INSPECT PRODUCT -> CLASSIFY LAUNCH GAPS -> SPLIT TECH/HUMAN -> PRIORITIZE -> WRITE plan/PROD-GAP.md -> UPDATE TASKS/HANDOFF
```

## Gap Categories

- Product / user gaps
- Market / evidence gaps
- UX / design gaps
- Architecture gaps
- Backend gaps
- Frontend gaps
- Data model gaps
- AI / automation gaps
- Integration gaps
- QA / validation gaps
- Security / privacy / compliance gaps
- DevOps / CI/CD / release gaps
- Documentation gaps
- Operational / support gaps
- Human-required launch blockers such as contracts, accounts, API keys, vendor signups, approvals, pricing, legal review, or production credentials

## Rules

- Do not invent product facts. Mark unknowns as gaps.
- Separate technical and non-technical gaps.
- Separate agent-solvable technical blockers from human-required blockers.
- Tie each gap to evidence, task, gate, or missing source when possible.
- Prioritize gaps as P0, P1, P2.
- For each P0/P1 gap, propose the next action.
- For technical P0/P1 gaps, create or update a task in `TASKS.yml`.
- For human-required P0/P1 gaps, list the exact human ask in `plan/PROD-GAP.md`, `DOUBTS.md`, and `HANDOFF.md`.
- Write output to `plan/PROD-GAP.md` in the product workspace.

## Optional Script

Use this to create or refresh the file structure. The script scans state files and the product source tree:

```bash
python scripts/prod_gap.py
```

Custom workspace:

```bash
python scripts/prod_gap.py --workspace ../product
```

## Output

Return:

1. `plan/PROD-GAP.md` path
2. Count of P0/P1/P2 gaps
3. Technical blockers the agent can solve
4. Human-required blockers the user must resolve
5. Next recommended command
