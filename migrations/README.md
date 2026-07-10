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

## Current Migrations

| ID | Name | Purpose |
|----|------|---------|
| 001 | `add_compact` | Seed missing `COMPACT.md` |
| 002 | `add_prod_gap` | Seed missing `plan/PROD-GAP.md` scaffold |
| 003 | `add_release_check` | Seed missing `RELEASE_CHECK.md` scaffold |
| 004 | `add_status_doctor_sync` | Seed missing status/doctor/sync scaffolds and version file |
| 005 | `add_deployment_plan` | Seed missing `DEPLOYMENT_PLAN.md` scaffold |
| 006 | `memory_layout` | Create `memories/`, `memories/USER.md`, `state.db`, user `skills/` |
| 007 | `session_bootstrap` | Seed `memories/SOUL.md`, `CONTEXT.md`, recall/review scaffolds, pending dirs |
| 008 | `organize_memory_layout` | Move root `main_plan.md` -> `plan/main_plan.md`, root `MEMORY.md`/`STARTUP_MEMORY.md` -> `memories/` |

## Unified CLI

Prefer the unified CLI when available:

```bash
loop doctor
loop recall
loop memory review --stage
loop migrate workspace
```

## When To Run

- After `/upgrade-loop-engineer`
- After pulling a newer `loop-engineer/` runtime
- During `/setup-loop-engine` if an older workspace is being reattached

Migrations are idempotent: existing files are never overwritten.
