# Loop Engineering OS

**Loop engineering, not prompt engineering.** A durable, open-source operating system for planning and building products across Codex, Claude Code, Cursor, Grok Build, OpenCode, and direct LLM APIs.

## Three master loops

| Loop | Skill / command | Purpose |
|------|-----------------|--------|
| **Step 1 - Planning** | `/plan-loop` or skill `skills/plan-loop` | Initialize product → brainstorm → fact-check → PRD → architecture → task breakdown |
| **Step 2 - Build** | `/product-develop` or skill `skills/product-develop` | Implement → review → QA → security/compliance → CI/CD → deploy |
| **All-in-one** | `/loop-engine` or skill `skills/loop-engine` | Route between planning, task compilation, development, QA, and release gates |

Everything else in this repo (model providers, AI-agent-development scaffolding, research search, feature specs, frontend animation, deployment, release checks, ...) is auto-detected and wired into these three - see [`docs/PROCESS.md`](docs/PROCESS.md) and the full command table in [`AGENTS.md`](AGENTS.md).

## Quick start (any agent)

### One-liner install (GitHub)

**Windows:**

```powershell
irm https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.ps1 | iex
```

**macOS / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/harshpgoti/loop-engineer/main/install.sh | bash
```

Then open your agent in `%USERPROFILE%\.loop-engineer\app` (Windows) or `~/.loop-engineer/app` (macOS/Linux) and run `/plan-loop`.

Full install options: [`INSTALL.md`](INSTALL.md).

### Manual central-tool setup

```text
Main/
├── loop-engineer/
└── product/
```

Open the agent in `loop-engineer/`, then register the product workspace once:

```text
/setup-loop-engine
```

Use:

```text
/setup-loop-engine
/plan-loop
/product-develop
/loop-engine
```

Agents should interpret these commands by reading `commands/` and `skills/`. On first run, `/plan-loop` initializes the user's product data automatically into `plan/main_plan.md`, `plan/`, `memories/MEMORY.md`, `DOUBTS.md`, and `TASKS.yml` - all inside the workspace data root, never inside the tool repo.

In central-tool setup, those product files are written to the registered product workspace, not into `loop-engineer/`.

`AGENT_BOOT_SEQUENCE.md` is now only a fallback for tools that do not auto-read repo instructions.

For install/copy instructions, see [`INSTALL.md`](INSTALL.md).
For central-tool vs embedded setup, see [`docs/WORKSPACES.md`](docs/WORKSPACES.md).
For data layout and auto-detection, see [`docs/DATA_LAYOUT.md`](docs/DATA_LAYOUT.md).

## Memory layer

These live in the **workspace data root** (`~/.loop-engineer/data/` or `<product-folder>/.loop-engineer/`) - created at setup from [`templates/starter/`](templates/starter/). The tool repo carries no live state files.

| File | Purpose |
|------|---------|
| `memories/MEMORY.md` | Human-mind progress: what happened, what is happening, what is next |
| `memories/USER.md` | User profile and durable preferences |
| `memories/SOUL.md` | Agent voice/behavior for this product |
| `DOUBTS.md` | Open user questions and grill points |
| `plan/main_plan.md` | Full product plan for the current user |
| `plan/` | Per-step product plans |
| `CURRENT_STATE.md` | What is true right now |
| `TASKS.yml` | Active backlog |
| `DECISIONS.md` | Decision log |
| `EVIDENCE_LOG.md` | Source-backed claims only |
| `HANDOFF.md` | Next agent instructions |
| `GATES.yml` | Hard stop/go criteria per phase |

## Always-on session lifecycle

Every agent session that touches the product runs this, in any tool:

```bash
loop session-start --command "<slash-command>" --tool "<tool>"
# read plan/SESSION_MANIFEST.md
# ... do the work ...
loop session-end --summary "<progress>"
```

This is what makes memory durable across chat sessions and tool switches - see
[`docs/SESSION_LIFECYCLE.md`](docs/SESSION_LIFECYCLE.md). The agent runs it, not the user.

## Command Usage

In order of a real product journey - every command works the same in Cursor, Claude Code, Codex, OpenCode, Grok Build, or a direct LLM with filesystem access.

### 0. Set up once

```bash
/setup-loop-engine            # in your agent - registers the workspace, seeds starter files
loop setup                    # same thing from the terminal (global data: ~/.loop-engineer/data/)
loop setup --use-cwd --name my-app                  # local data: ./my-app/.loop-engineer/
loop setup --use-cwd --source /path/to/other-tool          # import MEMORY/USER/skills from another AI tool
loop setup --use-cwd --source /path/to/other-tool --scan   # different structure? classify every file by content
loop model setup              # optional: pick the LLM provider for API-hosted inference
```

### 1. Plan - `/plan-loop`

```text
/plan-loop
/plan-loop an AI receptionist for dental clinics that answers calls and books appointments
```

Initializes the product on first run (asks name, target user, problem, first step, deployment targets), then: grill → product council → fact-check → PRD → architecture → feature spec → task compiler. Auto-detects platform-vs-convenient scale and routes `/ultraplan-loop` when needed.

### 2. Build - `/product-develop` (alias: `/develop-product`)

```text
/product-develop
```

Builds from the approved plan, one task at a time: implementation plan → smallest safe diff → tests → code review → QA → security/compliance → docs → prod-gap. Frontend motion/3D and AI-agent work auto-route to the right built-in skills.

### 3. All-in-one - `/loop-engine`

```text
/loop-engine
/loop-engine a marketplace for local tutors with escrow payments
```

The primary entry point: routes between planning and development based on gates - give it an idea and keep re-running it.

### Product & planning helpers

```text
/agent-builder        # design/scaffold an AI agent as the product - auto-activates in /plan-loop + /product-develop
/research-search      # search arXiv / Research Square / SSRN, e.g. loop research "multi-agent evaluation"
/model                # AI provider config, e.g. loop model anthropic:<model-id>, loop model doctor
/feature-new          # new feature spec folder, e.g. loop feature new "auth login" --step plan/step_01.md
/spec-clarify         # structured clarification on the active feature spec
/spec-checklist       # spec quality gate before feature-plan
/feature-converge     # post-build drift check vs spec/tasks
/ultraplan-loop            # deep per-step planning for platform-scale products
/frontend-animation   # route to built-in GSAP / Motion.dev / 3D skills
```

### Operations & maintenance

```text
/status               # snapshot: workspace, gate, task, blockers, next command
/doctor               # health-check runtime + workspace
/prod-gap             # launch-gap analysis into plan/PROD-GAP.md
/sync-loop-state      # reconcile MEMORY / HANDOFF / TASKS / GATES drift
/deployment-plan      # write or refresh DEPLOYMENT_PLAN.md
/release-check        # pre-production readiness check
/compact-loop         # durable context summary before long runs or tool switches
/migrate-import       # import another tool's data after setup; add --scan to classify arbitrary files by content
/upgrade-loop-engineer  # update tool files without touching product data
```

### Session lifecycle (agents run these, not you)

```text
/session-start        # loop session-start - recall, manifest, auto-skills
/session-end          # loop session-end - memory review, staged writes, state.db log
/session-recall       # recall only (normally inside session-start)
/memory-review        # memory curation only (normally inside session-end)
```

Full, current list: [`AGENTS.md`](AGENTS.md)'s Portable Commands table, or the plain list in [`LOOP_COMMANDS.md`](LOOP_COMMANDS.md).

For recurring Cursor work:

```text
/loop 2h /loop-engine
```

## Cross-Tool Adapters

| Tool | Entry |
|------|-------|
| Cursor | `CURSOR.md`, `AGENTS.md` |
| Claude Code | `CLAUDE.md`, `AGENTS.md` |
| Codex | `CODEX.md`, `AGENTS.md` |
| OpenCode | `OPENCODE.md`, `AGENTS.md` |
| Grok Build | `GROK.md`, `AGENTS.md` |
| Direct API | `API_USAGE.md` |

Canonical skills are in `skills/`; adapter files must stay thin.

## First-Run Behavior

When someone downloads this repo and runs `/plan-loop`, the agent must:

1. Detect whether `plan/main_plan.md` is still uninitialized.
2. Ask for product name, target user, problem, constraints, and first product step.
3. Ask for deployment targets during planning: cloud provider, single vs multi-cloud, LLM provider/model, and related infrastructure choices.
4. If the user is unavailable, record questions in `DOUBTS.md`.
5. Create or update `plan/step_01_<slug>.md`.
6. Update `memories/MEMORY.md`, `TASKS.yml`, `GATES.yml`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.

No product-specific data should be committed to this template repo.

Agents may use:

```bash
python scripts/init_product.py --name "<product>" --first-step "<step>" --target-user "<user>" --problem "<problem>"
```

To validate the template before publishing:

```bash
python scripts/validate_template.py
```

## Full playbook

See [`STARTUP_LOOP_ENGINEERING_PLAYBOOK.md`](STARTUP_LOOP_ENGINEERING_PLAYBOOK.md) for architecture, stack, CI gates, and compliance baseline.

See [`docs/PROCESS.md`](docs/PROCESS.md) for the `/plan-loop`, `/product-develop`, and `/loop-engine` process architecture.

## Quality Checks

```bash
python scripts/validate_template.py
python scripts/validate_outputs.py --workspace <your-product-workspace>
python scripts/doctor.py
python scripts/detect_workspace.py
python scripts/migrate_workspace.py --list
```

## Operations Commands

See **Operations & maintenance** in Command Usage above. After upgrading the runtime, apply workspace migrations:

```bash
python scripts/migrate_workspace.py --workspace ../product
```

## Long Context / Tool Switching

Use:

```text
/compact-loop
```

This updates `COMPACT.md` so Codex, Claude Code, Cursor, OpenCode, Grok Build, or a direct API agent can continue without relying on chat history.

For parent workspace setup:

```bash
python scripts/compact_context.py
```

## Upgrading The Tool

Use:

```text
/upgrade-loop-engineer
```

See [`docs/UPGRADE.md`](docs/UPGRADE.md). The upgrade flow preserves product-state files like `plan/main_plan.md`, `plan/`, `memories/MEMORY.md`, `TASKS.yml`, `EVIDENCE_LOG.md`, and `HANDOFF.md`.

Rubrics:

- `evals/plan_quality_rubric.md`
- `evals/development_quality_rubric.md`
