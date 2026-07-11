# /product-develop

Run Step 2: build the product from the approved plan, including frontend, backend, database, agent loops, QA, auto-validation, docs, security, compliance, CI/CD, deployment readiness, and handoff.

## How To Interpret

If the user says `/product-develop`, `product-develop`, `start development`, or `develop product`, execute this file directly. Do not ask for boot prompts or separate setup files.

## Required Reads

In central-tool setup, read command/skill files from `loop-engineer/`, but read and write product-state files and product code in the registered product workspace.

1. `AGENTS.md`
2. `memories/SOUL.md`
3. `memories/USER.md`
4. `memories/MEMORY.md`
5. `CONTEXT.md`
6. `DOUBTS.md`
7. `plan/SESSION_MANIFEST.md` (after session-start)
8. `skills/product-develop/SKILL.md`
9. `skills/session-lifecycle/SKILL.md`
10. `skills/feature-workflow/SKILL.md`
11. `skills/plan-loop/phases/spec-clarify.md` (when requirements ambiguous)
12. `skills/feature-converge/SKILL.md`
13. `skills/frontend-animation/SKILL.md` (when `plan/AUTO_SKILLS.md` present)
14. `skills/implementation-planner/SKILL.md`
15. `skills/code-reviewer/SKILL.md`
16. `skills/qa-validation/SKILL.md`
17. `skills/security-compliance/SKILL.md`
18. `skills/prod-gap/SKILL.md`
19. `skills/deployment-plan/SKILL.md`
20. `skills/compact-loop/SKILL.md`
21. `skills/memory-review/SKILL.md`
22. `plan/main_plan.md`
23. relevant `plan/step_*.md`
24. `.loop/active-feature.json` and active feature `spec.md`, `feature-plan.md`, `tasks.md`
25. `plan/SESSION_RECALL.md`
26. `plan/AUTO_SKILLS.md` (if present - read before frontend work)
27. `CURRENT_STATE.md`
28. `TASKS.yml`
29. `GATES.yml`
30. `DECISIONS.md`
31. `HANDOFF.md`
32. Product repo `AGENTS.md` if a product repo exists

Product-state files (`plan/main_plan.md`, `plan/`, `memories/MEMORY.md`, `TASKS.yml`, etc.) must come from the product workspace, not from the reusable `loop-engineer/` repo.

## Gate Check

Before building, classify the work:

- **Planning-only build instruction:** allowed anytime.
- **Synthetic prototype / reversible scaffold:** allowed if `DOUBTS.md` blockers are documented.
- **Production feature / sensitive data / external integration:** blocked until relevant gates pass.

Do not process real sensitive or regulated data until the relevant gate passes.

## Loop

```text
SESSION-START → RECALL → AUTO-SKILLS → SELECT TASK → IMPLEMENTATION PLAN → BUILD → TEST → REVIEW → CONVERGE → PROD-GAP → SESSION-END
```

## Cycle checklist (all develop features)

| Step | Feature | Command / script |
|------|---------|------------------|
| Start | Session lifecycle | `loop session-start --command /product-develop` |
| Bootstrap | Manifest + recall + auto-skills | `SESSION_MANIFEST.md`, `AUTO_SKILLS.md` |
| Pre-build | Active feature tasks | `tasks.md` + `TASKS.yml` |
| Blocked? | Clarify spec | `/spec-clarify` |
| Build | Plan diff + implement | `implementation-planner` |
| Frontend | Motion/3D skills | Read `AUTO_SKILLS.md` - do not ask user for library |
| Quality | Review + QA + security | `code-reviewer`, `qa-validation`, `security-compliance` |
| Sync | Tasks + converge | Update `tasks.md`; `loop feature converge` |
| Release | Gaps + deploy | `/prod-gap`, `/deployment-plan` |
| End | Memory + compact | `memory review --stage`, `/compact-loop` if long |
| End | Session lifecycle | `loop session-end --command /product-develop` |

## Always-on lifecycle (first and last step)

```bash
loop session-start --command /product-develop --tool "<tool>"
```

Read `plan/SESSION_MANIFEST.md` first - it lists recall, memory, and auto-skills.

At closeout:

```bash
loop session-end --command /product-develop --summary "<progress>"
```

## Development Scope

Build in the order defined by active feature `tasks.md`, `TASKS.yml`, and the active `plan/step_*.md`. If no active feature, run `loop feature new` or continue from `TASKS.yml` only.

```bash
loop feature list   # show active feature (*)
```

At session start, recall is included in `loop session-start`. For manual recall:

```bash
loop recall
```

For each task:

1. Run `skills/implementation-planner/SKILL.md`.
2. Implement the smallest safe diff.
3. Run relevant tests/checks.
4. Run `skills/code-reviewer/SKILL.md`.
5. Run `skills/qa-validation/SKILL.md` when behavior changes.
6. Run `skills/security-compliance/SKILL.md` when data, auth, external calls, or risk changes.
7. Update docs and handoff.
8. Run `/prod-gap` after a task or build loop completes to identify production-readiness blockers.
9. If `/prod-gap` finds P0/P1 technical blockers that are safe and in scope, add/update tasks and continue fixing them.
10. If `/prod-gap` finds human-required blockers, list them in `plan/PROD-GAP.md`, `DOUBTS.md`, and `HANDOFF.md`, then ask the user at the end.
11. At loop closeout, run `/feature-converge` (or rely on `loop session-end` which runs converge for `/product-develop`):
    ```bash
    loop feature converge
    ```
12. At loop closeout, run `/deployment-plan` (or `scripts/deployment_plan.py`) to write `DEPLOYMENT_PLAN.md`. Reuse cloud, LLM, and deployment answers already recorded in `DECISIONS.md`, resolved `DOUBTS.md`, or `plan/main_plan.md`. Ask the user only for unresolved deployment questions.
13. Run `/memory-review` at closeout (default `--stage`):
    ```bash
    loop memory review --stage
    ```
14. Run `/compact-loop` when development is long, many files changed, tests generated substantial context, the user may switch tools, or the context is getting heavy. At minimum, ensure `COMPACT.md` is current before ending a large `/product-develop` session.
15. **Session end** (mandatory - runs memory-review staging + feature converge):
    ```bash
    loop session-end --command /product-develop --summary "<progress>"
    ```

## Required Checks

Run relevant tests before marking done:

- Backend: lint, typecheck where configured, unit/integration tests, migration tests
- Frontend: lint, typecheck, unit tests, Playwright smoke
- Security: gitleaks, dependency audit, Bandit/Semgrep where configured
- Risk/compliance: no sensitive data in logs, tenant isolation when applicable, audit events where needed

If a command cannot run, record why in `memories/MEMORY.md` and `HANDOFF.md`.

Validate structure when plan or task outputs change:

```bash
python scripts/validate_outputs.py
```

## Output

Return:

1. What was built
2. Implementation plan summary
3. Tests/checks run
4. Code review findings
5. Security/compliance status
6. Files changed
7. Feature converge status (`converge-report.md`)
8. Production gap status (`plan/PROD-GAP.md` updated, top blockers)
9. Deployment plan status (`DEPLOYMENT_PLAN.md` updated, reused decisions, open deployment questions)
10. Human-required blockers to ask user
11. Compact status (`COMPACT.md` updated or why not needed)
12. Memory review status (`plan/MEMORY_REVIEW.md`, pending writes if staged)
13. Next task (from active feature `tasks.md`)

## Auto Update

Always update:

- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md` or relevant `plan/step_*.md` if product plan changed
- `CURRENT_STATE.md`
- `TASKS.yml`
- active feature `tasks.md` when present
- `HANDOFF.md`
- `DEPLOYMENT_PLAN.md` when the loop completes
- `.ai/SESSION_LOG.md`
