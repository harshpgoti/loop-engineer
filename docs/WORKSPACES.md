# Workspace Modes

See [`docs/DATA_LAYOUT.md`](DATA_LAYOUT.md) for the full layout.

## Auto-detection (default behavior)

When you run `/plan-loop`, `/loop-engine`, or any loop script:

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

## Main product with sub-products

A product split into sub-products keeps one workspace per folder, linked into a tree:

```text
main-product/
├── .loop-engineer/        role: main  - master plan + plan/SUBPRODUCTS.md
├── auth-svc/.loop-engineer/   role: sub  - own plan + plan/PARENT_CONTEXT.md
└── portal/.loop-engineer/     role: sub
```

Sub-products under the main folder are auto-detected; ones elsewhere are linked:

```bash
loop workspace tree
loop workspace link ../billing --map-id 03
loop workspace role standalone     # opt a folder out
```

No file means `standalone` - single-product workspaces are unaffected. Full behavior:
[`docs/PRODUCT_HIERARCHY.md`](PRODUCT_HIERARCHY.md).

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
