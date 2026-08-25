# Ultraplan - Platform-Scale Planning

When a user's idea is a **full platform** (multiple sub-products, AI agents, or major modules), Loop Engineer handles it **automatically**. The user only types their idea.

## User command (all you need)

```text
/plan-loop A platform with support triage agent, admin portal, and billing API
```

Or in chat:

```text
/plan-loop <full product idea>
/loop-engine <full product idea>
```

The agent runs:

```bash
loop session-start --command /plan-loop --text "<idea>"  # internal agent runtime
```

## What runs automatically

1. **Scale detect** → `plan/PLAN_SCALE.md` (`convenient` vs `platform`)
2. **Idea capture** → `plan/IDEA.md`
3. **Route card** → `plan/PLAN_BOOTSTRAP.md` (agent reads this first)
4. **If platform:** extract modules from idea text → `PRODUCT_MAP.md` → step stubs → `plan/steps/NN-slug/` ultraplan folders
5. **Ultraplan next step** named in bootstrap - agent fills deep docs **one step per session**

No manual scale, module, or decomposition commands for users.

## Per-step ultraplan pack

| File | Content |
|------|---------|
| `overview.md` | Role in platform, metrics |
| `prd.md` | Requirements, stories, NFRs |
| `architecture.md` | Components, APIs, ADRs |
| `agents.md` | Agent loops (type `agent`) |
| `data-model.md` | Entities, tenant rules |
| `integrations.md` | External + cross-step APIs |
| `risks.md` | Risks, compliance |
| `acceptance.md` | Testable done criteria |

## Workflow

```text
User: /plan-loop <idea>  OR  /loop-engine <idea>
  → auto bootstrap (PLAN_BOOTSTRAP.md)
  → [platform] ultraplan one step → feature spec → task-compiler
  → [convenient] standard step + feature spec
  → /develop-product
```

## When a step becomes its own workspace

A `PRODUCT_MAP.md` row can stay planned inside this workspace, or bind to a **sub-product
workspace** in its own folder once it is big enough to plan and build on its own:

```bash
cd main-product/auth-svc && loop setup --use-cwd     # the row now has a real workspace
```

The row stays the platform-level contract; the sub-product owns its own PRD, tasks, and
gates. The main workspace rolls all of them into `plan/SUBPRODUCTS.md` and reports where a
sub-product's plan contradicts the master plan. A row with no workspace is `unbuilt-row`;
a workspace with no row is `unmapped-sub`.

See [`docs/PRODUCT_HIERARCHY.md`](PRODUCT_HIERARCHY.md).

## Agent-only advanced CLI

Not for users - debugging or recovery only:

```bash
# Internal runtime reference for skill authors and maintainers:
loop plan-loop scale --write --text "..."
loop plan-loop decompose
loop plan-loop ultraplan next
loop plan-loop ultraplan next --step "19"  # explicit existing step
```

## Skills

- `skills/plan-loop/phases/ultraplan.md`
- Wired in `commands/plan-loop.md` and `commands/loop-engine.md`
