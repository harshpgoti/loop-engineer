---
name: plan
description: Orchestrates product planning end to end - initialize a fresh product plan, grill assumptions, run the senior product council, deep-plan platform steps (ultraplan), clarify and checklist the feature spec, and compile buildable tasks. Use when the user types /plan-loop, /ultraplan-loop, /spec-clarify, /spec-checklist, or asks to prepare product development.
---

# Plan (orchestrator)

Turn a product idea into a validated, buildable plan. This skill is a **thin orchestrator**: it holds the loop, the read order, and a phase router. Each planning phase lives in its own file under `phases/` and is **loaded only when its trigger fires** - never preload all phases.

## Command

`/plan-loop` (also the entry for `/ultraplan-loop`, `/spec-clarify`, `/spec-checklist`,
`/resolve-doubts`, which **enter** at one phase and then continue down the pipeline
to the planning terminus - see `docs/CONTINUATION.md`).

## Progressive disclosure - the one rule

> Read the orchestrator (this file) every planning session. Load a **phase file** only when the harness or a command selects it - **and load the next one as you advance through the pipeline**. Do not read all `phases/*.md` up front.

Progressive disclosure controls *when files are read*, not *how far the loop runs*. Reading one phase at a time is correct; **stopping** after one phase is not.

The harness picks the phase for you: the internal session-start runtime writes a
**`PHASE:` line** into `plan/PLAN_BOOTSTRAP.md` and `plan/SESSION_MANIFEST.md`,
computed from deterministic state (init status, `plan/PLAN_SCALE.md`, ultraplan
progress, active feature, checklist verdict). Read that line, then open the matching
phase file.

## Phase router

| Phase | Load when | File |
|-------|-----------|------|
| **grill** | product uninitialized, pivot, or `PHASE: grill` | `phases/grill.md` |
| **parent-findings** | this sub-product has unanswered findings from its parent product, or `PHASE: parent-findings` | `phases/parent-findings.md` |
| **hierarchy** | linked sub-products contradict the master plan (`plan/SUBPRODUCTS.md` has `error` findings), or `PHASE: hierarchy` | `phases/hierarchy.md` |
| **council** | before PRD/architecture lock, or `PHASE: council` | `phases/council.md` |
| **ultraplan** | `plan/PLAN_SCALE.md` = platform with an incomplete step, `/ultraplan-loop`, or `PHASE: ultraplan` | `phases/ultraplan.md` |
| **spec-clarify** | active feature spec has open questions, `/spec-clarify`, or `PHASE: spec-clarify` | `phases/spec-clarify.md` |
| **spec-checklist** | before locking `feature-plan.md`, `/spec-checklist`, or `PHASE: spec-checklist` | `phases/spec-checklist.md` |
| **resolve-doubts** | planning otherwise complete but `DOUBTS.md` has open items, `/resolve-doubts`, or `PHASE: resolve-doubts` | `phases/resolve-doubts.md` |
| **task-compiler** | spec checklist Ready and no open doubts â†’ compile tasks, or `PHASE: task-compiler` | `phases/task-compiler.md` |

## Read First (orchestrator only - not the phase files)

1. `AGENTS.md`
2. `memories/SOUL.md`, `memories/USER.md`, `memories/MEMORY.md`
3. `plan/PLAN_BOOTSTRAP.md` and `plan/SESSION_MANIFEST.md` - get the **`PHASE:`** line
   **and the skills it names**
4. `plan/main_plan.md`, `HANDOFF.md`
5. `DOUBTS.md`, `TASKS.yml`, `GATES.yml`

Then load **the current phase file** from the router above, and **only the skills the
manifest lists for it**.

> **Skills are phase-scoped too.** This list used to name twelve skill files
> unconditionally - 51KB every session, including `revise-plan` (a different command
> entirely) and `agent-builder` (only relevant when the product is an agent). The phase
> router now emits the skills for the selected phase; everything else stays unread.

Read on demand, when the phase you are in actually needs it:

| Need | File |
|------|------|
| Deployment questions during planning | `templates/plan_deployment_questions.md`, `skills/deployment-plan/SKILL.md` |
| Sourcing a claim | `skills/research-search/SKILL.md` → cite in `EVIDENCE_LOG.md` |
| Checking a past decision | `DECISIONS.md` - and `plan/archive/DECISIONS_DETAIL.md` for the rationale |
| Checking evidence behind a decision | `EVIDENCE_LOG.md`; settled sourcing is in `plan/archive/EVIDENCE_SETTLED.md` (`loop archive --search <term>`) |
| Session bookkeeping | `skills/session-lifecycle/SKILL.md`, `skills/memory-review/SKILL.md`, `skills/compact-loop/SKILL.md` |
| The product is/includes an AI agent | `skills/agent-builder/SKILL.md` (the manifest adds it when `plan/AUTO_AGENT_SKILLS.md` exists) |

## Needs a decision

`plan/SESSION_MANIFEST.md` carries a **`## Needs a decision`** block when something in
this workspace has gone out of date. It is absent when there is nothing to do, so if it
is there, work it before planning or building on top of it:

| Condition | Response |
|-----------|----------|
| Generated file no longer matches its sources | `loop fresh`, then re-run whatever generates it - the report names the changed input |
| Evidence past its validity window | `loop evidence` - re-check the claim or record a fresh `Date checked`. Uncertain, not disproved: it still supports whatever cited it |
| Reference to an id nothing defines | `loop graph dangling` - fix the id or add the record |
| Reference-graph rule violation | `loop graph check` - each finding names its own fix |

Never report these to the user as a list of commands to run. Run them, act on what they
say, and report what changed (`docs/CONTINUATION.md`).

## Loop

```text
SESSION-START -> READ PHASE -> [grill -> (parent-findings) -> (hierarchy) -> council] -> (platform: ultraplan/step) -> spec-clarify -> spec-checklist -> resolve-doubts -> task-compiler -> SESSION-END
```

`SESSION-START` and `SESSION-END` perform the product-tree sync automatically. In a
sub-product, parent findings are not merely acknowledged: accepted constraints are folded
into this workspace's plan/spec/tasks before the phase pipeline continues. Closeout converges
the active feature. Never return `loop workspace sync` or `/feature-converge` as user chores.

## Instructions

0. Internally run `loop session-start --command /plan-loop --text "<user idea>"` for
   an uninitialized plan. On an initialized plan, the runtime treats text as routing
   context and does not bootstrap or decompose again. Read `plan/PLAN_BOOTSTRAP.md` +
   `plan/SESSION_MANIFEST.md`. Note the `PHASE:` line.
   This runtime call belongs to the coding agent; never ask the user to run it.
1. `session-start` auto-detects agent-development signals - if `plan/AUTO_AGENT_SKILLS.md` was written, read it and `skills/agent-builder/SKILL.md` before drafting architecture.
2. **If product is uninitialized**, ask for product name, target user, problem, first product step, constraints, sensitive data, preferred stack, and deployment targets. Capture deployment choices in `plan/main_plan.md` â†’ **Deployment & Infrastructure**:
   - cloud provider; single-cloud vs multi-cloud; primary region(s); compute model; database hosting; LLM provider and model(s); embedding provider/model; agent runtime; CI/CD platform; secrets management.
3. **Reuse rule:** if a deployment answer already exists in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`, reuse it, inform the user, and do not ask again unless they want to change it.
4. If the user is unavailable, record missing inputs in `DOUBTS.md` and do not invent product-specific facts.
5. Restate the product state from `memories/MEMORY.md` and `plan/main_plan.md`.
6. **Run the current phase** (load its file from the router), then **immediately advance**: recompute the phase and load the next phase file, repeating until the planning terminus (**tasks compiled + go/no-go**) or a Stop Condition. Do not end the turn asking the user to run the next phase - see `docs/CONTINUATION.md`. Validate claims with sources before adding product decisions; for research-grounded claims use `skills/research-search/SKILL.md` (`loop research "<query>"`) and cite in `EVIDENCE_LOG.md`.
7. Update `plan/main_plan.md`, `plan/step_XX_<name>.md`, `GATES.yml`, `DECISIONS.md`, and `EVIDENCE_LOG.md` as phases produce them.
8. Draft `DEPLOYMENT_PLAN.md` with `python scripts/deployment_plan.py --source plan`.
9. Update `memories/MEMORY.md`, `DOUBTS.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.
10. Run `memory-review` at closeout with `--stage` by default (`loop memory review`).
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
