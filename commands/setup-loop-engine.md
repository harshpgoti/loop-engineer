# /setup-loop-engine

First-time setup for Loop Engineering OS.

## Purpose

Register where product memory lives and seed missing starter files.

## Memory modes

| Mode | Location | Setup |
|------|----------|--------|
| **Global** (default) | `~/.loop-engineer/data/` | `loop setup` — no extra flags |
| **Local** | `<product-folder>/.loop-engineer/` | `loop setup --use-cwd` or `loop setup --memory-mode local --workspace H:/POC/QEAutoAI` |

**Auto-detection:** After local setup, when you return to that folder and run `/plan` or `/loop-engine`, loop data is detected automatically. No need to pass flags again.

## Ask the user

> Where should product memory live?
>
> 1. **Local** — in your product folder (multiple products, separate memory each)
> 2. **Global** — in `~/.loop-engineer/data/` (default)

## Scripts

Global (default):

```bash
loop setup
python scripts/setup_loop_engine.py
```

Local in current folder:

```bash
cd H:/POC/QEAutoAI
loop setup --use-cwd --name qeautoai
```

Local with explicit path:

```bash
loop setup --memory-mode local --workspace H:/POC/QEAutoAI --name qeautoai
```

Interactive:

```bash
loop setup --interactive
```

Import memory/data from another tool in the same step:

```bash
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --dry-run
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --overwrite
loop setup --use-cwd --name qeautoai --source /path/to/other-tool/export --scan
```

`--scan` additionally classifies files that don't match Loop Engineer's names by
content and routes them (profile/rules/notes -> `memories/`, how-tos ->
`skills/imported/`, plans -> `plan/imported/`; secrets never copied).

Imports `MEMORY.md`, `USER.md`, `SOUL.md`, and `skills/` from `--source`. On a fresh
workspace the import supersedes Loop Engineer's own starter placeholders automatically;
on an existing workspace, real content is protected unless `--overwrite` is passed.

## Output

1. Workspace path and memory mode
2. Files created / skipped
3. Next command: `/plan`

See `docs/DATA_LAYOUT.md`.
