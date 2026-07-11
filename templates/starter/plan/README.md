# Plan Steps

This folder contains product-specific step plans.

`plan/main_plan.md` is the product master plan. Each step file describes one product module or major phase.

## Current Steps

No product-specific steps yet.

First `/plan-loop` should create:

```text
step_01_<slug>.md
plan/features/001-<slug>/spec.md   # active feature spec (via loop feature new)
```

## Feature specs

Buildable slices live in `plan/features/NNN-slug/`. See `docs/FEATURE_WORKFLOW.md`.

## Platform scale (ultraplan)

When the product has multiple sub-products or agents:

- `plan/PLAN_SCALE.md` - `convenient` vs `platform`
- `plan/PRODUCT_MAP.md` - module index
- `plan/steps/NN-slug/` - deep ultraplan pack per step
- `plan/ULTRAPLAN_STATUS.md` - progress tracker

See `docs/ULTRAPLAN.md` and `skills/plan-loop/phases/ultraplan.md`.

Active pointer: `.loop/active-feature.json`

## Naming

Use:

```text
step_XX_short_module_name.md
```

Examples:

- `step_01_customer_support_portal.md`
- `step_02_billing_automation.md`
- `step_03_analytics_dashboard.md`
