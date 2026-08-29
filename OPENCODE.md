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
See the full, current list in **`AGENTS.md`'s Portable Commands table** - not
duplicated here, since a second copy drifts stale every
time a command is added. Read `AGENTS.md`, find the row for what the user typed,
and open the two files it names.

## Where the routers are installed

`loop skills` writes two things for OpenCode, because it keeps them in separate
namespaces:

| | Path | Reached by |
|---|------|-----------|
| Skills | `~/.config/opencode/skills/loop-<name>/SKILL.md` | The model, from the description |
| Slash commands | `~/.config/opencode/command/<name>.md` | The user typing `/<name>` |

Installing only the skills leaves `opencode debug skill` listing every router while
`/plan-loop` matches nothing. Verify both with:

```bash
opencode debug skill      # the routers the model can reach
opencode debug config     # the `command` block - what `/` completes
```

OpenCode also auto-loads `~/.claude/skills/` and `~/.agents/skills/`, and dedupes by
skill `name`. A router whose `name` disagrees with its folder stops those copies
collapsing, so every install writes `name: loop-<command>` to match the folder.

`loop skills` also grants read access to the app root in
`~/.config/opencode/opencode.json[c]`:

```json
"permission": { "external_directory": { "*": "ask", "~/.loop-engineer/**": "allow" } }
```

Without it OpenCode asks for external-directory access on the first loop command in
every new product folder, and the answer is always yes - a prompt that teaches people to
click through prompts. Order matters: OpenCode applies the **last** matching rule, so the
broad `ask` is written first. An existing value is never overwritten, and a config that is
not plain JSON is left alone with the snippet printed instead, because OpenCode refuses to
start on invalid config.

Config is read once at startup - restart OpenCode after installing.

## Required Behavior

- Read `AGENTS.md` first.
- Read `memories/MEMORY.md`, `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`, `GATES.yml`, and `HANDOFF.md`.
- Update memory and handoff automatically.
- Do not process real sensitive or regulated data until the relevant gate passes.
