# Feature Workflow

Built-in spec-driven development for one feature at a time. This is Loop Engineer's own workflow - not a vendored external CLI.

## When to use

- **`/plan-loop`:** After a step plan exists, create the active feature spec.
- **`/product-develop`:** Implement from active feature `tasks.md`.
- **Closeout:** Drift check via `/feature-converge` (auto on `loop session-end` for product-develop).

## Layout

```text
plan/features/001-auth-login/
  spec.md              # requirements, scope, acceptance
  clarifications.md    # answered open questions
  spec-checklist.md    # quality gate
  feature-plan.md      # technical plan (not product strategy)
  tasks.md             # human task list with [P] and files:
  research.md          # spikes and evidence
  converge-report.md   # drift report (script-generated)
  contracts/           # API/event contracts
.loop/active-feature.json
```

## Commands

| Command | Script |
|---------|--------|
| `/feature-new` | `loop feature new "<title>" --step plan/step_XX.md` |
| `/spec-clarify` | agent skill - updates `clarifications.md` |
| `/spec-checklist` | agent skill - validates spec before feature-plan |
| `/feature-converge` | `loop feature converge` |

## Flow

```text
/plan-loop → step plan → /feature-new → spec.md
     → /spec-clarify → /spec-checklist → feature-plan.md
     → task-compiler → tasks.md + TASKS.yml
/product-develop → implement tasks → /feature-converge → session-end
```

## No duplication

| File | Role |
|------|------|
| `plan/main_plan.md` | Product strategy |
| `plan/step_XX.md` | Module/phase plan |
| `spec.md` | One buildable feature slice |
| `tasks.md` | Human-readable tasks for the feature |
| `TASKS.yml` | Machine sync - same task ids as `tasks.md` |

Do not copy entire step plans into `spec.md`. Link and summarize.

## Session wiring

- `loop session-start` includes active feature files in `plan/SESSION_MANIFEST.md`.
- `frontend_skill_router.py` reads active feature spec for auto-skills.
- `loop session-end` runs feature converge when command is `/product-develop`.

## Principles

Product engineering principles live in `memories/SOUL.md` (constitution-style). Feature specs must align with SOUL boundaries.
