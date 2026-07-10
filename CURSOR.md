# Cursor Adapter

Cursor should use the same canonical loop as every other agent.

## Always-on lifecycle (every Cursor session)

Before any loop command:

```bash
loop session-start --tool cursor --command "<slash-command>"
```

Read `plan/SESSION_MANIFEST.md` first. Before ending:

```bash
loop session-end --tool cursor
```

Optional Cursor hooks: `docs/SESSION_LIFECYCLE.md`

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) — not duplicated here, since a second copy drifts stale every
time a command is added. If Cursor doesn't route `/command` automatically, read
`AGENTS.md`, find the row for what the user typed, and open the two files it names.

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

- Use this root adapter file plus the canonical `skills/` folder.
- Use `skills/` as the canonical skill pack.
- Treat slash commands as plain text commands if Cursor does not route them automatically.
- Update `memories/MEMORY.md`, `DOUBTS.md`, and `HANDOFF.md` before ending.
- Synthetic data only until sensitive-data gates pass.

## Recurring Work

For Cursor loop mode:

```text
/loop 2h /loop-engine
```

The loop still routes through `commands/` and `skills/`.
