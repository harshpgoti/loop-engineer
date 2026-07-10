# /loop-engine

Run the all-in-one product loop: Step 1 planning and Step 2 product development, with gates deciding when to move from planning to build.

**This is the primary entry point.** It must run every built-in capability — nothing is optional or skipped unless a gate blocks it.

## How To Interpret

If the user says `/loop-engine`, `/loop-engine <idea>`, `loop engine`, `all in one`, or describes a product idea, execute this file directly.

**User types only the idea.** Auto-bootstrap runs on session-start with `--text` (same as `/plan-loop`).

```bash
loop session-start --command /loop-engine --tool "<tool>" --text "<user product idea>"
```

Read `plan/PLAN_BOOTSTRAP.md` first when present.

## Required Reads

Read command/skill files from the tool app. Product-state files come from the **active workspace** (local `.loop-engineer/` auto-detected from cwd, else `~/.loop-engineer/data/`).

1. `plan/SESSION_MANIFEST.md` (after session-start — **read first**)
2. `AGENTS.md`
3. `memories/SOUL.md`
4. `memories/USER.md`
5. `memories/MEMORY.md`
6. `CONTEXT.md`
7. `DOUBTS.md`
8. `skills/loop-engine/SKILL.md`
9. `skills/session-lifecycle/SKILL.md`
10. `commands/plan-loop.md` (when routing to planning)
11. `commands/product-develop.md` (when routing to development)
12. `skills/feature-workflow/SKILL.md`
13. `skills/spec-clarify/SKILL.md`
14. `skills/spec-checklist/SKILL.md`
15. `skills/feature-converge/SKILL.md`
16. `skills/task-compiler/SKILL.md`
17. `skills/product-council/SKILL.md`
18. `skills/product-grill/SKILL.md`
19. `skills/implementation-planner/SKILL.md`
20. `skills/code-reviewer/SKILL.md`
21. `skills/qa-validation/SKILL.md`
22. `skills/security-compliance/SKILL.md`
23. `skills/prod-gap/SKILL.md`
24. `skills/deployment-plan/SKILL.md`
25. `skills/cicd-release/SKILL.md`
26. `skills/compact-loop/SKILL.md`
27. `skills/memory-review/SKILL.md`
28. `skills/frontend-animation/SKILL.md` (when manifest lists auto-skills)
29. `plan/main_plan.md`
30. `plan/` and `plan/step_*.md`
31. `.loop/active-feature.json` and active feature folder when present
32. `plan/SESSION_RECALL.md`
33. `plan/AUTO_SKILLS.md` (if present)
34. `CURRENT_STATE.md`
35. `TASKS.yml`
36. `GATES.yml`
37. `EVIDENCE_LOG.md`
38. `DECISIONS.md`
39. `HANDOFF.md`

Product-state files must come from the product workspace, not from the reusable `loop-engineer/` repo.

## Full cycle (every feature wired)

```text
SESSION-START
  → SESSION_MANIFEST + SESSION_RECALL
  → AUTO-SKILLS (frontend router, if signals match)
  → ROUTE (plan branch | develop branch)
  → FEATURE SPEC (new → clarify → checklist → feature-plan → tasks)
  → TASK-COMPILER (tasks.md ↔ TASKS.yml)
  → BUILD (implementation-planner → code → review → QA → security)
  → FEATURE-CONVERGE + PROD-GAP + DEPLOYMENT-PLAN
  → MEMORY-REVIEW + COMPACT (if long)
SESSION-END
```

## Cycle checklist (all features — primary entry)

| Step | Feature | When |
|------|---------|------|
| Start | Session lifecycle | `loop session-start --command /loop-engine` |
| Bootstrap | Manifest + recall | `SESSION_MANIFEST.md`, `SESSION_RECALL.md` |
| Bootstrap | Auto frontend skills | `AUTO_SKILLS.md` when motion/3D signals |
| Setup | Model provider (API inference) | `loop model setup` → `plan/MODEL_STATUS.md` |
| Route | Pick branch | See routing table below |
| Plan branch | Scale + ultraplan | `loop plan-loop scale`, `ultraplan`, `PRODUCT_MAP.md` |
| Plan branch | Full `/plan-loop` cycle | `commands/plan-loop.md` |
| Plan branch | Feature spec | `feature new` → `spec-clarify` → `spec-checklist` → `task-compiler` |
| Develop branch | Full `/product-develop` cycle | `commands/product-develop.md` |
| Develop branch | Build + review | `implementation-planner`, `code-reviewer`, `qa-validation`, `security-compliance` |
| Develop branch | Drift + gaps | `feature converge`, `/prod-gap` |
| Either | Deployment | `/deployment-plan` |
| Either | Release (if in scope) | `cicd-release` |
| Long session | Compact | `/compact-loop` |
| End | Memory review | via `loop session-end` (staged) |
| End | Session lifecycle | `loop session-end --command /loop-engine` |

## Always-on lifecycle (mandatory bookends)

```bash
loop session-start --command /loop-engine --tool "<tool>"
# ... work ...
loop session-end --command /loop-engine --summary "<progress>"
```

Read `plan/SESSION_MANIFEST.md` before all other reads. Do not skip session-end.

## Routing logic

After session-start, pick **one branch** per session (or chain plan → develop when gates allow):

| Condition | Action |
|-----------|--------|
| `plan/main_plan.md` UNINITIALIZED or `G-INIT-01` blocked | Execute **`/plan-loop` flow** (`commands/plan-loop.md` steps 1–23) |
| Evidence / PRD / architecture gates blocked | **`/plan-loop` flow** + `product-council` |
| After user describes product idea | Auto: `plan/PLAN_BOOTSTRAP.md` via session-start `--text` or `loop plan-loop "<idea>"` |
| Scale is **platform** | Follow bootstrap → **`skills/ultraplan/SKILL.md`** on next step |
| Step plan missing for current module | **`/plan-loop` flow** (step file + ultraplan pack if platform) |
| No active feature folder | `loop feature new "<title>" --step plan/step_XX.md` |
| Open spec questions / ambiguous requirements | **`/spec-clarify`** |
| Spec not checklist-passed | **`/spec-checklist`** — do not compile tasks until ready |
| No `tasks.md` or `TASKS.yml` empty | **`task-compiler`** |
| Build gates pass, tasks ready | Execute **`/product-develop` flow** (`commands/product-develop.md`) |
| Requirements blocked mid-build | **`/spec-clarify`** then resume develop |
| Frontend motion/3D in task | Read `plan/AUTO_SKILLS.md` + matched skills |
| After dev slice or before session-end on develop | **`loop feature converge`** + **`/prod-gap`** |
| P0/P1 technical blockers from prod-gap | Route back to **`/product-develop`** |
| Human-required blockers | `DOUBTS.md` + `HANDOFF.md` — ask user |
| Meaningful work unit complete | **`/deployment-plan`** |
| Long session / tool switch | **`/compact-loop`** |
| Every closeout | **`loop session-end`** (includes memory-review staging; converge on develop) |

## Execute planning branch

When routing to plan, follow **`commands/plan-loop.md`** in full:

```text
scale detect → [convenient: step + feature spec] | [platform: PRODUCT_MAP → ultraplan/step → feature spec per step]
→ task-compiler → deployment-plan draft → validate_outputs → memory + handoff
```

## Execute development branch

When routing to develop, follow **`commands/product-develop.md`** in full:

```text
select task (active feature tasks.md + TASKS.yml)
→ implementation-planner → build → test → code-reviewer
→ qa-validation → security-compliance (when applicable)
→ update tasks.md + TASKS.yml → prod-gap → feature-converge
→ deployment-plan → memory + handoff
```

## Product completion definition

The product is not "done" until:

- PRD and ADRs exist
- Active feature spec checklist passed and `tasks.md` synced with `TASKS.yml`
- Backend/API works
- DB migrations work
- Frontend workbench works (auto-skills applied when motion/3D)
- Agent loops are schema-validated
- Tests and evals pass
- Security scans pass or have documented waivers
- Product-specific risk/compliance packet exists
- CI/CD deploys to staging (`cicd-release` when in scope)
- Rollback and smoke tests are documented
- `memories/MEMORY.md` and `HANDOFF.md` are current
- `converge-report.md` shows no critical drift
- `plan/PROD-GAP.md` has no unresolved P0 launch blockers
- `DEPLOYMENT_PLAN.md` is current
- `COMPACT.md` is current after long sessions

## Output

Return:

1. Which branch ran (`plan`, `develop`, or both)
2. Why that branch was chosen (gate + feature state)
3. Session lifecycle status (manifest, session-end)
4. Active feature status (`plan/features/`, converge if develop ran)
5. Auto-skills applied (if any)
6. Gate status
7. Work completed
8. Open doubts
9. Production gap status
10. Deployment plan status
11. Human-required blockers
12. Next action: `/loop-engine`, `/plan-loop`, or `/product-develop`
