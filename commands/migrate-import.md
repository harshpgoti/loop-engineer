# /migrate-import

Import memory, user profile, skills, and workspace instructions from another agent workspace into the active Loop Engineer product workspace.

## How To Interpret

If the user says `/migrate-import`, `migrate import`, or asks to import memory from another tool, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/migrate-import/SKILL.md`
3. `docs/DATA_LAYOUT.md`

## Imports

From `--source` directory when present:

- `MEMORY.md` → `memories/MEMORY.md`
- `USER.md` → `memories/USER.md`
- `SOUL.md` → `memories/SOUL.md`
- skills → `skills/imported/`
- `AGENTS.md` → `AGENTS.imported.md` (full preset only)

## Rules

- Dry-run first unless the user explicitly approves apply.
- Do not copy secrets/API keys automatically.
- Never overwrite existing product plan files (`plan/main_plan.md`, `plan/`, `TASKS.yml`, ...).
- Initialize memory layout (`memories/`, `state.db`, `skills/`) before import.

## Script

```bash
python scripts/migrate_import.py --source /path/to/source --dry-run
python scripts/migrate_import.py --source /path/to/source --workspace ../product
loop migrate import --source /path/to/source --scan   # classify arbitrary files by content
```

With `--scan`, files that don't match Loop Engineer's names are classified by
content (user profile -> `memories/USER.md`, rules -> `memories/SOUL.md`, notes ->
`memories/MEMORY.md`, how-tos -> `skills/imported/`, plans -> `plan/imported/`;
secrets are never copied). See `skills/migrate-import/SKILL.md`.

## Output

1. Source path
2. Files copied/skipped
3. Next: review `memories/` and `skills/imported/`
