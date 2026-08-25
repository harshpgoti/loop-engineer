# Loop commands

Use these directly in any agent that can access the repo:

```text
/setup-loop-engine
/plan-loop
/revise-plan
/ask-loop
/develop-product
/loop-engine
/prod-gap
/status
/doctor
/sync-loop-state
/release-check
/deployment-plan
/compact-loop
/session-start
/session-end
/session-recall
/memory-review
/migrate-import
/upgrade-loop-engineer
/frontend-animation
/feature-new
/spec-clarify
/spec-checklist
/resolve-doubts
/feature-converge
/eval-loop
/product-tree
/scope
/deploy
/plan-loop <idea>
/loop-engine <idea>
/ultraplan-loop
/agent-builder
/diagnose-loop
/research-search
```

Internal runtime (agents, installers, maintainers - **not** steps users chain by hand;
see `docs/INTERNAL_RUNTIME.md`):

```bash
loop setup
loop doctor
loop skills install            # wire every coding agent to this app
loop skills install --project  # or project scope, committed with the repo
loop team-init required        # make Loop the team standard (auto-bootstrap teammates)
loop plan-loop "your full product idea here"
loop workspace tree            # this workspace and the sub-product scopes it holds
loop research "your topic"
loop agent scaffold
loop session-start --command /loop-engine --tool cursor --text "your idea"
```

Agent-only (during `/develop-product`, not for users):

```bash
python scripts/frontend_skill_router.py --write
python scripts/agent_skill_router.py --write
```

The agent must route the command through `commands/*.md` and update `memories/MEMORY.md`, `DOUBTS.md`, and `HANDOFF.md`.

---

## Command meanings

| Command | Runs | Use when |
|---------|------|----------|
| `/setup-loop-engine` | `commands/setup-loop-engine.md` | First-time setup and product workspace registration |
| `/plan-loop` | `commands/plan-loop.md` | Brainstorming, validation, grilling, PRD, architecture |
| `/revise-plan` | `commands/revise-plan.md` | Correct or add a detail to a plan that already exists, without asking which file it belongs in |
| `/ask-loop` | `commands/ask-loop.md` | Ask a question about the existing plan or build; read-only answer with citations, reads code when needed |
| `/develop-product` | `commands/develop-product.md` | Build frontend/backend/db/agents/QA/security/CI/CD |
| `/loop-engine` | `commands/loop-engine.md` | All-in-one loop that chooses plan or build based on gates |
| `/prod-gap` | `commands/prod-gap.md` | Analyze product requirements/progress and write `plan/PROD-GAP.md` |
| `/status` | `commands/status.md` | Quick snapshot of workspace, gate, task, and next command |
| `/doctor` | `commands/doctor.md` | Health-check runtime and product workspace setup |
| `/sync-loop-state` | `commands/sync-loop-state.md` | Reconcile drift across memory, handoff, tasks, and gates |
| `/release-check` | `commands/release-check.md` | Pre-production release readiness check |
| `/deployment-plan` | `commands/deployment-plan.md` | Write or refresh `DEPLOYMENT_PLAN.md` |
| `/compact-loop` | `commands/compact-loop.md` | Durable context summary before long runs or tool switches |
| `/session-start` | `commands/session-start.md` | Always-on bootstrap: recall, manifest, auto-skills (any tool) |
| `/session-end` | `commands/session-end.md` | Always-on closeout: memory review, staged writes, state.db |
| `/session-recall` | `commands/session-recall.md` | Recall only (usually via session-start) |
| `/memory-review` | `commands/memory-review.md` | Curate memory only (usually via session-end) |
| `/migrate-import` | `commands/migrate-import.md` | Import memory/skills from an external workspace folder |
| `/frontend-animation` | `commands/frontend-animation.md` | Built-in GSAP, Motion.dev, and 3D animation skills |
| `/feature-new` | `commands/feature-new.md` | Create `plan/features/NNN-slug/` and set active feature |
| `/spec-clarify` | `commands/spec-clarify.md` | Structured clarification on active feature spec |
| `/spec-checklist` | `commands/spec-checklist.md` | Spec quality gate before feature-plan |
| `/resolve-doubts` | `commands/resolve-doubts.md` | Interactively clear all open doubts/blockers plan-wide, ending in a go/no-go for development |
| `/feature-converge` | `commands/feature-converge.md` | Drift check after implementation |
| `/eval-loop` | `commands/eval-loop.md` | Score golden cases, record runs, catch regressions |
| `/product-tree` | `commands/product-tree.md` | Show sub-product workspaces, their roll-up, and drift vs the master plan |
| `/ultraplan-loop` | `commands/ultraplan-loop.md` | Deep planning per step when scale is platform |
| `/agent-builder` | `commands/agent-builder.md` | Design/scaffold an AI agent (or agentic/dynamic workflow) as the product |
| `/research-search` | `commands/research-search.md` | Search arXiv, Research Square, and SSRN to ground a claim |
| `/diagnose-loop` | `commands/diagnose-loop.md` | Build a feedback loop that goes red on a bug, then hypothesise |
| `/deploy` | `commands/deploy.md` | Deploy to the chosen cloud, recording every resource and what it serves |
| `/scope` | `commands/scope.md` | Sub-products inside one workspace: list, switch, check contracts, absorb a federated sub-product |
| `/upgrade-loop-engineer` | `commands/upgrade-loop-engineer.md` | Safe tool update without overwriting product data |

## Aliases

| Alias | Command |
|-------|---------|
| `/startup-discovery-loop` | `/plan-loop` |
| `/startup-build-loop` | `/develop-product` |
| `/develop-product` | `/develop-product` |
| `/all-in-one` | `/loop-engine` |

## Step 1 → Step 2 transition prompt

```text
Verify GATES.yml: G-INIT-01, G-DISCOVERY-01, G-DISCOVERY-02, G-ARCH-01.
If all pass:
1. Create monorepo per `plan/main_plan.md` and active `plan/step_*.md`
2. Add schemas/contracts defined by the active product step
3. Switch to `/develop-product`
If blocked: list blockers and run discovery tasks only.
```

---

## Recurring loop

```text
/loop 2h /loop-engine
```
