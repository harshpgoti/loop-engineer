# Upgrade Guide

Use `/upgrade-loop-engineer` to update the reusable tool without losing product data.

## Best Setup: Separate Tool And Product Folders

```text
Main/
├── loop-engineer/
└── product/
```

Update the tool only:

```bash
cd loop-engineer
git pull
python scripts/validate_template.py
```

Product data remains in `product/.loop-engineer/` (a hidden nested folder — see `docs/DATA_LAYOUT.md`).

In this setup, product state is never stored in `loop-engineer/`. Files like `plan/main_plan.md`, `memories/MEMORY.md`, `TASKS.yml`, and `HANDOFF.md` live in `product/.loop-engineer/`. Updating `loop-engineer/` cannot overwrite them.

Useful commands from `loop-engineer/`:

```bash
python scripts/workspace_registry.py current
python scripts/compact_context.py
python scripts/validate_outputs.py --workspace <your-product-workspace>
python scripts/detect_workspace.py
python scripts/migrate_workspace.py --workspace ../product
python scripts/doctor.py --workspace ../product
```

## Embedded Setup: Tool Files Copied Into Product

If you copied Loop Engineering OS files into a product repo, use the upgrade script.

First compact and back up:

```text
/compact-loop
```

Then run dry-run:

```bash
python path/to/new-loop-engineer/scripts/upgrade_loop_engineer.py --source path/to/new-loop-engineer --target path/to/product
```

If the output looks safe:

```bash
python path/to/new-loop-engineer/scripts/upgrade_loop_engineer.py --source path/to/new-loop-engineer --target path/to/product --apply
```

## Protected Product-State Files

The upgrade script never copies over:

```text
plan/main_plan.md
plan/
memories/ (MEMORY.md, USER.md, SOUL.md)
DOUBTS.md
TASKS.yml
GATES.yml
HANDOFF.md
CURRENT_STATE.md
DECISIONS.md
EVIDENCE_LOG.md
COMPACT.md
DEPLOYMENT_PLAN.md
memories/
skills/
state.db
.ai/
docs/
```

## What Gets Updated

Reusable tool files:

```text
commands/
skills/
scripts/
templates/
tools/
evals/
adapters and root tool docs
```

## After Upgrade

Run:

```bash
python scripts/validate_outputs.py --workspace <your-product-workspace>
```

Then continue:

```text
/loop-engine
```
