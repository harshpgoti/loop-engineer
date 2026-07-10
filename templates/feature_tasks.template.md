# Tasks: {{FEATURE_TITLE}}

**Feature:** {{FEATURE_ID}}  
**Updated:** {{DATE}}

Human-readable task list for this feature. `skills/task-compiler/SKILL.md` syncs ids into `TASKS.yml`.

## Format

```text
- [ ] TASK-NNN Title [P] files: path/to/file
- [x] TASK-NNN Done item
```

- `[P]` = safe to run in parallel with other `[P]` tasks in this feature.
- `files:` = primary paths touched (optional but recommended).

## Setup

- [ ] TASK-001 Scaffold feature module files: src/...

## Core

- [ ] TASK-002 Implement primary flow [P] files: src/...

## Tests

- [ ] TASK-003 Add tests files: tests/...

## Docs

- [ ] TASK-004 Update docs files: docs/...
