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
4. **If platform:** extract modules from idea text → `PRODUCT_MAP.md` → owner folders
   (`plan/products/<slug>/` for sub-products; `plan/steps/NN-slug/` for root-owned work)
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

## When a step becomes its own sub-product

A `PRODUCT_MAP.md` row can stay a plain module planned here, or become a **scope** with
its own plan folder, tasks and gates once it is big enough to be planned and built on its
own:

```bash
loop scope new auth --name "Auth and Identity" --map-id 01 --code-dir services/auth
```

The row stays the platform-level contract; the scope owns its PRD, tasks and gates. Its
code can live anywhere - a folder here, or another repo - but its plan stays in this
workspace, so one sub-product can depend on another directly.

See [`docs/SCOPES.md`](docs/SCOPES.md).

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
