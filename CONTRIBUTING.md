# Contributing

Thanks for improving Loop Engineering OS.

## Rules

- Keep `skills/` and `commands/` product-neutral.
- Do not commit a user's product data to the template repo.
- Keep `plan/main_plan.md` uninitialized in the template.
- Do not commit `plan/step_*.md` files to the template.
- Add reusable behavior to `skills/`, not tool-specific adapter files.
- Keep adapter files thin (`CURSOR.md`, `CLAUDE.md`, `CODEX.md`, `OPENCODE.md`, `GROK.md`).

## Validate

Before publishing:

```bash
python scripts/validate_template.py
```

## Skill Guidelines

Every skill must have:

- YAML frontmatter
- `name`
- `description`
- clear read/update rules
- no product-specific content

## Product-Specific Data

Product-specific data belongs only in a user's initialized repo:

- `plan/main_plan.md`
- `plan/`
- `memories/MEMORY.md`
- `DOUBTS.md`
- `TASKS.yml`
- `GATES.yml`
- `DECISIONS.md`
- `EVIDENCE_LOG.md`
- `HANDOFF.md`
