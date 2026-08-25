# Pi Adapter

[Pi](https://pi.dev) should route product-loop commands to the canonical command and
skill files. Pi is a minimal harness - it supplies primitives, so the loop's behaviour
comes entirely from the files below, not from anything Pi does on its own.

## Always-on lifecycle

```bash
loop session-start --tool pi --command "<slash-command>"
loop session-end --tool pi
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) - not duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names.

## Where the routers are installed

`loop skills` writes two things for Pi, because a Pi skill is not reachable at
`/<name>`:

| | Path | Reached by |
|---|------|-----------|
| Skills | `~/.pi/agent/skills/loop-<name>/SKILL.md` | The model from the description, or the user typing `/skill:loop-<name>` |
| Prompt templates | `~/.pi/agent/prompts/<name>.md` | The user typing `/<name>` |

Pi reserves `/skill:` for skills; its plain `/` namespace is prompt templates. Installing
only skills leaves `/plan-loop` matching nothing, which is exactly what a Pi user sees
before this row exists.

Pi also scans `~/.agents/skills` globally and `.agents/skills` in the cwd and its
ancestors, so a project-scope install (`loop skills install --project`) reaches Pi through
the universal directory - no `.pi/skills` copy, which Pi would list a second time.

**Project scope needs trust.** Pi reads `.agents/skills`, `.pi/skills`, and `.pi/prompts`
only after the project is trusted (`~/.pi/agent/trust.json`). Trust the folder in Pi once;
a global install needs none of this.

Verify with `/help` in Pi, or:

```bash
ls ~/.pi/agent/skills ~/.pi/agent/prompts
```

## Instructions files

Pi loads `AGENTS.md` from `~/.pi/agent/`, the cwd, and its ancestors - so a product
workspace containing this repo's `AGENTS.md` is picked up with no extra configuration.
`SYSTEM.md` can override the system prompt per project; Loop does not write one, and a
project that adds one must keep `AGENTS.md` routing intact.

## Required Behavior

- Read `AGENTS.md` first.
- Read `memories/MEMORY.md`, `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`, `GATES.yml`, and `HANDOFF.md`.
- Update memory and handoff automatically.
- Do not process real sensitive or regulated data until the relevant gate passes.
