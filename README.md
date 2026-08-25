# Loop Engineering OS

**Loop engineering, not prompt engineering.** A durable, open-source operating system for planning and building products across Codex, Claude Code, Cursor, Grok Build, OpenCode, and any other coding agent.

The public interface is the skill layer: type `/plan-loop`, `/develop-product`,
`/loop-engine`, or describe what you want in your coding agent. The installed `loop`
executable is an internal deterministic runtime bridge used by those skills; normal users
do not operate the product through a terminal CLI. See
[`docs/INTERNAL_RUNTIME.md`](docs/INTERNAL_RUNTIME.md).

## Three master loops

| Loop | Skill / command | Purpose |
|------|-----------------|--------|
| **Step 1 - Planning** | `/plan-loop` or skill `skills/plan-loop` | Initialize product → brainstorm → fact-check → PRD → architecture → task breakdown |
| **Step 2 - Build** | `/develop-product` or skill `skills/develop-product` | Implement → review → QA → security/compliance → CI/CD → deploy |
| **All-in-one** | `/loop-engine` or skill `skills/loop-engine` | Route between planning, task compilation, development, QA, and release gates |

Everything else in this repo (AI-agent-development scaffolding, research search, feature specs, frontend animation, deployment, release checks, ...) is auto-detected and wired into these three - see [`docs/PROCESS.md`](docs/PROCESS.md) and the full command table in [`AGENTS.md`](AGENTS.md).

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
/develop-product
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
| `CONTEXT.md` | Repo map, conventions, and `## Language` - the product's own words |
| `plan/main_plan.md` | Full product plan for the current user |
| `plan/` | Per-step product plans |
| `CURRENT_STATE.md` | What is true right now |
| `TASKS.yml` | Active backlog |
| `DECISIONS.md` | Decision log |
| `EVIDENCE_LOG.md` | Source-backed claims only |
| `HANDOFF.md` | Next agent instructions |
| `GATES.yml` | Hard stop/go criteria per phase |

## Always-on session lifecycle

Every agent session that touches the product runs the internal lifecycle, in any tool:

```bash
loop session-start --command "<slash-command>" --tool "<tool>"
# read plan/SESSION_MANIFEST.md
# ... do the work ...
loop session-end --summary "<progress>"
```

These are internal runtime calls shown for maintainers; the user does not run them. This is
what makes memory durable across chat sessions and tool switches - see
[`docs/SESSION_LIFECYCLE.md`](docs/SESSION_LIFECYCLE.md). The agent runs it, not the user.

## Questions get asked, not queued

Three things used to sit in a file waiting for someone to remember them. All three are now
raised in the session, with a recommended answer, by `/plan-loop`, `/develop-product`,
`/loop-engine` and `/revise-plan`.

**Doubts are asked in rounds.** A doubt can declare what it waits on:

```markdown
### DQ-009: Which PMS do we integrate first?
- **Status:** open
- **Blocking:** yes
- **Depends on:** DQ-005
- **Default if unavailable:** Whichever the design partner already runs.
```

Without that line this gets asked in the same breath as DQ-005, and the only honest answer is
"ask me again once I have a partner". With it, the round holds DQ-009 back and says what it is
waiting on. Answering **or deferring** DQ-005 advances the frontier - going with the default is
a decision. A prerequisite written only in prose gets caught by `loop doubts lint`.

**Questions that are not yours to answer leave the critical path.** Mark one
`- **Ask:** the clearinghouse rep` and `loop doubts questionnaire` writes their questions out as
a document to send, with the assumption we proceed on if nobody replies.

**A parent product's disagreements** are derived fresh every session from both plans and asked
the same way, never queued. See [`docs/SCOPES.md`](docs/SCOPES.md).

## What the plan knows it does not know

A plan has three kinds of unknown, and each has somewhere to live:

| | Where | |
|---|---|---|
| A question you can state | `DOUBTS.md` | Asked in rounds, with a recommendation |
| A decision you can see coming but cannot yet phrase | `plan/main_plan.md` → `## Not yet specified` | Timed; chased once it stops clearing |
| Work you have ruled out | `plan/main_plan.md` → `## Out of scope` | Never graduates - stops it being re-suggested |

The test for the middle one is whether you can **state** it precisely now, not whether you can
answer it. Fog is meant to clear, so it is timed from when the patch first appeared: after 28
days the session manifest says so, and the active planning command either promotes it to a
real question or records it as work deliberately ruled out.

## The product's own words

`CONTEXT.md` gets a `## Language` section: one opinionated name per concept, and the synonyms
it displaces.

```markdown
**Denial**
A claim the payer adjudicated and refused to pay.
_Avoid_: rejection, decline
```

The internal glossary validator counts where a displaced synonym is still used across the plan, most-entrenched
first, and surfaces it in the session manifest. It **reports and never rewrites** - when two
words turn out to name different things the answer is two definitions, not a rename, and that
call is yours.

## Use in your coding agent

In order of a real product journey - every command works the same in Cursor, Claude Code, Codex, OpenCode, Grok Build, or any other coding agent with filesystem access.

### 0. Set up once

```text
/setup-loop-engine            # registers this workspace and seeds starter files
/migrate-import               # imports memory/skills from another tool when needed
```

### 1. Plan - `/plan-loop`

```text
/plan-loop
/plan-loop an AI receptionist for dental clinics that answers calls and books appointments
```

Initializes the product on first run (asks name, target user, problem, first step, deployment targets), then: grill → product council → fact-check → PRD → architecture → feature spec → task compiler. Auto-detects platform-vs-convenient scale and routes `/ultraplan-loop` when needed.

Grilling happens in **rounds**. Each round is the set of questions whose prerequisites are
already settled, numbered, every one carrying a recommended answer. Questions that depend on
an answer you have not given yet wait for the next round instead of being asked early - see
[Questions get asked, not queued](#questions-get-asked-not-queued).

### 2. Build - `/develop-product` (alias: `/develop-product`)

```text
/develop-product
```

Builds from the approved plan, one task at a time: implementation plan → smallest safe diff → tests → code review → QA → security/compliance → docs → prod-gap. Frontend motion/3D and AI-agent work auto-route to the right built-in skills.

Code review runs on two axes reported separately - **Spec** (does it do what the task asked?)
and **Standards** (is it built the way this repo builds things?) - because a change can pass
either while failing the other. A red test whose cause is not obvious routes to
`/diagnose-loop`.

### 3. All-in-one - `/loop-engine`

```text
/loop-engine
/loop-engine a marketplace for local tutors with escrow payments
```

The primary entry point: routes between planning and development based on gates - give it an idea and keep re-running it.

### Ask, revise, unblock

```text
/ask-loop             # answer a question about the plan or the build from full context - read-only, cites sources
/revise-plan          # correct or extend an existing plan; routes the edit to the right file
/resolve-doubts       # clear every open blocker plan-wide, then give a go/no-go for development
/diagnose-loop        # something is broken: build a loop that goes red on it, then hypothesise
/eval-loop            # score the product's golden cases, catch regressions, let the failures pick the next task
```

`/diagnose-loop` refuses to theorise before it can name one command it has already run that
drives the real code path and asserts the symptom. `/eval-loop` also runs itself after any
change to agent behaviour - a prompt, a model, a tool definition - which unit tests cannot see.

### Product & planning helpers

```text
/agent-builder        # design/scaffold an AI agent as the product - auto-activates in /plan-loop + /develop-product
/research-search      # search arXiv / Research Square / SSRN
/feature-new          # create and activate a numbered feature spec
/spec-clarify         # structured clarification on the active feature spec
/spec-checklist       # spec quality gate before feature-plan
/feature-converge     # post-build drift check vs spec/tasks
/ultraplan-loop            # deep per-step planning for platform-scale products
/frontend-animation   # route to built-in GSAP / Motion.dev / 3D skills
```

### Big product split into sub-products

A product too big for one folder gets a main folder with the master plan and sub-product
folders that plan and build on their own - each with its own `.loop-engineer/`:

```text
main-product/
├── .loop-engineer/            THE workspace - master plan + every sub-product's plan
│   └── plan/products/auth/    one sub-product: prd, steps, features, TASKS, GATES, DOUBTS
├── services/auth/             its code (or another repo entirely - scope.json says where)
└── apps/portal/
```

Sub-products under the main folder are found automatically. For one in another repo, tell
the agent “link ../billing as a sub-product” while using `/product-tree`. Working inside a sub-product still uses that
sub-product's workspace - the difference is that the main plan can now see them, and says
when a sub-product's plan contradicts it (conflicting cloud, datastore, or decision;
unmapped sub-product; missing contract). Corrections are **staged** into the sub-product
for approval, never written into it. Single-product workspaces are unaffected.

```text
/product-tree         # roles, roll-up, and where a sub-product's plan contradicts the master plan
```

A row typed `sub-product` in `plan/PRODUCT_MAP.md` is a statement that the work will live
from the row title (which is what `map_id` binds on), seeds the workspace, hands over the
row's step plan so it does not re-plan from nothing, and links both ends. It reports the
main-product tasks carrying the gate the row declares - and does not move them, because
the new workspace compiles its own.

### One workspace instead of many

The layout above gives every sub-product its own workspace, and everything that keeps the
two ends agreeing is a bridge across that boundary. A sub-product needing something from
*another* sub-product has no channel at all - it can only be reported as two plans
disagreeing.

The alternative is one workspace, with each sub-product as a **scope**:

```text
main-product/
├── .loop-engineer/plan/products/auth/     plan, tasks, gates, doubts - all of it here
├── .loop-engineer/plan/contracts/         what auth provides, and who consumes it
├── services/auth/                         its code
└── apps/portal/
```

Everything is run from the main folder, naming the sub-product in the command:

```text
/plan-loop start working on auth product
/develop-product continue the portal checkout flow
/scope                              # which sub-products exist, and which one is active
/scope check auth and portal            # contracts, blockers, cycles across sub-products
/scope absorb the auth-service folder   # fold its own workspace into this one
```

Or just say it: "work on the portal checkout flow", "merge the auth sub-product into the
main workspace".

A portal task can now be `blocked_by` an auth task, and a contract has one provider and
real consumers - so nothing needs syncing. Sub-products in **another repo** stay
federated, exactly as above. `/scope absorb` migrates an existing one and
`/scope eject` reverses it.

Details: [`docs/SCOPES.md`](docs/SCOPES.md)

Details of the federated model: [`docs/SCOPES.md`](docs/SCOPES.md)

### Deploying, and knowing what you created

`/develop-product` reaches deployment on its own once the release gate passes and the
plan names a real cloud - or say **"lets deploy this"** to go there now.

```text
/deploy                      # deploy the chosen environment to the chosen cloud
/deploy to staging
what did we create in AWS?   # the inventory, per environment
what can I delete?           # dev resources that have outlived their reason
```

Two things make it safe to repeat. It **reads the provider's current official docs**
before running any command rather than deploying from memory, and it **records every
resource the moment it is created** - what it serves, which sub-product, which
environment, and the command that removes it:

```text
| ID    | Env | Provider | Service | Resource       | Purpose               | Scope  |
| R-001 | dev | aws      | ECS     | denial-api-dev | denial engine API     | denial |
| R-002 | dev | aws      | RDS     | denial-db-dev  | application database  | denial |
```

That is what makes a temporary environment findable later. `dev` rows are treated as
disposable and are the ones offered for teardown; `prod` and `staging` never are.
Creating and deleting both stop and ask first - one question listing everything, with
costs, not a prompt per resource.

Details: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)

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
/session-start        # recall, manifest, auto-skills; normally automatic
/session-end          # memory review and state history; normally automatic
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
| Any other agent | `AGENTS.md` (portable interpretation) |

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

See [`docs/PROCESS.md`](docs/PROCESS.md) for the `/plan-loop`, `/develop-product`, and `/loop-engine` process architecture.

## How code gets built

Four reference skills the build loop loads when they apply. None of them needs a command -
the phase that needs one reads it.

| Skill | When it loads | What it settles |
|-------|---------------|-----------------|
| [`codebase-design`](skills/codebase-design/SKILL.md) | Placing a seam or shaping an interface | Shared words: module, interface, depth, seam, adapter, leverage, locality |
| [`tdd`](skills/tdd/SKILL.md) | Writing or reviewing tests | Which seam to test at, and the three ways a test ends up proving nothing |
| [`code-reviewer`](skills/code-reviewer/SKILL.md) | After code edits | Spec and Standards as separate axes, plus a twelve-smell baseline |
| [`diagnose-loop`](skills/diagnose-loop/SKILL.md) | A bug the diff does not explain | A feedback loop that goes red before any theory is allowed |

The bar `tdd` adds to "tests required" is mostly about the **tautological test** - where the
expected value is computed the way the code computes it, so the test passes by construction and
can never disagree with the code:

```python
expected = sum(i.price for i in items)      # recomputes the implementation
assert calculate_total(items) == expected   # proves nothing

assert calculate_total([{"price": 10}, {"price": 5}]) == 15   # an independent fact
```

## Quality Checks

Every check below is deterministic, and each one exists because something drifted without
anyone noticing: an unreachable command, an orphaned skill, a README five commits stale.

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

This updates `COMPACT.md` so Codex, Claude Code, Cursor, OpenCode, Grok Build, or any other agent can continue without relying on chat history.

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
