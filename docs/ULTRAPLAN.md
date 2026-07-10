# Ultraplan — Platform-Scale Planning

When a user's idea is a **full platform** (multiple sub-products, AI agents, or major modules), Loop Engineer handles it **automatically**. The user only types their idea.

## User command (all you need)

```bash
loop plan-loop "A platform with support triage agent, admin portal, and billing API"
```

Or in chat:

```text
/plan-loop <full product idea>
/loop-engine <full product idea>
```

The agent runs:

```bash
loop session-start --command /plan-loop --text "<idea>"
# equivalent: loop plan-loop "<idea>"
```

## What runs automatically

1. **Scale detect** → `plan/PLAN_SCALE.md` (`convenient` vs `platform`)
2. **Idea capture** → `plan/IDEA.md`
3. **Route card** → `plan/PLAN_BOOTSTRAP.md` (agent reads this first)
4. **If platform:** extract modules from idea text → `PRODUCT_MAP.md` → step stubs → `plan/steps/NN-slug/` ultraplan folders
5. **Ultraplan next step** named in bootstrap — agent fills deep docs **one step per session**

No manual `loop plan-loop scale`, `modules`, or `decompose` for users.

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
  → /product-develop
```

## Agent-only advanced CLI

Not for users — debugging or recovery only:

```bash
loop plan-loop scale --write --text "..."
loop plan-loop decompose
loop plan-loop ultraplan next
```

## Skills

- `skills/ultraplan/SKILL.md`
- Wired in `commands/plan-loop.md` and `commands/loop-engine.md`
