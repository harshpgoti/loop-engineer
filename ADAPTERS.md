# Tool Adapters

This repo is designed to work across Cursor, Claude Code, Codex, OpenCode, Grok Build, and any other coding agent without duplicating logic.

## Source of Truth

- Commands: `commands/`
- Skills: `skills/`
- Product plan: `plan/main_plan.md`
- Step plans: `plan/`
- Memory: `memories/MEMORY.md`
- Doubts: `DOUBTS.md`

## Adapter Strategy

| Tool | Adapter | How it connects |
|------|---------|-----------------|
| Cursor | `CURSOR.md`, `AGENTS.md` | Reads universal instructions and skill map |
| Claude Code | `CLAUDE.md`, `AGENTS.md` | Reads universal instructions and skill map |
| Codex | `AGENTS.md`, `CODEX.md` | Reads universal instructions and skill map |
| OpenCode | `AGENTS.md`, `OPENCODE.md` | Reads universal instructions and skill map |
| Grok Build | `GROK.md` | Reads command + skill map |
| Any other agent | `AGENTS.md` | Portable interpretation of commands |

## Use

In any agent, type any command from **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md` for the plain list) - not duplicated here, since a second copy
drifts stale every time a command is added.

If slash commands are not supported, type the same text as a normal message. The agent should route it via `AGENTS.md`.

## Distributing to coding agents

Design goal: from any tool, global or project level, every command runs **from
the single installed app** — no copies, one runtime to update. Loop distributes
**thin routers**, not content, through two channels. Full detail:
`docs/DISTRIBUTION.md`.

**1. Router skills in every agent's skills dir** (universal `.agents/skills` plus
`~/.claude/skills`, `~/.codex/skills`, `~/.cursor/skills`, OpenCode, Gemini, Grok,
Factory, Kiro, ...). One generated ~15-line router SKILL.md per command, pointing
the agent at the installed app. Installed to **all** agents at once so switching
mid-task needs no setup. Canonical command/skill edits need no reinstall.
`loop setup` / `loop update` run this automatically.

```bash
loop skills install            # global: every agent (default)
loop skills install --project  # project scope, under the current repo
loop skills install --detected-only   # only agents already present
loop skills installed          # show what Loop installed, per agent
loop skills uninstall          # remove only Loop-owned routers, everywhere
```

Loop tracks ownership per destination (`.loop-engineer-manifest.json` + a marker
in each router) and never overwrites a directory it didn't create. Adding a new
agent is one row in the `HOSTS` table in `scripts/install_skills.py`.

**Claude Code** needs no plugin: its skills and slash commands are unified, so the
router Loop installs into `~/.claude/skills` is directly invokable as `/plan-loop`
and auto-activates by description.

**Auto-update + team mode.** `loop session-start` silently fast-forwards the app
once/hour (`LOOP_AUTO_UPDATE=pull|check|off`). `loop team-init [required|optional]`
commits a path-free bootstrap so teammates auto-get Loop on first session. Detail:
`docs/DISTRIBUTION.md`.

**3. Legacy per-tool wrappers (deprecated).** The old `loop commands install`
generated a thin `/command` file inside each tool's private command dir. Still
works for tool versions predating SKILL.md support, but no longer run by default -
opt in with `loop setup --legacy-commands` / `loop update --legacy-commands`. Will
be removed after a deprecation window.

Portable interpretation still works everywhere: type any command from **`AGENTS.md`'s
Portable Commands table** and the agent routes it via `commands/<name>.md`, even
without native autocomplete.
