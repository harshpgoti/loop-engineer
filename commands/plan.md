# /plan

Run Step 1: initialize product planning, validation, grilling, evidence, PRD, architecture, and development instructions.

## How To Interpret

If the user says `/plan`, `/plan <idea>`, `/startup-discovery-loop`, `plan`, or describes a product idea, execute this file directly. Do not ask for `AGENT_BOOT_SEQUENCE.md`.

**User types only the idea.** Loop Engineer auto-detects scale, decomposes modules, and routes ultraplan — no manual scale/decompose commands.

## One command (required first step)

```bash
loop session-start --command /plan --tool "<tool>" --text "<user's full product idea>"
loop plan "<user's full product idea>"
```

Both run the same auto-bootstrap → read **`plan/PLAN_BOOTSTRAP.md`** before other plan reads.

Advanced (agent-only, not for users): `loop plan scale`, `loop plan decompose`, `loop plan ultraplan next`.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read and write product-state files in the **active workspace** (local `.loop-engineer/` auto-detected from cwd, else `~/.loop-engineer/data/`). See `docs/DATA_LAYOUT.md`.

1. `AGENTS.md`
2. `memories/SOUL.md`
3. `memories/USER.md`
4. `memories/MEMORY.md`
5. `CONTEXT.md`
6. `DOUBTS.md`
7. `skills/plan/SKILL.md`
8. `skills/ultraplan/SKILL.md`
9. `skills/session-lifecycle/SKILL.md`
9. `skills/feature-workflow/SKILL.md`
10. `skills/spec-clarify/SKILL.md`
11. `skills/spec-checklist/SKILL.md`
12. `skills/product-council/SKILL.md`
13. `skills/product-grill/SKILL.md`
14. `skills/task-compiler/SKILL.md`
15. `skills/deployment-plan/SKILL.md`
16. `skills/compact-loop/SKILL.md`
17. `skills/memory-review/SKILL.md`
18. `plan/main_plan.md`
19. `plan/` and `plan/step_*.md`
20. `.loop/active-feature.json` (when present)
21. `plan/SESSION_MANIFEST.md`
22. `plan/SESSION_RECALL.md`
23. `CURRENT_STATE.md`
24. `TASKS.yml`
25. `GATES.yml`
26. `EVIDENCE_LOG.md`
27. `DECISIONS.md`
28. `HANDOFF.md`

Product-state files (`plan/main_plan.md`, `plan/`, `memories/MEMORY.md`, `TASKS.yml`, etc.) must come from the product workspace, not from the reusable `loop-engineer/` repo.

## Loop

```text
SESSION-START → RECALL → PLAN → GRILL → EVIDENCE → PRD → ARCHITECTURE → FEATURE SPEC → TASKS → SESSION-END
```

## Cycle checklist (all plan features)

| Step | Feature | Command / script |
|------|---------|------------------|
| Start | Session lifecycle | `loop session-start --command /plan --text "<idea>"` |
| Bootstrap | **Auto plan from idea** | `plan/PLAN_BOOTSTRAP.md` (scale + map + ultraplan route) |
| Bootstrap | Recall + manifest | `plan/SESSION_MANIFEST.md`, `SESSION_RECALL.md` |
| Setup | Model provider (API inference) | `loop model setup` → `plan/MODEL_STATUS.md` |
| Plan | Product grill + council | `product-grill`, `product-council` |
| Plan | Step plan | `plan/step_XX_*.md` (index; ultraplan for platform) |
| Plan | Feature spec | `loop feature new` → `/spec-clarify` → `/spec-checklist` → `feature-plan.md` |
| Plan | Tasks | `task-compiler` → `tasks.md` + `TASKS.yml` |
| Plan | Deployment | `deployment_plan.py --source plan` |
| Plan | Validate | `validate_outputs.py` |
| End | Memory + compact | `memory review --stage`, `/compact-loop` if long |
| End | Session lifecycle | `loop session-end --command /plan` |

## Always-on lifecycle (first and last step)

```bash
loop session-start --command /plan --tool "<tool>"
```

Read `plan/SESSION_MANIFEST.md` before other required reads.

At closeout (after memory/handoff updates):

```bash
loop session-end --command /plan --summary "<progress>"
```

```text
RECALL → DETECT INIT → ASK/INFER (PRODUCT + DEPLOYMENT) → GRILL → COUNCIL → RESEARCH → PLAN → COMPILE TASKS → DEPLOYMENT PLAN DRAFT → VALIDATE → MEMORY → MEMORY REVIEW → COMPACT IF NEEDED
```

## Steps

0. **Session start + auto-bootstrap** (pass the user's idea as `--text`):
   ```bash
   loop session-start --command /plan --tool "<tool>" --text "<user product idea>"
   ```
   Or: `loop plan "<user product idea>"`
   Read `plan/PLAN_BOOTSTRAP.md` then `plan/SESSION_MANIFEST.md`. Do **not** ask the user to run scale/decompose/ultraplan manually.
1. **Detect initialization.** If `plan/main_plan.md` says `Status: **UNINITIALIZED**`, initialize the user's product plan.
2. **Ask for required product inputs:** product name, target user, problem, first product step, constraints, sensitive data, preferred stack.
3. **Ask for deployment inputs during planning:** cloud provider, single vs multi-cloud, primary region(s), compute model, database hosting, LLM provider/model, embedding model, agent runtime, CI/CD platform, secrets management. Use `templates/plan_deployment_questions.md` as the checklist.
4. **Reuse prior answers** from `DECISIONS.md`, resolved `DOUBTS.md`, or existing `plan/main_plan.md` → **Deployment & Infrastructure**. Inform the user when reusing; do not ask again unless they want to change something.
5. **If the user is unavailable**, record missing inputs in `DOUBTS.md` and do not invent product-specific facts.
6. **Restate current product state** from `memories/MEMORY.md` and `plan/main_plan.md`, not from chat memory.
7. **Review `DOUBTS.md`**. Ask any open blocking questions. If unavailable, keep doubts open and continue only safe planning work.
8. **Grill the plan** using:
   - first customer ICP
   - buyer and budget
   - real data access
   - compliance path
   - wedge sharpness
   - evidence quality
   - cloud/deployment fit
   - LLM vendor lock-in and cost
9. **Run `skills/product-council/SKILL.md`** before major product or architecture decisions.
10. **Fact-check claims** before decisions. Add sources to `EVIDENCE_LOG.md`.
11. **Update `plan/main_plan.md`** with product-level strategy and the **Deployment & Infrastructure** table. Use `templates/main_plan.template.md` on first initialization.
12. **Follow `plan/PLAN_BOOTSTRAP.md`** for scale branch (already auto-detected):
    - **`convenient`:** one step file + feature spec (steps 15–17).
    - **`platform`:** ultraplan the step named in bootstrap (one step per session), then feature spec for that step only.

## Plan scale branch (automatic — do not ask user to run manual commands)

### A) `convenient` — single wedge product

Continue with standard step + deep **feature spec** (steps 15–17 below).

### B) `platform` — multiple sub-products / agents

Already bootstrapped: `PRODUCT_MAP.md`, step stubs, `plan/steps/NN-slug/` folders. **Your job:** fill the ultraplan pack for the step listed in `PLAN_BOOTSTRAP.md` — one step per session.

13. **Use the initializer when enough product inputs are known** (convenient scale only, or first platform step):
   ```bash
   python scripts/init_product.py --name "<product>" --first-step "<step>" --target-user "<user>" --problem "<problem>" --cloud-provider "<cloud>" --cloud-strategy "<single|multi>" --llm-provider "<provider>" --llm-models "<models>"
   ```
14. **Create or update planning docs** from templates when useful:
   - `templates/prd.template.md`
   - `templates/adr.template.md`
   - `templates/risks.template.md`
   - `templates/metrics.template.md`
15. **Create or update `plan/step_XX_<name>.md`** — for platform scale, step file is an **index** only; deep content lives in `plan/steps/NN-slug/`. For convenient scale, use `templates/step_plan.template.md` with full PRD, flows, and acceptance criteria.
16. **Create or update active feature spec** (built-in spec-driven workflow):
   ```bash
   loop feature new "<module title>" --step plan/step_XX_<name>.md
   ```
   Fill `plan/features/NNN-slug/spec.md` from the step plan — link, do not duplicate entire step file.
   Run `/spec-clarify` then `/spec-checklist` before locking `feature-plan.md`.
17. **Run `skills/task-compiler/SKILL.md`** to convert plan into tasks, gates, acceptance criteria, test plan, and sync active feature `tasks.md` with `TASKS.yml`.
18. **Record deployment decisions** in `DECISIONS.md` and unresolved items in `DOUBTS.md`.
19. **Draft `DEPLOYMENT_PLAN.md`** from captured planning decisions:
   ```bash
   python scripts/deployment_plan.py --source plan
   ```
20. **Validate outputs** when product files are initialized:
   ```bash
   python scripts/validate_outputs.py
   ```
21. **Update `DECISIONS.md`** for any strategy or architecture decision.
22. **Update `memories/MEMORY.md`, `DOUBTS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.**
23. **Run `/memory-review` at closeout** (default `--stage` for production workspaces):
   ```bash
   python scripts/memory_curator.py --stage
   loop memory review --stage
   ```
24. **Run `/compact-loop` when planning is long, many files changed, the user may switch tools, or the context is getting heavy.** At minimum, ensure `COMPACT.md` is current before ending a large `/plan` session.
25. **Session end** (mandatory — runs memory-review staging):
    ```bash
    loop session-end --command /plan --summary "<progress>"
    ```

## Output

Return:

1. Plan summary
2. Product grill questions answered/open
3. Evidence added
4. Plan files created/updated
5. Product council verdict
6. Task compiler summary
7. Active feature spec status (`plan/features/`, `.loop/active-feature.json`)
8. Plan scale (`plan/PLAN_SCALE.md`) and ultraplan status if platform
9. Deployment decisions captured/reused and `DEPLOYMENT_PLAN.md` status
10. Gate status
11. Compact status (`COMPACT.md` updated or why not needed)
12. Memory review status (`plan/MEMORY_REVIEW.md`, pending writes if staged)
13. Next command: `/plan`, `/ultraplan`, `/product-develop`, or `/loop-engine`

## Stop Conditions

Stop and ask the user when:

- The product direction changes.
- Sensitive or regulated data is requested before the relevant gate passes.
- A build task would create irreversible architecture.
- Customer evidence is too weak to justify product development.
