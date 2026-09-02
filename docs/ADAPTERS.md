# Tool Adapters

This repo is designed to work across any coding agent that can read Markdown files and run shell commands. The chain exposes itself as a portable set of commands and skills; the agent reads the canonical files and routes to them.

## Source of Truth

- Commands: `commands/`
- Skills: `skills/`
- Product plan: `plan/main_plan.md`
- Step plans: `plan/`
- Memory: `memories/MEMORY.md`
- Doubts: `DOUBTS.md`

## Adapter Strategy

| Tool | Adapter | How it connects |
|---|---|---|
| <adapter> | `CURSOR.md`, `AGENTS.md` | Reads universal instructions and skill map |
| <adapter> | `CLAUDE.md`, `AGENTS.md` | Reads universal instructions and skill map |
| <adapter> | `AGENTS.md`, `CODEX.md` | Reads universal instructions and skill map |
| <adapter> | `AGENTS.md`, `OPENCODE.md` | Reads universal instructions and skill map |
| <adapter> | `GROK.md` | Reads command + skill map |
| <adapter> | `PI.md`, `AGENTS.md` | Reads universal instructions and skill map |
| <adapter> | `CLINE.md`, `AGENTS.md` | Reads universal instructions and skill map |
| Any other agent | `AGENTS.md` | Portable interpretation of commands |
## Use

In any agent, type any command from **`AGENTS.md`'s Portable Commands table** - not
duplicated here, since a second copy
drifts stale every time a command is added.

If slash commands are not supported, type the same text as a normal message. The agent should route it via `AGENTS.md`.

## Distributing to coding agents

Design goal: from any tool, global or project level, every command runs **from
the single installed app** — no copies, one runtime to update. Loop distributes
**thin routers**, not content, through two channels. Full detail:
`docs/DISTRIBUTION.md`.

**1. Router skills in every agent's skills dir** (the chain writes a ~15-line
router SKILL.md per command into whatever skills directory the agent reads).
The router points the agent at the installed app. Installed to **all** agents
at once so switching mid-task needs no setup. Canonical command/skill edits
need no reinstall. `loop setup` / `loop update` run this automatically.

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

**<adapter>** needs no plugin: its skills and slash commands are unified, so the
router Loop installs into `~/.claude/skills` is directly invokable as `/plan-loop`
and auto-activates by description.

**Auto-update + team mode.** `loop session-start` silently fast-forwards the app
once/hour (`LOOP_AUTO_UPDATE=pull|check|off`). `loop team-init [required|optional]`
commits a path-free bootstrap so teammates auto-get Loop on first session. Detail:
`docs/DISTRIBUTION.md`.

**3. Legacy per-tool wrappers (removed in v3).** Loop <= v2 generated a thin
`/command` file inside each tool's private command dir. Every supported tool reads
SKILL.md now, so the generator, `loop commands install`, and the
`--legacy-commands` flags are gone. `loop skills install` prunes leftover wrappers,
which otherwise listed every command twice in <adapter>.

Portable interpretation still works everywhere: type any command from **`AGENTS.md`'s
Portable Commands table** and the agent routes it via `commands/<name>.md`, even
without native autocomplete.
