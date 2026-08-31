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
12. **Always-on lifecycle** - Before loop work: `loop session-start`. Before stopping: `loop session-end`. Read `plan/SESSION_MANIFEST.md` first. Works in any coding agent (Cursor, Claude, Codex, OpenCode, Grok, Cline, ...).
13. **Run to terminus, not to chunk** - A command cascades automatically through its downstream phases until its **terminus** or a **Stop Condition**. Never end a turn by telling the user to run a command you could have run. Reconcile whatever your work invalidates (gates, tasks, specs, decisions) in the same run. When you must stop, name the Stop Condition and what you need. See `docs/CONTINUATION.md`.
14. **Skills are the public interface** - Users invoke slash commands or describe the work in natural language. The `loop` shell is an internal deterministic runtime bridge for agents, installers, diagnostics, and compatibility. Agents run required runtime operations themselves and never assign them to the user. See `docs/INTERNAL_RUNTIME.md`.
15. **Scope before writing** - In a workspace with `plan/products/`, every command resolves *which sub-product* it is about before reading a plan or writing a file: `loop scope resolve --text "<what the user typed>"`. Exit `2` means **ask the user** - never treat an unnamed sub-product as shared platform work. Announce the resolved scope. A change needed in another sub-product is located, asked about, then applied there. See `docs/SCOPES.md`.
16. **One workspace** - Sub-products are **scopes** in this workspace (`plan/products/<slug>/`), including sub-products whose code lives in another repo. There is no second workspace to sync, and no parent/child link to maintain. `/scope` lists, switches, checks contracts, and folds in a sub-product that still has its own `.loop-engineer/`. See `docs/SCOPES.md`.

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
| **Start** | Recall → bidirectional tree sync → manifest → auto-skills → read manifest |
| **Work** | Follow active command (`/plan-loop`, `/develop-product`, etc.) |
| **End** | Reconcile/converge → bidirectional tree sync → update handoff/memory → log `state.db` |

Details: `docs/SESSION_LIFECYCLE.md` + `skills/session-lifecycle/SKILL.md`.

User does **not** run these manually - the agent runs them, and closeout writes this
workspace's memory itself.

Two things that used to be the user's chore are now raised **in the session**, as
questions with a recommended answer, by `/plan-loop`, `/develop-product`,
`/loop-engine` and `/revise-plan`:

| | Command | What it raises |
|---|---------|----------------|
| Blocking questions in `DOUBTS.md` | `loop doubts ask` → `loop doubts resolve <id> "<answer>"` / `loop doubts defer` | One parser owns the file; the `Default if unavailable` field is the recommendation |

Never tell the user to go run these - run them, ask the question, act on the answer
(`docs/CONTINUATION.md`). `loop pending` is now only the opt-in `--stage` memory path.

`loop doubts ask` asks **one round**: the blocking questions whose prerequisites are
settled, each numbered with its recommended answer. A doubt's `Depends on:` puts it in a
later round; its `Ask:` sends it to somebody who is not here, via
`loop doubts questionnaire`. See `skills/plan-loop/phases/grill.md`.
In a scoped workspace, ordinary doubt commands read the shared platform plus the selected
scope. `/resolve-doubts` is the plan-wide exception and uses `--all-scopes`; every resolution
is written back to the canonical file that owns its id.

Two more channels report themselves into `plan/SESSION_MANIFEST.md`, so nobody has to
remember a command:

| | Command | What it raises |
|---|---------|----------------|
| The plan stopped using its own words | `loop glossary` | Where a synonym displaced by `CONTEXT.md` `## Language` is still in use |
| The plan's fog is not clearing | `loop fog` → `loop fog promote <n>` | `## Not yet specified` patches that have sat unchanged - now either a stateable question or work you have decided against |

## App root resolution

Commands and skills reference app files (`AGENTS.md`, `commands/`, `skills/`,
`templates/`, `scripts/`) **relative to the app root**. Resolve it in this order:

1. **Router skill** from a coding agent's skills dir — the router names the app
   root explicitly; if that path is missing, run `loop home` (app = `<home>/app`).
2. **Direct checkout** — you are already inside the app; use relative paths.

The app root holds the runtime only. Product state always lives in the active
workspace (local `.loop-engineer/` or `~/.loop-engineer/data/`), never in the app.

## Portable Commands

The user should be able to type these commands in Cursor, Codex, Claude Code, Grok Build, OpenCode, Cline, or any other coding agent with filesystem access. Do not ask the user to paste boot prompts.

| Command | Meaning | First file to read |
|---------|---------|--------------------|
| `/setup-loop-engine` | First-time setup: register product workspace and seed missing product-state files | `commands/setup-loop-engine.md` + `skills/setup-loop-engine/SKILL.md` |
| `/plan-loop` | Run Step 1: brainstorm, grill, fact-check, evidence, PRD, architecture, and task planning | `commands/plan-loop.md` + `skills/plan-loop/SKILL.md` |
| `/startup-discovery-loop` | Alias for `/plan-loop` | `commands/plan-loop.md` + `skills/plan-loop/SKILL.md` |
| `/revise-plan` | Correct or add detail to a plan that already exists - agent routes the edit to the right file from full plan context | `commands/revise-plan.md` + `skills/revise-plan/SKILL.md` |
| `/ask-loop` | Answer a question about the existing plan or build from full context (reads product code when needed); read-only, cites sources | `commands/ask-loop.md` + `skills/ask-loop/SKILL.md` |
| `/develop-product` | Run Step 2: build product from the approved plan, with QA/security/compliance/CI/CD gates | `commands/develop-product.md` + `skills/develop-product/SKILL.md` |
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
| `/resolve-doubts` | Interactively clear all open doubts/blockers plan-wide, then give a go/no-go for development | `commands/resolve-doubts.md` + `skills/plan-loop/phases/resolve-doubts.md` |
| `/feature-converge` | Post-build drift check vs spec/tasks | `commands/feature-converge.md` + `skills/feature-converge/SKILL.md` |
| `/eval-loop` | Score the product's golden cases, record the run, find regressions, and let the failure pattern decide what to build next | `commands/eval-loop.md` + `skills/eval-loop/SKILL.md` |
| `/product-tree` | Show main product ⇄ sub-product workspaces, their roll-up, and where a sub-product's plan contradicts the master plan | `commands/product-tree.md` + `skills/product-tree/SKILL.md` |
| `/deploy` | Deploy to the chosen cloud and record every resource created - what it serves, which environment, and how to remove it. Also answers "what can I delete?" | `commands/deploy.md` + `skills/deploy/SKILL.md` |
| `/scope` | Sub-products planned and built inside **one** workspace (`plan/products/<slug>/`): list, switch, check cross-scope contracts, and absorb a sub-product that still has its own `.loop-engineer/` | `commands/scope.md` + `skills/scope/SKILL.md` |
| `/ultraplan-loop` | Deep per-step planning for platform-scale products | `commands/ultraplan-loop.md` + `skills/plan-loop/phases/ultraplan.md` |
| `/frontend-animation` | Route to built-in GSAP, Motion.dev, and 3D core skills for frontend work | `commands/frontend-animation.md` + `skills/frontend-animation/SKILL.md` |
| `/agent-builder` | Design/scaffold an AI agent (or agentic/dynamic workflow) as the product itself - auto-activates in `/plan-loop` and `/develop-product` | `commands/agent-builder.md` + `skills/agent-builder/SKILL.md` |
| `/research-search` | Search arXiv, Research Square, and SSRN to ground a claim in evidence | `commands/research-search.md` + `skills/research-search/SKILL.md` |
| `/diagnose-loop` | Diagnose a bug or performance regression - build a feedback loop that goes red on it first, hypothesise second | `commands/diagnose-loop.md` + `skills/diagnose-loop/SKILL.md` |

If a tool does not support slash commands natively, interpret a plain user message containing one of the commands as a request to read the matching command file and execute it.

## Canonical Skill Pack

`skills/` is the source of truth for skills across all tools.

Tool-specific files are adapters only:

- `CLAUDE.md`
- `CURSOR.md`
- `CODEX.md`
- `OPENCODE.md`
- `GROK.md`
- `PI.md`
- `CLINE.md`

Do not put canonical logic only in a tool-specific folder.

## Product Plan Files

Product-specific planning belongs here:

- `plan/main_plan.md`: full product plan for the current user.
- `plan/`: root-owned step/module plans such as `plan/step_01_<module>.md`.
- `plan/products/<slug>/`: a sub-product's ultraplan pack, with its own `steps/` and `features/`.
- `plan/features/`: one folder per buildable feature (`spec.md`, `feature-plan.md`, `tasks.md`). Active pointer: `.loop/active-feature.json`.

Reusable loop mechanics belong in `skills/` and `commands/`.

## Feature workflow (built-in)

During `/plan-loop`, detect scale (`loop plan-loop scale --write`). **Convenient** → standard step + feature spec. **Platform** → `PRODUCT_MAP.md` + an ultraplan pack at each row's canonical owner: sub-products in `plan/products/<slug>/`, root-owned work in `plan/steps/NN-slug/` (`skills/plan-loop/phases/ultraplan.md`).

```text
/feature-new → /spec-clarify → /spec-checklist → feature-plan → task-compiler → /develop-product → /feature-converge
```

Platform: `loop plan-loop ultraplan next` before feature spec for each step.

Details: `docs/FEATURE_WORKFLOW.md`, `docs/ULTRAPLAN.md` + `skills/feature-workflow/SKILL.md`.

## Stack defaults (unless DECISIONS.md says otherwise)

Use conservative defaults unless `plan/main_plan.md` or `DECISIONS.md` says otherwise. The agent should choose a stack based on the product, team, risk, and deployment needs rather than forcing one startup's stack.

## Agent roles (use explicitly in prompts)

`manifests/agents.json` is the machine-checkable source for role classes, canonical skills,
mutation authority, and builder/reviewer independence. Session start selects the minimum
roles deterministically and records them in `plan/AUTO_AGENTS.md`; do not preload every role.

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
- `skills/codebase-design/SKILL.md` when placing a seam or shaping an interface - the shared
  vocabulary the planner, the tests, and the review all use.
- `skills/tdd/SKILL.md` when writing tests - the bar `AGENTS.md` #10 is measured against.
- `skills/code-reviewer/SKILL.md` after code edits. Two axes, reported separately: Spec (does
  it do what the task asked?) and Standards (is it built the way this repo builds things?).
- `skills/diagnose-loop/SKILL.md` when something is broken and the cause is not obvious from
  the diff.

## Memory layout (tool vs data)

- **App** (`~/.loop-engineer/app/`): updatable tool runtime - update with `loop update`.
- **Global data** (`~/.loop-engineer/data/`): default memory when no local product folder is detected. Never mixed with `app/`.
- **Local data** (`<product-folder>/.loop-engineer/`): memories/, state.db, plan/main_plan.md - **auto-detected** when you work from that folder. A single hidden folder, kept out of the product's own code.

When you run `/plan-loop`, `/loop-engine`, or any loop command, Loop checks the current folder (and parents) for a `.loop-engineer/` data dir. If found, it uses `<that-folder>/.loop-engineer/`; otherwise it uses `~/.loop-engineer/data/`.

See `docs/DATA_LAYOUT.md`.

## Product hierarchy (main product + sub-products)

Local workspaces nest. A main product folder holding sub-product folders links them into
a tree (`<workspace>/.loop/workspace.json`, refreshed at every `loop session-start`):

- **Scopes** - each sub-product's plan lives at `plan/products/<slug>/`; its code lives wherever `scope.json` says, including another repo.
- **Contracts** - what one sub-product provides another lives in `plan/contracts/`, checked deterministically.
- **standalone** - the default; single-product behavior is unchanged.

Sub-products under the main folder are auto-discovered; ones elsewhere use
`/scope`. Deterministic contract checks compare what scopes declare against
each sub-product's real plan state.

**Write rule:** metadata (`.loop/workspace.json`) may be stamped into a sub-product;
product state (`DOUBTS.md`, `HANDOFF.md`, `plan/*`) is **never** written across
workspaces - it is staged into that sub-product's `.loop/pending/` and applied there with
`loop pending approve`.

See `docs/SCOPES.md`.

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
