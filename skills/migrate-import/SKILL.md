---
name: migrate-import
description: Imports memory and skills from an external agent workspace into the active Loop Engineer product workspace. Use when the user types /migrate-import.
---

# Migrate Import

## Purpose

Copy durable memory and skills from another tool's workspace folder into Loop Engineer paths.

## Command

`/migrate-import`

## Script

```bash
python scripts/migrate_import.py --source /path/to/source --dry-run
python scripts/migrate_import.py --source /path/to/source
loop migrate import --source /path/to/source --scan          # + classify arbitrary files
```

## Scan mode (`--scan`) - different tool, different file structure

When the source tool's files don't use Loop Engineer's names, add `--scan`: every
file in the folder is classified deterministically (filename + content signals -
rules first, no LLM call) and routed:

| Detected as | Goes to |
|-------------|---------|
| user profile / preferences | appended to `memories/USER.md` |
| behavior rules / persona / prompts | appended to `memories/SOUL.md` |
| project memory / notes / logs | appended to `memories/MEMORY.md` |
| how-tos / runbooks / procedures | `skills/imported/<slug>.md` (frontmatter added) |
| plans / roadmaps / PRDs / specs | `plan/imported/` - absorb via `/plan-loop` next session |
| secrets / API keys | **never copied** - warned; re-enter via `loop manage-model set-key` |
| binary / unclassifiable | skipped / staged in `.loop/import-review/` for manual review |

Appends carry an `Imported from <path>` marker, so re-running is idempotent.
Dry-run first: `loop migrate import --source <path> --scan --dry-run`.

## Rules

- Require explicit `--source` path.
- Dry-run first unless user approves apply.
- Do not copy secrets automatically.
- Never overwrite core product plan files without user approval.

## One-shot alternative

To import during first-time setup instead of as a separate step, pass `--source` to
`/setup-loop-engine` directly (`loop setup --use-cwd --source /path/to/other-tool`) -
same underlying `scripts/migrate_import.run_import()`, same `--overwrite` semantics.
