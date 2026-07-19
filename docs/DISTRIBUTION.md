# Distributing Loop Engineer to coding agents

**Design goal:** whether the user works globally or inside a project, any coding
agent can run every Loop command **from the single installed app** — one runtime,
updated in one place, never copied.

Loop's canonical skills are not self-contained documents: they read `AGENTS.md`
and `templates/`, and run `scripts/` from the app root. Copying them into a
user's project would break those references and create per-project drift. So
Loop distributes **thin routers, never content** — one SKILL.md per command,
written into every coding agent's skills dir, each pointing back at the single
installed app. The old per-tool command-wrapper spray is opt-in legacy.

## 1. Router skills in every agent's skills dir

Loop generates one ~15-line **router skill per command**. Frontmatter carries the
command's clean `name:` and description-plus-trigger
(`Invoke when the user types /plan-loop ...`); the body points the agent at the
installed app (`AGENTS.md` → `commands/<name>.md` → `skills/<name>/SKILL.md`) and
at the active workspace. The directory is prefixed `loop-<command>` for
collision-safety; `name:` stays clean so `/plan-loop` still resolves.

**Installed into every agent at once — not just the one you picked.** Switching
agents mid-task must need no setup, so `loop skills install` writes routers to
the universal `.agents/skills` **and** each agent's own skills dir. Adding a new
agent is one row in the `HOSTS` table in `scripts/install_skills.py` — zero code.

| Agent | Global (`--user`) | Project (`--project`) |
|---|---|---|
| universal | `~/.agents/skills` | `.agents/skills` |
| Claude Code | `~/.claude/skills` | `.claude/skills` |
| Codex | `~/.codex/skills` | `.agents/skills` |
| Cursor | `~/.cursor/skills` | `.cursor/skills` |
| OpenCode | `~/.config/opencode/skills` | `.opencode/skills` |
| Gemini CLI | `~/.gemini/skills` | `.agents/skills` |
| Grok Build | `~/.grok/skills` | `.grok/skills` |
| Factory / Kiro / Slate / Hermes | `~/.<tool>/skills` | `.agents/skills` |

Grok Build also auto-reads Claude Code skills and `CLAUDE.md`, so it is covered a
second way by the `~/.claude/skills` router and team mode.

Because routers are pointers, **editing canonical commands/skills never requires
a reinstall** — only adding or renaming a command does, and `loop setup` /
`loop update` regenerate automatically (skip with `--skip-native-commands`).

```bash
loop skills install              # global: every agent's skills dir (default)
loop skills install --project    # project scope, under the current repo
loop skills install --detected-only   # only agents already present (+ universal)
loop skills install --host codex --host cursor   # limit to specific agents
loop skills installed            # show what Loop installed, per agent
loop skills uninstall            # remove only Loop-owned routers, everywhere
```

Ownership is tracked per destination in `.loop-engineer-manifest.json` plus a
`loop-engineer:generated` marker inside each router — install, update, and
uninstall never touch a directory Loop didn't create, and re-installs clean up
older full-copy installs automatically.

**Skills vs. slash commands.** In the open standard a tool loads a skill when the
conversation matches its `description`, and many tools have no `/`-autocomplete
for skills. The routers name their command triggers, so typing `/plan-loop` (or
describing the task) routes to the right command in the app. In Claude Code,
skills and slash commands are unified — a router in `~/.claude/skills/` is
directly invokable as `/plan-loop` *and* auto-activates by description, so no
separate plugin is needed.

## Auto-update at session-start

`loop session-start` runs in every agent at every session, so it is where Loop
keeps the app current — gstack's "no version drift, no manual upgrades" property,
but Loop has one app to update instead of one clone per tool. The check is
silent, throttled to once per hour, and failure-safe (any error skips and retries
next hour). Modes (`LOOP_AUTO_UPDATE` env → `~/.loop-engineer/data/auto_update.txt`
→ default `pull`):

- `pull` — fast-forward the app when its checkout is clean; refresh routers if
  commands changed. If the checkout is dirty or can't fast-forward, it leaves a
  one-line notice in `plan/SESSION_MANIFEST.md` instead of touching anything.
- `check` — only notice available updates; never modify files.
- `off` — never touch the app.

## Team mode

`loop team-init [required|optional]` commits a **path-free bootstrap** into the
product repo — a `loop-engineer` bootstrap skill (in each project skills dir) plus
a marker-guarded "Loop Engineering OS" section in `CLAUDE.md`. A teammate clones
the repo, opens any agent, and is walked through installing Loop on first session;
`required` blocks AI-assisted product work until it's installed, `optional`
nudges. No vendored tool files, no version drift — the committed artifact is an
instruction, not the runtime. Add `--commit` to stage and commit in one step.

> **Why no Claude Code plugin?** Claude Code's skills and slash commands are
> unified, so the router Loop already installs into `~/.claude/skills/` gives real
> `/plan-loop` autocomplete with no extra mechanism. A plugin would bundle a
> second, self-contained copy of the repo that Claude Code's marketplace updates
> independently of `~/.loop-engineer/app` — reintroducing the one-copy-per-tool
> drift the router model exists to avoid. So Loop ships no plugin.

## 2. Legacy: per-tool command wrappers (deprecated)

The old approach generated a thin `/command` wrapper file inside each tool's
private command directory (`~/.claude/commands/`, `~/.cursor/commands/`,
`~/.config/opencode/commands/`, `~/.codex/skills/`). It still works for tool
versions that predate SKILL.md support, but it is no longer run by default:

```bash
loop setup --legacy-commands
loop update --legacy-commands
loop commands install --tool all --scope user   # direct invocation
```

Prefer the router skills (1). The wrapper generator will be removed after a
deprecation window.

## What about MCP?

An MCP server exposing loop commands as prompts is elegant (one registration per
host) but prompt-as-slash-command support is uneven across hosts, and the skills
pack already covers discovery for >90% of tools. Revisit only if a target tool
supports MCP but not the SKILL.md standard.
