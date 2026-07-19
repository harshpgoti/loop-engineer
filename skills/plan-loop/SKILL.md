---
name: plan
description: Orchestrates product planning end to end - initialize a fresh product plan, grill assumptions, run the senior product council, deep-plan platform steps (ultraplan), clarify and checklist the feature spec, and compile buildable tasks. Use when the user types /plan-loop, /ultraplan-loop, /spec-clarify, /spec-checklist, or asks to prepare product development.
---

# Plan (orchestrator)

Turn a product idea into a validated, buildable plan. This skill is a **thin orchestrator**: it holds the loop, the read order, and a phase router. Each planning phase lives in its own file under `phases/` and is **loaded only when its trigger fires** - never preload all phases.

## Command

`/plan-loop` (also the entry for `/ultraplan-loop`, `/spec-clarify`, `/spec-checklist`, which jump straight to one phase).

## Progressive disclosure - the one rule

> Read the orchestrator (this file) every planning session. Load a **phase file** only when the harness or a command selects it. Do not read all `phases/*.md` up front.

The harness picks the phase for you: `loop session-start` / `loop plan-loop "<idea>"` writes a **`PHASE:` line** into `plan/PLAN_BOOTSTRAP.md` and `plan/SESSION_MANIFEST.md`, computed from deterministic state (init status, `plan/PLAN_SCALE.md`, ultraplan progress, active feature, checklist verdict). Read that line, then open the matching phase file.

## Phase router

| Phase | Load when | File |
|-------|-----------|------|
| **grill** | product uninitialized, pivot, or `PHASE: grill` | `phases/grill.md` |
| **council** | before PRD/architecture lock, or `PHASE: council` | `phases/council.md` |
| **ultraplan** | `plan/PLAN_SCALE.md` = platform with an incomplete step, `/ultraplan-loop`, or `PHASE: ultraplan` | `phases/ultraplan.md` |
| **spec-clarify** | active feature spec has open questions, `/spec-clarify`, or `PHASE: spec-clarify` | `phases/spec-clarify.md` |
| **spec-checklist** | before locking `feature-plan.md`, `/spec-checklist`, or `PHASE: spec-checklist` | `phases/spec-checklist.md` |
| **task-compiler** | spec checklist Ready → compile tasks, or `PHASE: task-compiler` | `phases/task-compiler.md` |

## Read First (orchestrator only - not the phase files)

1. `AGENTS.md`
2. `memories/SOUL.md`, `memories/USER.md`, `memories/MEMORY.md`
3. `DOUBTS.md`
4. `plan/main_plan.md`, `plan/`
5. `TASKS.yml`, `GATES.yml`, `EVIDENCE_LOG.md`, `DECISIONS.md`, `HANDOFF.md`
6. `plan/PLAN_BOOTSTRAP.md` and `plan/SESSION_MANIFEST.md` - get the `PHASE:` line
7. `templates/plan_deployment_questions.md`
8. `skills/session-lifecycle/SKILL.md`, `skills/session-recall/SKILL.md`, `skills/memory-review/SKILL.md`, `skills/compact-loop/SKILL.md`
9. `skills/feature-workflow/SKILL.md` (feature spec folder routing)
10. `skills/deployment-plan/SKILL.md` (closeout deployment draft)
11. `skills/agent-builder/SKILL.md` (when the product is/includes an AI agent - see `plan/AUTO_AGENT_SKILLS.md`)
12. `skills/research-search/SKILL.md`, `skills/tool-orchestrator/SKILL.md`

Then load the current phase file from the router above.

## Loop

```text
SESSION-START -> READ PHASE -> [grill -> council] -> (platform: ultraplan/step) -> spec-clarify -> spec-checklist -> task-compiler -> SESSION-END
```

## Instructions

0. Run `loop session-start --command /plan-loop --text "<user idea>"` (or `loop plan-loop "<idea>"`) and read `plan/PLAN_BOOTSTRAP.md` + `plan/SESSION_MANIFEST.md`. Note the `PHASE:` line.
1. `session-start` auto-detects agent-development signals - if `plan/AUTO_AGENT_SKILLS.md` was written, read it and `skills/agent-builder/SKILL.md` before drafting architecture.
2. **If product is uninitialized**, ask for product name, target user, problem, first product step, constraints, sensitive data, preferred stack, and deployment targets. Capture deployment choices in `plan/main_plan.md` → **Deployment & Infrastructure**:
   - cloud provider; single-cloud vs multi-cloud; primary region(s); compute model; database hosting; LLM provider and model(s); embedding provider/model; agent runtime; CI/CD platform; secrets management.
3. **Reuse rule:** if a deployment answer already exists in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`, reuse it, inform the user, and do not ask again unless they want to change it.
4. If the user is unavailable, record missing inputs in `DOUBTS.md` and do not invent product-specific facts.
5. Restate the product state from `memories/MEMORY.md` and `plan/main_plan.md`.
6. **Run the current phase** (load its file from the router), then advance along the loop. Validate claims with sources before adding product decisions; for research-grounded claims use `skills/research-search/SKILL.md` (`loop research "<query>"`) and cite in `EVIDENCE_LOG.md`.
7. Update `plan/main_plan.md`, `plan/step_XX_<name>.md`, `GATES.yml`, `DECISIONS.md`, and `EVIDENCE_LOG.md` as phases produce them.
8. Draft `DEPLOYMENT_PLAN.md` with `python scripts/deployment_plan.py --source plan`.
9. Update `memories/MEMORY.md`, `DOUBTS.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.
10. Run `memory-review` at closeout with `--stage` by default (`loop memory review --stage`).
11. Run `compact-loop` when planning is long, many files changed, the user may switch tools, or the context is getting heavy.
12. Run `loop session-end --command /plan-loop` (mandatory closeout).

## Optional Initializer

```bash
python scripts/init_product.py --name "<product>" --first-step "<step>" --cloud-provider "<cloud>" --cloud-strategy "<single|multi>" --llm-provider "<provider>" --llm-models "<models>"
```

## Output

- Product plan summary
- Deployment decisions captured or reused
- Open user questions; evidence added
- Step files created/updated
- Active feature spec status (`plan/features/`)
- Plan scale and ultraplan status (`plan/PLAN_SCALE.md`, `plan/ULTRAPLAN_STATUS.md`)
- Phase(s) run this session and next `PHASE:`
- `DEPLOYMENT_PLAN.md` draft status; gate status; compact status
- Next command

## After the plan exists

Once `plan/main_plan.md` is initialized, route later corrections or additions (not a new
planning session) to `skills/revise-plan/SKILL.md` (`/revise-plan`) instead of re-running
grill/council - it loads the full plan surface and edits the right file directly.

## Stop Conditions

Stop and ask if:

- A decision changes the product direction
- Sensitive or regulated data is requested before the relevant gate passes
- The product repo should be created but product/repo strategy is unresolved
- Evidence is too weak for a major architecture or product decision
- Cloud or LLM vendor choice has major cost, compliance, or lock-in impact and is still unresolved
