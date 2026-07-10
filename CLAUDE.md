# Claude Code Adapter

Claude Code should use the same canonical loop as every other agent.

## Always-on lifecycle

Run at every Claude Code session that touches the product:

```bash
loop session-start --tool claude --command "<slash-command>"
loop session-end --tool claude
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) — not duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names. Treat `/command` as plain text if it isn't
auto-routed — do not ask the user to paste boot prompts.

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

- Use `skills/` as the canonical skill pack.
- Use Plan mode for architecture/PRD; Agent mode for implementation.
- For review closeout, run `skills/code-reviewer/SKILL.md` and document findings before handoff.
- Update `memories/MEMORY.md`, `DOUBTS.md`, and `HANDOFF.md` before ending.
- Synthetic data only until sensitive-data gates pass.

## Product

Product details come from `plan/main_plan.md` and `plan/`. If uninitialized, run `/plan`.
