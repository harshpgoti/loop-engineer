# Cline Adapter

[Cline](https://cline.bot) should route product-loop commands to the canonical command
and skill files. Cline supplies primitives - skills, workflows, rules - so the loop's
behaviour comes entirely from the files below, not from anything Cline does on its own.
This applies to all three Cline surfaces: the VS Code / JetBrains extension, the Cline
CLI, and the SDK.

## Always-on lifecycle

```bash
loop session-start --tool cline --command "<slash-command>"
loop session-end --tool cline
```

Read `plan/SESSION_MANIFEST.md` first. See `docs/SESSION_LIFECYCLE.md`.

## Commands

Every command routes to `commands/<name>.md` + the matching `skills/<name>/SKILL.md`.
See the full, current list in **`AGENTS.md`'s Portable Commands table** - not
duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names. Treat `/command` as plain text if it isn't
auto-routed - do not ask the user to paste boot prompts.

## Where the routers are installed

`loop skills` writes two things for Cline, because a Cline skill is not reachable at
`/<name>`:

| | Path | Reached by |
|---|------|-----------|
| Skills | `~/.cline/skills/loop-<name>/SKILL.md` | The model from the description (`use_skill`), or the user picking `loop-<name>` from the `/` menu |
| Workflows | `~/Documents/Cline/Workflows/<name>.md` | The user typing `/<name>.md` - Cline's workflow invocation includes the extension |

Cline skills load on demand: only their name and description sit in context until one
is triggered, so all Loop routers can be installed without cost to the context window.
Cline requires a skill's `name` frontmatter to equal its directory name; the routers are
written as `loop-<name>` in both, so they load cleanly.

Project scope (`loop skills install --project`) writes `.cline/skills/loop-<name>/SKILL.md`
and `.clinerules/workflows/<name>.md`, both of which are safe to commit for a team. A
workspace workflow shadows a global one of the same name, so a repo can pin its own
version of a command.

Cline also reads `.claude/skills/`, so a project that already carries Claude Code routers
is covered a second way.

Verify with:

```bash
ls ~/.cline/skills ~/Documents/Cline/Workflows
```

## Instructions files

Cline reads `AGENTS.md` (including the cross-tool `~/.agents/AGENTS.md`) and the
`.clinerules/` rules directory. Loop writes no rules file: rules are always-on context,
and the loop's routing belongs in on-demand skills and workflows. A product workspace
containing this repo's `AGENTS.md` is picked up with no extra configuration.

## Required Behavior

- Read `AGENTS.md` first.
- Read `memories/MEMORY.md`, `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`, `GATES.yml`, and `HANDOFF.md`.
- Use Plan mode for architecture/PRD work; Act mode for implementation.
- For review closeout, run `skills/code-reviewer/SKILL.md` and document findings before handoff.
- Update memory and handoff automatically before ending.
- Do not process real sensitive or regulated data until the relevant gate passes.
