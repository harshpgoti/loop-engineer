# OpenCode Adapter

OpenCode should route product-loop commands to the canonical command and skill files.

## Always-on lifecycle

```bash
loop session-start --tool opencode --command "<slash-command>"
loop session-end --tool opencode
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) — not duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names.

## Required Behavior

- Read `AGENTS.md` first.
- Read `memories/MEMORY.md`, `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`, `GATES.yml`, and `HANDOFF.md`.
- Update memory and handoff automatically.
- Do not process real sensitive or regulated data until the relevant gate passes.
