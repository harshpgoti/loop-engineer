# Codex Adapter

Codex should use the same canonical loop as every other agent.

## Always-on lifecycle

Run at every Codex session that touches the product:

```bash
loop session-start --tool codex --command "<slash-command>"
loop session-end --tool codex
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) - not duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names.

## Required Context

Before acting, read:

1. `AGENTS.md`
2. `memories/MEMORY.md`
3. `DOUBTS.md`
4. `plan/main_plan.md`
5. `TASKS.yml`
6. `GATES.yml`
7. `HANDOFF.md`

## Rules

- Do not ask the user to paste boot prompts.
- Use `skills/` as the canonical skill source.
- Update `memories/MEMORY.md`, `DOUBTS.md`, and `HANDOFF.md` before ending.
- Synthetic data only until sensitive-data gates pass.
