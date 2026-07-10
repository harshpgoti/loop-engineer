# /session-recall

Search past loop sessions in `state.db` and write `plan/SESSION_RECALL.md` so the agent reuses prior decisions at session start.

## How To Interpret

If the user says `/session-recall`, `session recall`, or asks what was decided before, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/session-recall/SKILL.md`
3. `plan/main_plan.md`
4. `CURRENT_STATE.md`
5. `HANDOFF.md`
6. `plan/SESSION_RECALL.md` if it exists

## Loop

```text
INIT DB -> EXTRACT KEYWORDS -> FTS SEARCH -> WRITE SESSION_RECALL -> POINTER IN HANDOFF
```

## Script

```bash
python scripts/session_recall.py
loop recall
```

Custom query:

```bash
python scripts/session_recall.py --query "deployment AWS"
loop recall --query "deployment AWS"
```

## When To Run

- At the start of `/plan`, `/product-develop`, and `/loop-engine`
- Before asking the user a question that may already be answered in past sessions
- After long gaps between sessions

## Output

Return:

1. `plan/SESSION_RECALL.md` path
2. Number of hits and query used
3. Top recalled decisions to reuse
4. Reminder not to re-ask unless the user wants to change something
