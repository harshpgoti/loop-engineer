# Workspace Migrations

Loop Engineering OS evolves over time. Product workspaces may need new state files without losing existing product data.

## How It Works

- Each product workspace stores its migration version in `.loop-workspace-version`.
- Migration modules live in `migrations/`.
- `scripts/migrate_workspace.py` applies only pending migrations.

## Commands

List migrations:

```bash
python scripts/migrate_workspace.py --list
```

Dry run:

```bash
python scripts/migrate_workspace.py --workspace ../product --dry-run
```

Apply:

```bash
python scripts/migrate_workspace.py --workspace ../product
```

## Current Migration

| ID | Name | Purpose |
|----|------|---------|
| 008 | `organize_memory_layout` | Cumulatively seed current state and organize legacy memory/plan files |

Migration 008 contains the idempotent effects of the former migrations 001-007. A
workspace recorded at any earlier version therefore upgrades directly to version 8.

## Unified CLI

Prefer the unified CLI when available:

```bash
loop doctor
loop recall
loop memory review
loop migrate workspace
```

## When To Run

- After `/upgrade-loop-engineer`
- After pulling a newer `loop-engineer/` runtime
- During `/setup-loop-engine` if an older workspace is being reattached

Migrations are idempotent: existing files are never overwritten.
