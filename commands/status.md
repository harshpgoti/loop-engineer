# /status

Show a quick snapshot of the active product workspace: current product, gate, task, human blockers, and the next recommended command.

## How To Interpret

If the user says `/status`, `status`, `where am I`, `what is next`, or `show current state`, execute this file directly.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files in the registered product workspace.

1. `AGENTS.md`
2. `skills/status/SKILL.md`
3. `memories/MEMORY.md`
4. `DOUBTS.md`
5. `plan/main_plan.md`
6. `TASKS.yml`
7. `GATES.yml`
8. `CURRENT_STATE.md`
9. `HANDOFF.md`
10. `plan/PROD-GAP.md`

## Loop

```text
READ STATE -> SUMMARIZE -> WRITE STATUS.md -> UPDATE HANDOFF IF NEEDED
```

## Optional Script

```bash
python scripts/status.py
```

Custom workspace:

```bash
python scripts/status.py --workspace ../product
```

Workspace detection helper:

```bash
python scripts/detect_workspace.py
```

## Output

Return:

1. `STATUS.md` path
2. Current workspace and product
3. Active gate and task
4. Open human blockers
5. Next recommended command
