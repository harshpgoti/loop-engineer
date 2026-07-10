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
`LOOP_COMMANDS.md` for the plain list) — not duplicated here, since a second copy
drifts stale every time a command is added.

If slash commands are not supported, type the same text as a normal message. The agent should route it via `AGENTS.md`.
