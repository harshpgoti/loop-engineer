# Workspace Modes

See [`docs/DATA_LAYOUT.md`](DATA_LAYOUT.md) for the full layout.

## Auto-detection (default behavior)

When you run `/plan-loop`, `/loop-engine`, or another Loop skill:

1. **Local `.loop-engineer/` folder detected** in cwd or a parent → use `<that-folder>/.loop-engineer/`
2. **No local data** → use global `~/.loop-engineer/data/`

## Layout

```text
~/.loop-engineer/
├── app/              # updatable tool runtime
├── bin/loop          # internal bridge used by skills
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

Use `/setup-loop-engine` in the coding agent. Run it from the product folder for a
local `.loop-engineer/` workspace; the installer-created global workspace remains the
fallback when no local workspace is found.

## Main product with sub-products

A product split into sub-products keeps one workspace per folder, linked into a tree:

```text
main-product/
├── .loop-engineer/            THE workspace - master plan + every sub-product's plan
│   └── plan/products/auth/    one sub-product: prd, steps, features, TASKS, GATES, DOUBTS
├── services/auth/             its code (or another repo entirely - scope.json says where)
└── apps/portal/
```

Sub-products under the main folder are auto-detected. Use `/product-tree` to inspect the
tree, or tell the agent “link ../billing as map row 03” / “make this workspace standalone”
for exceptional layouts. The agent performs the internal deterministic operation.

No file means `standalone` - single-product workspaces are unaffected. Full behavior:
[`docs/SCOPES.md`](SCOPES.md).

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
