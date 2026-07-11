---
name: feature-workflow
description: Routes feature spec folders under plan/features - create, clarify, checklist, compile tasks, develop, converge. Wired into /plan-loop and /product-develop.
---

# Feature Workflow

## Purpose

Build one feature at a time with a durable spec folder. This is Loop Engineer's built-in spec-driven path - not a vendored external tool.

## Layout

```text
plan/features/001-slug/
  spec.md
  clarifications.md
  feature-plan.md
  tasks.md
  research.md
  spec-checklist.md
  converge-report.md
  contracts/
.loop/active-feature.json   # pointer to active feature
```

## Commands

| Command | When |
|---------|------|
| `/feature-new` | New buildable feature during `/plan-loop` |
| `/spec-clarify` | Resolve open questions before feature-plan |
| `/spec-checklist` | Quality gate before task compile |
| `/feature-converge` | After dev slices - drift vs spec/tasks |

## Scripts

```bash
loop feature new "auth login" --step plan/step_01_auth.md
loop feature list
loop feature converge
```

## Wiring (required)

- **`/plan-loop`:** After step plan, run `loop feature new` (or update active feature `spec.md`).
- **`task-compiler`:** Write `tasks.md` in active feature; sync ids to `TASKS.yml`.
- **`/product-develop`:** Read active feature `tasks.md` and `feature-plan.md`.
- **`session-start`:** Manifest includes active feature artifacts.
- **`session-end`:** Run `loop feature converge` when implementation changed.

## Read First

1. `.loop/active-feature.json`
2. Active feature `spec.md`
3. `plan/main_plan.md` and related `plan/step_*.md`

## Output

- Numbered feature folder
- Active feature pointer
- No duplicate task sources - `tasks.md` is human view; `TASKS.yml` is machine sync
