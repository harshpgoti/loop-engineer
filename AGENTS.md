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
| `/research-search` | Search arXiv, Research Square, PubMed, and SSRN to ground a claim in evidence | `commands/research-search.md` + `skills/research-search/SKILL.md` |
| `/diagnose-loop` | Diagnose a bug or performance regression - build a feedback loop that goes red on it first, hypothesise second | `commands/diagnose-loop.md` + `skills/diagnose-loop/SKILL.md` |
| `/dev-team` | Run a preset four-persona parallel review (PM / Architect / Developer / QA) as analysis-only subagents; constructive complement to /council | `commands/dev-team.md` + `skills/dev-team/SKILL.md` |
| `/dynamic-workflow` | Design a task-local harness using the {Objective, Inputs, Loop, Eval, Handoff, Human_gate} template | `commands/dynamic-workflow.md` + `skills/dynamic-workflow-mode/SKILL.md` |
| `/adr` | Capture an architectural decision as a durable ADR with date, status, deciders, context, alternatives, and consequences | `commands/adr.md` + `skills/architecture-decision-records/SKILL.md` |
| `/api-design` | Apply REST/HTTP conventions: resources, methods, status codes, error envelopes, pagination, rate limiting, versioning | `commands/api-design.md` + `skills/api-design/SKILL.md` |
| `/error-handling` | Map internal exceptions to the public error envelope; typed errors, no stack traces, observability hooks | `commands/error-handling.md` + `skills/error-handling/SKILL.md` |
| `/decision-ledger` | Append a revisit to the recursive decision ledger; record prior winner, fresh evidence, search space, and outcome | `commands/decision-ledger.md` + `skills/recursive-decision-ledger/SKILL.md` |
| `/codebase-onboarding` | 4-phase onboarding (recon -> architecture -> convention detection -> ONBOARDING.md + CLAUDE.md patch) for a fresh or stale project | `commands/codebase-onboarding.md` + `skills/codebase-onboarding/SKILL.md` |
| `/inherit-legacy-style` | Codify a hand-written legacy codebase's style into `.ai-style-rules.md` (Golden Files, Naming, State, DONTs) | `commands/inherit-legacy-style.md` + `skills/inherit-legacy-style/SKILL.md` |
| `/plan-orchestrate` | Coordinate a multi-plan DAG run; sequence and parallelise, reconcile cross-scope contracts, emit ORCHESTRATION_LOG.md | `commands/plan-orchestrate.md` + `skills/plan-orchestrate/SKILL.md` |
| `/living-docs-governance` | Detect drift between documentation and code; deterministic checks; emit drift report + tasks | `commands/living-docs-governance.md` + `skills/living-docs-governance/SKILL.md` |
| `/loop-design-check` | 5-failure-mode review of a closed loop's design (verifiable done-criterion, boundaries, fallback, layering, external anchor) | `commands/loop-design-check.md` + `skills/loop-design-check/SKILL.md` |
| `/contract-first` | Design every cross-boundary contract as a single canonical artifact (OpenAPI / AsyncAPI / Protobuf / JSON Schema) with both-sides verification | `commands/contract-first.md` + `skills/contract-first/SKILL.md` |
| `/gateguard` | Enforce a release gate as a Stop hook; machine-verifiable checks block the agent from finishing | `commands/gateguard.md` + `skills/gateguard/SKILL.md` |
| `/strategic-compact` | Suggest /compact at phase boundaries (research->planning, planning->implementation, etc.) rather than arbitrary token thresholds | `commands/strategic-compact.md` + `skills/strategic-compact/SKILL.md` |
| `/agent-sort` | Classify the canonical skills/commands/agents/rules/hooks as DAILY vs LIBRARY via parallel subagent review passes with evidence tables | `commands/agent-sort.md` + `skills/agent-sort/SKILL.md` |
| `/agent-eval` | Head-to-head agent comparison on a YAML task suite in isolated git worktrees; pass rate, cost, time, consistency | `commands/agent-eval.md` + `skills/agent-eval/SKILL.md` |
| `/safeguard` | Apply the 6-bullet Prompt Defense Baseline when designing or reviewing any skill, agent, or prompt that handles user input or external content | `commands/safeguard.md` + `skills/safeguard/SKILL.md` |
| `/config-gc` | Walk the workspace, identify env vars / flags / config entries no longer referenced, emit a deletion report (proposal, not auto-delete) | `commands/config-gc.md` + `skills/config-gc/SKILL.md` |
| `/skill-scout` | Before creating a new skill, search the local pack and adjacent ecosystems for existing coverage; vet externals for malicious shell/writes | `commands/skill-scout.md` + `skills/skill-scout/SKILL.md` |
| `/hookify-rules` | Turn a one-off hook event into a reusable rule; verify positive / negative / regression before adoption | `commands/hookify-rules.md` + `skills/hookify-rules/SKILL.md` |
| `/self-audit` | Walk the LE app's own state: skill-policy vs capabilities consistency, command/skill reachability, harness compatibility, install-profile budget, role manifest consistency | `commands/self-audit.md` + `skills/chain-meta/SKILL.md` |
| `/roles` | List every role in the chain with class, model tier, skills, hand-off targets, and independence (uses `scripts/roles_list.py`) | `commands/roles.md` + `skills/chain-meta/SKILL.md` |
| `/skill-list` | List every skill in the chain with class, owning capability, and activation paths (uses `scripts/skill_list.py`) | `commands/skill-list.md` + `skills/chain-meta/SKILL.md` |
| `/onboard` | Print or open the Loop Engineer contributor onboarding guide (`docs/LE_ONBOARDING.md`) - the 60-minute introduction for new maintainers | `commands/onboard.md` + `skills/contributor-onboarding/SKILL.md` |
| `/lint` | Run the project's linter (configured via `<workspace>/.loop/dev_config.json`) | `commands/lint.md` + `skills/dev-tooling/SKILL.md` |
| `/test` | Run the project's test suite (configured via `<workspace>/.loop/dev_config.json`) | `commands/test.md` + `skills/dev-tooling/SKILL.md` |
| `/format` | Format the project (configured via `<workspace>/.loop/dev_config.json`) | `commands/format.md` + `skills/dev-tooling/SKILL.md` |
| `/commit` | Stage and commit with a structured message that follows the conventional-commits template | `commands/commit.md` + `skills/dev-tooling/SKILL.md` |
| `/code-reviewer` | Run the two-axis review (Spec vs Standards) on the current diff; reports two axes, never re-ranks across them | `commands/code-reviewer.md` + `skills/code-reviewer/SKILL.md` |
| `/qa-validation` | Run unit, integration, E2E, golden, schema, and tenant-isolation checks; emit findings with the Pre-Report Gate | `commands/qa-validation.md` + `skills/qa-validation/SKILL.md` |
| `/security-compliance` | Run security and compliance review: secrets, sensitive data, tenant isolation, audit logs, prompt injection, IDOR | `commands/security-compliance.md` + `skills/security-compliance/SKILL.md` |
| `/data-engineering` | Run the data engineering review: data models, migrations, pipelines, quality, lineage, retention, tenant-safe access | `commands/data-engineering.md` + `skills/data-engineering/SKILL.md` |
| `/ml-engineering` | Run the ML engineering review: dataset versioning, training, evaluation, model registry, inference, monitoring, rollback | `commands/ml-engineering.md` + `skills/ml-engineering/SKILL.md` |
| `/operations` | Run the production operations review: observability, SLOs, incident response, backups, capacity, cost, recovery | `commands/operations.md` + `skills/operations/SKILL.md` |
| `/tdd` | Run the TDD discipline: RED -> GREEN -> REFACTOR with the test bar `AGENTS.md` #10 is measured against | `commands/tdd.md` + `skills/tdd/SKILL.md` |
| `/council-multi-model` | Run an external-model critique on a council decision with honest provider-relationship labels and explicit consent | `commands/council-multi-model.md` + `skills/council-multi-model/SKILL.md` |
| `/council` | Convene a four-voice council (Architect / Skeptic / Pragmatist / Critic) for ambiguous decisions; anti-anchored, locked output schema | `commands/council.md` + `skills/council/SKILL.md` |
| `/docs` | Create or update product documentation (main plan, step plans, PRDs, ADRs, API specs, runbooks, release notes, handoffs) | `commands/docs.md` + `skills/docs/SKILL.md` |
| `/feature-workflow` | Run the per-feature pipeline (spec -> clarify -> checklist -> feature-plan -> task compiler) for a single feature | `commands/feature-workflow.md` + `skills/feature-workflow/SKILL.md` |
| `/skill-list` | List every skill in the chain with class, owning capability, and activation paths (uses `scripts/skill_list.py`) | `commands/skill-list.md` + `scripts/skill_list.py` |
| `/roles` | List every role in the chain with class, model tier, skills, hand-off targets, independence (uses `scripts/roles_list.py`) | `commands/roles.md` + `scripts/roles_list.py` |
| `/revise-skill` | Revise an existing skill's SKILL.md safely: pre-edit checklist, edit, run audit, run tests, commit minimal diff | `commands/revise-skill.md` |
| `/latency-critical-systems` | Run the latency-critical design review: p99 budget, hot path, profile before/after, batching, caching, regression test in CI | `commands/latency-critical-systems.md` + `skills/latency-critical-systems/SKILL.md` |
| `/market-research` | Run market research: TAM/SAM/SOM with sources, competitor analysis, customer interview synthesis, positioning, kill criterion | `commands/market-research.md` + `skills/market-research/SKILL.md` |
| `/learn-curator` | Promote eligible observations to staged records (3+ sessions, 0.8+ confidence); runs at /session-end | `commands/learn-curator.md` + `skills/learn-curator/SKILL.md` |
| `/handoff` | Read or write the HANDOFF.md at any chain transition; the durable record that survives session boundaries | `commands/handoff.md` + `skills/handoff/SKILL.md` |
| `/living-docs-governance` | Detect drift between documentation and code; deterministic checks; emit drift report + tasks | `commands/living-docs-governance.md` + `skills/living-docs-governance/SKILL.md` + `scripts/living_docs_audit.py` |
| `/chain-bench` | Benchmark the chain's own state (skills, commands, roles, plan, tests, state.db); surface as Markdown + JSON | `commands/chain-bench.md` + `skills/chain-bench/SKILL.md` + `scripts/chain_bench.py` |
| `/lint` | Run the project's linter (configured via `<workspace>/.loop/dev_config.json`) | `commands/lint.md` + `scripts/dev.py` |
| `/test` | Run the project's test suite (configured via `<workspace>/.loop/dev_config.json`) | `commands/test.md` + `scripts/dev.py` |
| `/format` | Format the project (configured via `<workspace>/.loop/dev_config.json`) | `commands/format.md` + `scripts/dev.py` |
| `/commit` | Stage and commit with a structured message that follows the conventional-commits template | `commands/commit.md` + `scripts/dev.py` |
| `/chain-catalog` | Render the full chain surface (skills, commands, roles, capabilities, harnesses) as a single Markdown catalog page | `commands/chain-catalog.md` + `skills/chain-catalog/SKILL.md` + `scripts/chain_catalog.py` |
| `/codehealth-mcp` | Run a code-health snapshot of the active workspace (lint debt, test coverage, churn, dep freshness, doc coverage) | `commands/codehealth-mcp.md` + `skills/codehealth-mcp/SKILL.md` |
| `/iterative-retrieval` | Run a three-round retrieval loop against a corpus; each round refines the query from the prior round's results | `commands/iterative-retrieval.md` + `skills/iterative-retrieval/SKILL.md` |
| `/competitive-platform-analysis` | Run a structured competitive analysis (direct / indirect / substitute competitors, wedge, positioning) | `commands/competitive-platform-analysis.md` + `skills/competitive-platform-analysis/SKILL.md` |
| `/automation-audit-ops` | Audit every automation the chain runs (CI, hooks, scripts, harnesses) for stale, unowned, or risky automations | `commands/automation-audit-ops.md` + `skills/automation-audit-ops/SKILL.md` |
| `/parallel-execution-optimizer` | Decide whether a multi-step task should run sequentially or in parallel; emit a parallel plan | `commands/parallel-execution-optimizer.md` + `skills/parallel-execution-optimizer/SKILL.md` |
| `/dashboard-builder` | Build a self-contained HTML dashboard from a YAML spec (no JS frameworks, no CDN) | `commands/dashboard-builder.md` + `skills/dashboard-builder/SKILL.md` |
| `/bench-history` | Record and diff chain benchmarks over time; emit trend deltas against the prior snapshot | `commands/bench-history.md` + `skills/bench-history/SKILL.md` + `scripts/bench_history.py` |
| `/harness-catalog` | Consolidate the per-coding-agent harness JSON files into a single discoverable view | `commands/harness-catalog.md` + `skills/harness-catalog/SKILL.md` + `scripts/harness_catalog.py` |
| `/code-simplifier` | Read-then-edit refactor that preserves behavior; targets complexity, dead branches, unclear names | `commands/code-simplifier.md` + `skills/code-simplifier/SKILL.md` |
| `/comment-analyzer` | Verify comment accuracy and staleness; 4 buckets (Inaccurate / Stale / Incomplete / Low-value) | `commands/comment-analyzer.md` + `skills/comment-analyzer/SKILL.md` |
| `/performance-optimizer` | Algorithmic complexity + Web Vitals + bundle analysis; profile before/after, CI test | `commands/performance-optimizer.md` + `skills/performance-optimizer/SKILL.md` |
| `/refactor-cleaner` | Dead-code hunter (knip / depcheck / ts-prune); SAFE / CAREFUL / RISKY per category | `commands/refactor-cleaner.md` + `skills/refactor-cleaner/SKILL.md` |
| `/type-design-analyzer` | Score type design on 4 axes (Encapsulation / Invariant Expression / Usefulness / Enforcement) | `commands/type-design-analyzer.md` + `skills/type-design-analyzer/SKILL.md` |
| `/harness-optimizer` | Eval-driven harness tuning via pass@k / pass^k; BLOCKED on security-sensitive diffs | `commands/harness-optimizer.md` + `skills/harness-optimizer/SKILL.md` |
| `/pr-test-analyzer` | Test quality not test count; Critical / Important / Nice-to-have gap buckets | `commands/pr-test-analyzer.md` + `skills/pr-test-analyzer/SKILL.md` |
| `/conversation-analyzer` | Mine session transcript for corrections, repeated mistakes, prompt-injection attempts | `commands/conversation-analyzer.md` + `skills/conversation-analyzer/SKILL.md` |
| `/network-architect` | Design the network topology: subnets, firewall rules, DNS, load balancers, VPN, ingress, observability | `commands/network-architect.md` + `skills/network-architect/SKILL.md` |
| `/network-troubleshooter` | Read-only OSI-layer diagnosis; evidence-based root cause; narrow allow rules over disabling ACLs | `commands/network-troubleshooter.md` + `skills/network-troubleshooter/SKILL.md` |
| `/network-config-reviewer` | Audit running network device config (SSH v1, plaintext credentials, SNMP, NTP, AAA, Telnet, HTTP) | `commands/network-config-reviewer.md` + `skills/network-config-reviewer/SKILL.md` |
| `/recursive-decision-ledger` | Append a revisit to the recursive decision ledger; record prior winner, fresh evidence, search space, and outcome | `commands/recursive-decision-ledger.md` + `skills/recursive-decision-ledger/SKILL.md` |
| `/grill` | Run the structured interview (66 questions, 11 categories) from `skills/plan-loop/phases/grill.md` | `commands/grill.md` + `scripts/grill.py` |

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

Use these before major work. Each skill ships a discoverable command (or is
loaded as a phase file by the chain). When in doubt, run `/skill-list` to see
the full surface.

**Planning:** `/council` and `/council-multi-model` (adversarial), `/dev-team`
(constructive), `/adr` (decisions), `/plan-loop` with `grill.md`, `/plan-orchestrate`
(multi-plan), `/loop-design-check` (loop design), `/contract-first` (boundaries),
`/market-research` (early planning).

**Build:** `implementation-planner`, `codebase-design`, `tdd`, `code-reviewer`
(after edits, two axes), `diagnose-loop` (when broken).

**Quality / safety:** `safeguard` (prompt defence), `security-compliance`
(release), `qa-validation` (after build), `operations` (SLOs/rollback),
`latency-critical-systems` (latency SLOs), `gateguard` (release gate
enforcement), `living-docs-governance` (docs drift).

**Release / chain maintenance:** `release-check` (pre-launch), `prod-gap`
(production blockers), `deployment-plan` (deploy targets), `self_audit.py` /
`/self-audit` (LE-app self-check), `skill_audit.py` (per-skill contract).

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
