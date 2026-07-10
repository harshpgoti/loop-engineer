---
name: setup-loop-engine
description: First-time setup with global (~/.loop-engineer/data/) or local (<product-folder>/.loop-engineer/) memory. Local data dirs are auto-detected on return. Use when the user types /setup-loop-engine.
---

# Setup Loop Engine

## Memory modes

| Mode | Path | Command |
|------|------|---------|
| Global (default) | `~/.loop-engineer/data/` | `loop setup` |
| Local | `<product-folder>/.loop-engineer/` | `loop setup --use-cwd` |

## Auto-detection

After local setup, `/plan-loop` and `/loop-engine` auto-use the product folder when loop data exists there.

## Commands

```bash
loop setup
loop setup --use-cwd --name qeautoai
loop setup --memory-mode local --workspace H:/POC/QEAutoAI --name qeautoai
loop setup --interactive
```

## Importing memory/data from another tool during setup

Pass `--source <path>` to import an external tool's `memories/MEMORY.md`, `memories/USER.md`, `memories/SOUL.md`,
and `skills/` in the same step — no separate `/migrate-import` call needed:

```bash
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --dry-run
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --scan
```

`--scan` handles tools with a **different file structure**: dump everything in one
folder and each file is classified by content and routed to the right home
(profile -> `memories/USER.md`, rules -> `memories/SOUL.md`, notes ->
`memories/MEMORY.md`, how-tos -> `skills/imported/`, plans -> `plan/imported/`;
secrets never copied). See `skills/migrate-import/SKILL.md` for the full table.

- Fresh workspace: the imported files supersede Loop Engineer's own starter
  placeholders automatically (there is nothing real to protect yet).
- Existing workspace: real content is protected — pass `--overwrite` to replace it.
- To import later instead, use `skills/migrate-import/SKILL.md` (`/migrate-import`)
  standalone — same underlying `run_import()`, same `--overwrite` semantics.

See `docs/DATA_LAYOUT.md`.
