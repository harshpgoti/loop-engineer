# Grok Build Adapter

Grok Build should use the repo's canonical command and skill files.

## Native skills

Grok Build reads SKILL.md skills from `~/.grok/skills/` (global) and
`.grok/skills/` (project), and surfaces user-invocable skills as `/<name>` slash
commands - `loop skills install` writes Loop's router skills there like any other
agent. Grok Build also auto-reads Claude Code skills, plugins, and `CLAUDE.md`, so
`loop team-init` reaches it through that channel too. Add it explicitly with
`loop skills install --host grok` if you want Grok-only.

## Always-on lifecycle

```bash
loop session-start --tool grok --command "<slash-command>"
loop session-end --tool grok
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Route Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) - not duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names.

## Required Read

Read:

- `AGENTS.md`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md`
- `TASKS.yml`
- `GATES.yml`
- `HANDOFF.md`

## Closeout

Update:

- `memories/MEMORY.md`
- `DOUBTS.md`
- `HANDOFF.md`
- `.ai/SESSION_LOG.md`
