# Product Map - {{PRODUCT_NAME}}

**Updated:** {{DATE}}

One row per **sub-product**, **AI agent**, or major platform module. Each row becomes one `plan/step_XX_*.md` plus a deep ultraplan pack under `plan/steps/NN-slug/`.

| ID | Step file | Type | Title | Depends on | Ultraplan status |
|----|-----------|------|-------|------------|------------------|
| 01 | step_01 | agent | Example support agent | | outline |
| 02 | step_02 | product | Example admin portal | 01 | outline |

## Types

- `sub-product` - **delegated**: gets its own `.loop-engineer/` workspace, plan, tasks and gates
- `agent` - autonomous AI agent or copilot module
- `product` - user-facing sub-product or app
- `service` - backend service or API domain
- `module` - shared capability (auth, billing, etc.)
- `program` - company workstream (pricing, partners, legal) - not a product at all

Only `sub-product` rows are expected to have their own workspace. Every other type is
planned here, in `plan/steps/NN-slug/`, and built in this workspace - that is the normal
case, and it is why an unbuilt `module` row is not a warning.

## Columns

| Column | Required | Meaning |
|--------|----------|---------|
| ID | yes | Row identity. **Never renumber** - it is what binds plans, steps and workspaces |
| Type | yes | See above. `sub-product` is the only delegating type |
| Title | yes | Binds a `sub-product` row to a folder of the same name |
| Depends on | no | Other row IDs |
| Workspace | no | Folder name, when it differs from Title - the explicit binding |

Columns are read **by name**, so extra columns of your own are safe to add.

## Rules

- Keep **one wedge per step** - do not merge unrelated sub-products.
- Link dependencies in **Depends on** (step IDs).
- Do not duplicate full PRD text here - details go in `plan/steps/NN-slug/`.
- Renaming a `sub-product` row's Title breaks its binding unless a `Workspace` column
  pins it. Check with `loop workspace tree`.
