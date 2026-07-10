# Product Map — {{PRODUCT_NAME}}

**Updated:** {{DATE}}

One row per **sub-product**, **AI agent**, or major platform module. Each row becomes one `plan/step_XX_*.md` plus a deep ultraplan pack under `plan/steps/NN-slug/`.

| ID | Step file | Type | Title | Depends on | Ultraplan status |
|----|-----------|------|-------|------------|------------------|
| 01 | step_01 | agent | Example support agent | | outline |
| 02 | step_02 | product | Example admin portal | 01 | outline |

## Types

- `agent` — autonomous AI agent or copilot module
- `product` — user-facing sub-product or app
- `service` — backend service or API domain
- `module` — shared capability (auth, billing, etc.)

## Rules

- Keep **one wedge per step** — do not merge unrelated sub-products.
- Link dependencies in **Depends on** (step IDs).
- Do not duplicate full PRD text here — details go in `plan/steps/NN-slug/`.
