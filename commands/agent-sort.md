# /agent-sort

Classify the canonical skills, commands, agents, rules, and hooks in a workspace
as DAILY (load every session) or LIBRARY (keep accessible, do not auto-load).
Run parallel subagent review passes over each surface and write an
evidence_table.

## How To Interpret

If the user says `/agent-sort`, `sort skills into daily and library`, `what should
we auto-load`, or asks to keep the loaded set small, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/agent-sort/SKILL.md`
3. `manifests/skill_policy.json`
4. `manifests/capabilities.json`
5. `manifests/agents.json`
6. the workspace's `commands/` and `skills/`

## Loop

```text
LAUNCH 5 PARALLEL SUBAGENTS (skills, commands, agents, rules, hooks+extras) -> COLLECT evidence_tables -> WRITE REPORT
```

## Output

`plan/AGENT_SORT_REPORT.md` with:

- Per-surface evidence tables (one row per surface element)
- Summary counts (DAILY vs LIBRARY per surface)
- Recommended default working set
- Recommended DAILY-by-exception set
- DAILY items that lack evidence of use (move to LIBRARY)

## Continuation

The DAILY set is what the chain auto-loads. Update the harness's loader
configuration to honour the recommendation. Re-run when the surface changes
(a new skill, a new command).