# Tool Adapters

This repo is designed to work across Cursor, Claude Code, Codex, OpenCode, Grok Build, and direct LLM API usage without duplicating logic.

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
| Direct API | `API_USAGE.md` | Use command files as system/developer prompts |

## Use

In any agent, type any command from **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md` for the plain list) - not duplicated here, since a second copy
drifts stale every time a command is added.

If slash commands are not supported, type the same text as a normal message. The agent should route it via `AGENTS.md`.

## Native slash commands (autocomplete)

By default the commands are *portable* - an agent reads `commands/<name>.md` and runs
it. Most agent CLIs only autocomplete **native** slash commands they discover in a
per-tool directory, so `/plan-loop` won't appear in the `/` menu until you install
thin native wrappers:

```bash
loop commands install                       # all supported tools, user scope
loop commands install --tool claude         # one tool
loop commands install --scope project       # <workspace>/.<tool>/commands/ instead
loop commands install --dry-run             # preview
```

This regenerates from `commands/*.md` (single source of truth) - re-run whenever
commands are added or renamed. Each wrapper carries a `loop-engineer:generated`
marker; hand-written command files are never overwritten without `--force`.

| Tool | Native wrapper location (user scope) | Invoke |
|------|---------------------------------------|--------|
| Claude Code | `~/.claude/commands/<name>.md` | `/<name>` |
| Cursor | `~/.cursor/commands/<name>.md` | `/<name>` |
| Codex | `~/.codex/skills/<name>/SKILL.md` | `$<name>` (or implicit, matched from your prompt) |
| OpenCode | `~/.config/opencode/commands/<name>.md` | `/<name>` |
| Grok Build | *(no file-based command mechanism)* | type as text; routes via `GROK.md` + `AGENTS.md` |

**Codex note:** file-based custom *prompts* (`~/.codex/prompts/*.md`, invoked as
`/prompts:<name>`) were removed upstream in codex-cli >= 0.117.0 - Codex reserves
`/` for built-in session commands. `loop commands install` writes Codex wrappers
as *Skills* instead (the current mechanism) and automatically deletes any
previously generated `~/.codex/prompts/*.md` files. If you already have stale
files there from an older Loop Engineer version, re-run `loop commands install`
(or `loop update`) to clean them up.
