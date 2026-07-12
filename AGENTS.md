# AGENTS.md - Universal Operating Rules

## Mission

Run a reusable product loop that helps any user plan, validate, build, test, secure, document, and deploy a software product.

## Non-negotiables

1. **Memory first** - Auto-detect local `.loop-engineer/` data in cwd; else read global `~/.loop-engineer/data/`. Then read `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`, `GATES.yml`, `HANDOFF.md`.
2. **First-run initialization** - If `plan/main_plan.md` is uninitialized, `/plan-loop` must initialize product data automatically.
3. **Evidence gate** - Product/architecture decisions require an entry in `EVIDENCE_LOG.md`.
4. **Rules first, AI second** - Prefer deterministic parsers, validators, and rules before LLM calls. Frontend motion/3D: run `frontend_skill_router.py --write` and read `plan/AUTO_SKILLS.md`; do not ask the user to pick a library.
5. **Human approval** - High-risk external actions require explicit user approval unless the product plan says otherwise.
6. **Sensitive data safety** - Do not put secrets, regulated data, or private customer data in logs, fixtures, screenshots, or prompts.
7. **Tenant isolation** - If the product is multi-tenant, every tenant-owned query must be server-scoped and tested.
8. **Idempotent workflows** - Safe retries; audit important transitions.
9. **Minimal diffs** - Match existing conventions; no drive-by refactors.
10. **Tests required** - No task marked done without relevant tests or a documented reason tests could not run.
11. **Handoff required** - Update `memories/MEMORY.md`, `DOUBTS.md`, and `HANDOFF.md` before ending session.
12. **Always-on lifecycle** - Before loop work: `loop session-start`. Before stopping: `loop session-end`. Read `plan/SESSION_MANIFEST.md` first. Works in any tool (Cursor, Claude, Codex, OpenCode, Grok, direct LLM).

## Always-on session lifecycle (any tool)

Always-on memory is **not** chat-bound. Every agent session that touches the product must:

```bash
loop session-start --command "<slash-command>" --tool "<tool>"
# read plan/SESSION_MANIFEST.md + listed files
# ... do work ...
loop session-end --summary "<progress>"
```

| Step | Action |
|------|--------|
| **Start** | Recall → manifest → auto-skills → read manifest |
| **Work** | Follow active command (`/plan-loop`, `/product-develop`, etc.) |
| **End** | Update handoff/memory → stage memory review → log `state.db` |

Details: `docs/SESSION_LIFECYCLE.md` + `skills/session-lifecycle/SKILL.md`.

User does **not** run these manually - the agent runs them. Staged memory: `loop pending approve --all`.

## Portable Commands

The user should be able to type these commands in Cursor, Codex, Claude Code, Grok Build, OpenCode, or a direct LLM with filesystem access. Do not ask the user to paste boot prompts.

| Command | Meaning | First file to read |
|---------|---------|--------------------|
| `/setup-loop-engine` | First-time setup: register product workspace and seed missing product-state files | `commands/setup-loop-engine.md` + `skills/setup-loop-engine/SKILL.md` |
| `/plan-loop` | Run Step 1: brainstorm, grill, fact-check, evidence, PRD, architecture, and task planning | `commands/plan-loop.md` + `skills/plan-loop/SKILL.md` |
| `/startup-discovery-loop` | Alias for `/plan-loop` | `commands/plan-loop.md` + `skills/plan-loop/SKILL.md` |
| `/revise-plan` | Correct or add detail to a plan that already exists - agent routes the edit to the right file from full plan context | `commands/revise-plan.md` + `skills/revise-plan/SKILL.md` |
| `/ask-loop` | Answer a question about the existing plan or build from full context (reads product code when needed); read-only, cites sources | `commands/ask-loop.md` + `skills/ask-loop/SKILL.md` |
| `/product-develop` | Run Step 2: build product from the approved plan, with QA/security/compliance/CI/CD gates | `commands/product-develop.md` + `skills/product-develop/SKILL.md` |
| `/loop-engine` | Run all-in-one loop: Step 1 planning, then Step 2 development when gates allow | `commands/loop-engine.md` + `skills/loop-engine/SKILL.md` |
| `/prod-gap` | Analyze product requirements, current progress, implementation, and readiness gaps | `commands/prod-gap.md` + `skills/prod-gap/SKILL.md` |
| `/status` | Quick snapshot of workspace, gate, task, blockers, and next command | `commands/status.md` + `skills/status/SKILL.md` |
| `/doctor` | Health-check the loop runtime and active product workspace | `commands/doctor.md` + `skills/doctor/SKILL.md` |
| `/sync-loop-state` | Reconcile drift across memory, handoff, tasks, gates, and compact state | `commands/sync-loop-state.md` + `skills/sync-loop-state/SKILL.md` |
| `/release-check` | Focused pre-production release readiness check | `commands/release-check.md` + `skills/release-check/SKILL.md` |
| `/deployment-plan` | Write or refresh deployment targets in `DEPLOYMENT_PLAN.md` | `commands/deployment-plan.md` + `skills/deployment-plan/SKILL.md` |
| `/compact-loop` | Compact long-running context into `COMPACT.md` before continuing or switching tools | `commands/compact-loop.md` + `skills/compact-loop/SKILL.md` |
| `/session-start` | Always-on bootstrap: recall, manifest, auto-skills | `commands/session-start.md` + `skills/session-lifecycle/SKILL.md` |
| `/session-end` | Always-on closeout: memory review, staged writes, state.db log | `commands/session-end.md` + `skills/session-lifecycle/SKILL.md` |
| `/session-recall` | Recall only (usually via session-start) | `commands/session-recall.md` + `skills/session-recall/SKILL.md` |
| `/memory-review` | Curate memory only (usually via session-end) | `commands/memory-review.md` + `skills/memory-review/SKILL.md` |
| `/upgrade-loop-engineer` | Safely update tool files without overwriting product-state files | `commands/upgrade-loop-engineer.md` + `skills/upgrade-loop-engineer/SKILL.md` |
| `/migrate-import` | Import external workspace memory/skills into product paths | `commands/migrate-import.md` + `skills/migrate-import/SKILL.md` |
| `/feature-new` | Create numbered feature spec folder (`plan/features/`) | `commands/feature-new.md` + `skills/feature-workflow/SKILL.md` |
| `/spec-clarify` | Structured clarification on active feature spec | `commands/spec-clarify.md` + `skills/plan-loop/phases/spec-clarify.md` |
| `/spec-checklist` | Spec quality gate before feature-plan | `commands/spec-checklist.md` + `skills/plan-loop/phases/spec-checklist.md` |
| `/feature-converge` | Post-build drift check vs spec/tasks | `commands/feature-converge.md` + `skills/feature-converge/SKILL.md` |
| `/ultraplan-loop` | Deep per-step planning for platform-scale products | `commands/ultraplan-loop.md` + `skills/plan-loop/phases/ultraplan.md` |
| `/manage-model` | Configure AI model provider for API-hosted inference | `commands/manage-model.md` + `skills/model-providers/SKILL.md` |
| `/frontend-animation` | Route to built-in GSAP, Motion.dev, and 3D core skills for frontend work | `commands/frontend-animation.md` + `skills/frontend-animation/SKILL.md` |
| `/agent-builder` | Design/scaffold an AI agent (or agentic/dynamic workflow) as the product itself - auto-activates in `/plan-loop` and `/product-develop` | `commands/agent-builder.md` + `skills/agent-builder/SKILL.md` |
| `/research-search` | Search arXiv, Research Square, and SSRN to ground a claim in evidence | `commands/research-search.md` + `skills/research-search/SKILL.md` |

If a tool does not support slash commands natively, interpret a plain user message containing one of the commands as a request to read the matching command file and execute it.

## Canonical Skill Pack

`skills/` is the source of truth for skills across all tools.

Tool-specific files are adapters only:

- `CLAUDE.md`
- `CURSOR.md`
- `CODEX.md`
- `OPENCODE.md`
- `GROK.md`
- `API_USAGE.md`

Do not put canonical logic only in a tool-specific folder.

## Product Plan Files

Product-specific planning belongs here:

- `plan/main_plan.md`: full product plan for the current user.
- `plan/`: step/module plans such as `plan/step_01_<module>.md`.
- `plan/features/`: one folder per buildable feature (`spec.md`, `feature-plan.md`, `tasks.md`). Active pointer: `.loop/active-feature.json`.

Reusable loop mechanics belong in `skills/` and `commands/`.

## Feature workflow (built-in)

During `/plan-loop`, detect scale (`loop plan-loop scale --write`). **Convenient** → standard step + feature spec. **Platform** → `PRODUCT_MAP.md` + ultraplan pack per sub-product/agent (`skills/plan-loop/phases/ultraplan.md`).

```text
/feature-new → /spec-clarify → /spec-checklist → feature-plan → task-compiler → /product-develop → /feature-converge
```

Platform: `loop plan-loop ultraplan next` before feature spec for each step.

Details: `docs/FEATURE_WORKFLOW.md`, `docs/ULTRAPLAN.md` + `skills/feature-workflow/SKILL.md`.

## Stack defaults (unless DECISIONS.md says otherwise)

Use conservative defaults unless `plan/main_plan.md` or `DECISIONS.md` says otherwise. The agent should choose a stack based on the product, team, risk, and deployment needs rather than forcing one startup's stack.

## Agent roles (use explicitly in prompts)

| Role | Responsibility |
|------|----------------|
| Founder Strategist | Wedge, positioning, kill/keep |
| Market Researcher | TAM, SAM, SOM, competitors, interviews |
| Fact Checker | Sources → EVIDENCE_LOG.md |
| Product Manager | PRD, acceptance criteria |
| System Architect | ADRs, data model, integrations |
| Backend / Frontend Engineer | Implementation |
| AI/LLM Engineer | Loops, prompts, evals |
| Security Engineer | Threat model, scans |
| Compliance Reviewer | Product-specific regulatory checklist |
| QA Engineer | Tests, golden cases |
| DevOps Engineer | CI/CD, deploy |
| Release Manager | Gates, rollback |

**Never** let the builder approve its own PR. Run `autoreview` pattern or separate review pass.

## Senior Review Layers

Use these before major work:

- `skills/plan-loop/phases/council.md` before major product, architecture, or release decisions.
- `skills/plan-loop/phases/task-compiler.md` after planning and before development.
- `skills/implementation-planner/SKILL.md` before code edits.
- `skills/code-reviewer/SKILL.md` after code edits.

## Memory layout (tool vs data)

- **App** (`~/.loop-engineer/app/`): updatable tool runtime - update with `loop update`.
- **Global data** (`~/.loop-engineer/data/`): default memory when no local product folder is detected. Never mixed with `app/`.
- **Local data** (`<product-folder>/.loop-engineer/`): memories/, state.db, plan/main_plan.md - **auto-detected** when you work from that folder. A single hidden folder, kept out of the product's own code.

When you run `/plan-loop`, `/loop-engine`, or any loop command, Loop checks the current folder (and parents) for a `.loop-engineer/` data dir. If found, it uses `<that-folder>/.loop-engineer/`; otherwise it uses `~/.loop-engineer/data/`.

See `docs/DATA_LAYOUT.md`.

Canonical skills live in `skills/`. User skills live in the product workspace `skills/` folder.

## Session loop

```text
SESSION-START → READ MANIFEST → RESTATE → PLAN (one task) → BUILD → TEST → UPDATE MEMORY → SESSION-END
```

## Auto Memory Protocol

Every command must update:

- Run **`loop session-start`** at the beginning and **`loop session-end`** at the end (or `/session-start` / `/session-end`).
- `plan/SESSION_MANIFEST.md` and `plan/SESSION_CLOSEOUT.md` - lifecycle outputs (script-generated).
- `memories/MEMORY.md` (or `memories/MEMORY.md`): what changed, what is happening now, what is next.
- `memories/USER.md`: user profile and durable preferences.
- `state.db`: searchable session history for long-running loops.
- `DOUBTS.md`: unresolved questions and grill points.
- `plan/main_plan.md`: product-level plan updates.
- `plan/`: step-level product plan updates.
- `CURRENT_STATE.md`: current phase/gate/product repo status.
- `HANDOFF.md`: exact next action for the next agent.
- `COMPACT.md`: compact context summary for long loops and tool switches.
- `DEPLOYMENT_PLAN.md`: cloud, LLM, CI/CD, and production deployment plan updated at loop closeout.
- `.ai/SESSION_LOG.md`: append-only session note.

Do not ask the user to manually transfer context between tools. Write the context into these files.

## External references

Use `tools/registry.md` for optional references and integrations. Do not add dependencies or tooling just because they are listed.

## Product repo

This directory is the **loop OS template**. A user's product repo may live in this repo or another repo, depending on `plan/main_plan.md` and `DECISIONS.md`.
