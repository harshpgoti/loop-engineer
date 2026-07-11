# Phase: Ultraplan

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: ultraplan`, or when the user types `/ultraplan-loop`.
> Deep per-step planning for **platform-scale** products (multiple sub-products / AI agents).

## Purpose

When the user's idea is **platform-scale** (multiple sub-products, agents, or major modules), each module becomes one step - but planning must go **deep**, not shallow TBD step files.

## When to use

| Scale | Harness |
|-------|---------|
| `convenient` | Standard `plan/step_XX.md` + feature spec - skip ultraplan |
| `platform` | `PRODUCT_MAP.md` + `plan/steps/NN-slug/` ultraplan pack per step |

Detect scale: automatic via `loop plan-loop "<idea>"` → `plan/PLAN_SCALE.md`.

## Read First

1. `plan/PLAN_BOOTSTRAP.md`
2. `plan/PLAN_SCALE.md`
3. `plan/PRODUCT_MAP.md`
4. `plan/ULTRAPLAN_STATUS.md`
5. Active step index `plan/step_XX_*.md`
6. Active ultraplan folder `plan/steps/NN-slug/`
7. `plan/main_plan.md`, `EVIDENCE_LOG.md`, `DOUBTS.md`

## Auto-bootstrap (default)

User says `/plan-loop <idea>` or `/loop-engine <idea>`. Agent runs `loop session-start --text "<idea>"` or `loop plan-loop "<idea>"`. Read `plan/PLAN_BOOTSTRAP.md` first.

When the user's message contains a product idea, bootstrap already ran. Verify `plan/PLAN_BOOTSTRAP.md`. If platform and modules missing from bootstrap, propose rows in `PRODUCT_MAP.md` and re-run `loop plan-loop "<idea>"`.

## Deep-plan one step (one session)

1. Run `loop plan-loop ultraplan next` - pick the next incomplete step.
2. Fill **every** file in `plan/steps/NN-slug/`:
   - `overview.md` - role in platform, metrics
   - `prd.md` - requirements, stories, NFRs
   - `architecture.md` - components, APIs, ADRs
   - `agents.md` - required for type `agent`; else N/A
   - `data-model.md`, `integrations.md`, `risks.md`, `acceptance.md`
3. Run `loop plan-loop ultraplan status` - refresh tracker.
4. Repeat until all steps complete.
5. For the **active** step only: `loop feature new` → `spec-clarify` → `spec-checklist` → `task-compiler`.

Do **not** shallow-fill all steps in one session - ultraplan one step at a time with council + evidence.

## Quality gate (per step)

Before marking a step ultraplan-complete:

- [ ] No more than 2 `TBD` tokens across the pack
- [ ] PRD has numbered requirements
- [ ] Architecture names components and boundaries
- [ ] Agents doc complete if type is `agent`
- [ ] Acceptance checklist filled
- [ ] Product council consulted for major boundaries (`council` phase)
- [ ] Evidence logged for non-obvious claims

## Output

- Updated ultraplan pack for one step
- `plan/ULTRAPLAN_STATUS.md` refreshed
- Next step id or "all complete"
- Handoff: ultraplan next step OR feature spec for completed step

## Wiring

- **`/plan-loop`:** After scale detect - branch here for platform scale
- **`/loop-engine`:** Routes here when `PLAN_SCALE.md` is platform and ultraplan incomplete

## Next phase

For the active step: create the feature spec, then `spec-clarify`.
