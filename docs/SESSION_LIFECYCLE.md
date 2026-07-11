# Always-on Session Lifecycle

Cross-tool persistent memory that works in **any agent tool**, not only Cursor.

## Principle

Memory lives in the **product workspace** (`~/.loop-engineer/data/` or `<product-folder>/.loop-engineer/`), not in chat history. Every tool reads and writes the same files.

## Two commands (agents run these - not users)

| Phase | CLI | Slash |
|-------|-----|-------|
| Start | `loop session-start` | `/session-start` |
| End | `loop session-end` | `/session-end` |

## Session start

```bash
loop session-start --command /product-develop --tool cursor
```

Produces:

| File | Purpose |
|------|---------|
| `plan/SESSION_MANIFEST.md` | **Read first** - ordered bootstrap list |
| `plan/SESSION_RECALL.md` | Past decisions from `state.db` |
| `plan/AUTO_SKILLS.md` | Frontend motion skills (if applicable) |
| `.loop/session.json` | Session metadata |

## Session end

```bash
loop session-end --summary "Completed TASK-005; next: deploy staging"
```

Produces:

| File | Purpose |
|------|---------|
| `plan/MEMORY_REVIEW.md` | Curator report, usage vs limits |
| `plan/SESSION_CLOSEOUT.md` | Pending writes, next steps |
| `.loop/pending/memory/*.json` | Staged memory updates (default) |

Approve memory:

```bash
loop pending list
loop pending approve --all
```

## Tool integration

| Tool | How |
|------|-----|
| **Any LLM + filesystem** | Agent runs `loop session-start` / `loop session-end` per `AGENTS.md` |
| **Cursor** | Same CLI; optional: Cursor hook on session start (see below) |
| **Claude Code** | Read `CLAUDE.md`; commands route to `commands/session-start.md` + `session-end.md` |
| **Codex / OpenCode / Grok** | Read `CODEX.md`, `OPENCODE.md`, `GROK.md` |
| **Direct API** | `API_USAGE.md` - call lifecycle scripts between API turns |

### Optional Cursor hook (local)

Add to `.cursor/hooks.json` in your product repo (not required - agents can run CLI manually):

```json
{
  "version": 1,
  "hooks": {
    "sessionStart": [{ "command": "loop session-start --tool cursor" }],
    "stop": [{ "command": "loop session-end --tool cursor" }]
  }
}
```

Adjust paths if `loop` is not on PATH (use full path to `~/.loop-engineer/bin/loop`).

## When to run

| Situation | Start | End |
|-----------|-------|-----|
| `/plan-loop`, `/product-develop`, `/loop-engine` | Yes | Yes |
| Switching Cursor → Claude Code mid-product | Yes (refreshes manifest) | End previous tool first |
| Quick question in product repo | Start if touching plan/code | End if you changed state files |

## Bootstrap read order

After `session-start`, read files in order from `plan/SESSION_MANIFEST.md`:

```text
SESSION_MANIFEST → SOUL → USER → MEMORY → CONTEXT → … → SESSION_RECALL
```

Verify: `loop bootstrap`

## Related

- `docs/DATA_LAYOUT.md` - where memory files live
- `skills/session-lifecycle/SKILL.md`
- `skills/memory-review/SKILL.md`
