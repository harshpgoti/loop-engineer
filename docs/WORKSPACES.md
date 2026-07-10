# Workspace Modes

See [`docs/DATA_LAYOUT.md`](DATA_LAYOUT.md) for the full layout.

## Auto-detection (default behavior)

When you run `/plan`, `/loop-engine`, or any loop script:

1. **Local `.loop-engineer/` folder detected** in cwd or a parent → use `<that-folder>/.loop-engineer/`
2. **No local data** → use global `~/.loop-engineer/data/`

## Layout

```text
~/.loop-engineer/
├── app/              # updatable tool (loop update)
├── bin/loop
└── data/             # ALL global memory/data
    ├── memories/
    ├── state.db
    ├── skills/
    ├── plan/main_plan.md
    └── ...

H:/POC/QEAutoAI/               # example local product folder
├── ... your product code      # untouched by Loop Engineer
└── .loop-engineer/            # ALL local memory/data, hidden
    ├── memories/
    ├── state.db
    ├── plan/main_plan.md
    └── ...
```

## Setup

```bash
# Global (default)
loop setup

# Local product folder
cd H:/POC/QEAutoAI
loop setup --use-cwd --name qeautoai
```

## Switch registered local products

```bash
python scripts/workspace_registry.py list
python scripts/workspace_registry.py use qeautoai
```

## Central tool mode (manual clone)

```text
Main/
├── loop-engineer/    # or ~/.loop-engineer/app/
└── product/          # local memory with --memory-mode local -> product/.loop-engineer/
```

Never store product state inside the app runtime directory. Loop Engineer's own code (`app/`) and data (`data/` or `.loop-engineer/`) are always separate directories, never mixed.
