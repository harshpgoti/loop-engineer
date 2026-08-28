# ECC-Guided Loop Engineer Evolution Plan

**Status:** proposed for approval  
**Date:** 2026-08-28  
**ECC baseline:** `affaan-m/ECC@5eddf1a3ffd311423be2d4ba7d26f7209c91b033`  
**AgentShield baseline:** `affaan-m/agentshield@bdad15dd28da548a0586d6ca989cb5aa35a67ad6`

## Executive decision

Evolve Loop Engineer into a governed, harness-independent capability platform.
Adopt ECC's strongest control-plane patterns—manifest-selected capability packs,
deterministic hooks, command-to-capability mapping, trust-aware memory, independent
review verification, observable execution, and security evidence packs—while preserving
Loop's canonical product state, deterministic phase routers, evidence gates, scopes,
continuation contract, and human approval boundaries.

Do not copy ECC wholesale. Its breadth is useful evidence, but importing hundreds of
skills and harness-specific mirrors would recreate the duplication and context pressure
Loop's phase routing already avoids.

## Research method and evidence

The review traced architecture documents and manifests into representative commands,
skills, hooks, runtime code, tests, and the separate AgentShield implementation. Catalog
counts are descriptive, not a quality claim.

| Source | Evidence inspected | Finding used by this plan |
|---|---|---|
| [ECC repository](https://github.com/affaan-m/ECC/tree/5eddf1a3ffd311423be2d4ba7d26f7209c91b033) | 3,000+ files; 286 skill directories, 68 agent files, 94 command files in the pinned checkout | ECC is an agent operating system and distribution layer, not merely a prompt pack |
| [ECC 2.0 reference architecture](https://github.com/affaan-m/ECC/blob/5eddf1a3ffd311423be2d4ba7d26f7209c91b033/docs/ECC-2.0-REFERENCE-ARCHITECTURE.md) | Operator surface, adapters, worktree/session runtime, observability/evaluation, security platform | Separate operator, adapter, runtime, evidence, and policy planes |
| ECC install manifests | `manifests/install-components.json`, `install-modules.json`, `install-profiles.json` | Install capability bundles from data rather than hard-coded copy lists |
| ECC command/agent map | `docs/COMMAND-AGENT-MAP.md` | Make reachability and ownership machine-checkable |
| ECC hooks | `hooks/hooks.json`, hook scripts and tests | Hooks are deterministic lifecycle sensors; installation must prevent duplicate execution |
| ECC memory vault | `skills/unified-memory`, `scripts/memory.js`, MCP adapter | Memory must be scoped, create-only, searchable, validated, and explicitly untrusted |
| ECC learning loop | `continuous-learning-v2` | Capture observations separately from confidence-weighted candidate instincts; promotion is a gate |
| ECC review workflow | `workflows/orch-review.workflow.js` | Parallel dimensions, evidence-based deduplication, adversarial verification, fail-closed aggregation |
| ECC capability catalog | planning, TDD, repair, security, architecture, docs, frontend, data, ML, operations, research and domain skills | Route focused packs by repository/task signals; do not preload a universal catalog |
| [AgentShield repository](https://github.com/affaan-m/agentshield/tree/bdad15dd28da548a0586d6ca989cb5aa35a67ad6) | Scanner, 102-rule taxonomy, baselines, policies, runtime guard, fixes, SARIF, evidence packs and tests | Security needs structured findings, provenance/confidence, stable fingerprints, baselines and policy gates |

## Architecture assessment

### What Loop already does better

- One canonical `.loop-engineer/` product-state tree rather than separate execution,
  planning, and memory backlogs.
- Deterministic phase routing and progressive disclosure instead of loading an entire
  skill catalog.
- Explicit doubts, evidence, decisions, tasks, gates, scopes, contracts, and handoff.
- A command terminus that continues through downstream validation instead of returning
  a menu of manual next steps.
- Rules-first parsers and validators, with AI used after deterministic routing.
- Builder/reviewer separation and exact task acceptance criteria.
- Portable Python runtime and supported-harness routers rather than a Claude-only core.
- A new durable execution supervisor with worktrees, worker generations, events,
  validation runs, delivery authority, and fail-closed teardown.

### Gaps ECC exposes

| Gap in Loop | Consequence | ECC guidance |
|---|---|---|
| Installation is router-oriented, not capability-profile-oriented | Every installation exposes roughly the same product surface | Component/module/profile manifests with ownership and dry-run plans |
| No canonical capability registry | Commands, phases, skills, tests, risk triggers and owners are inferred across files | Command-agent-skill map plus catalog validation |
| Hooks are optional examples, not a governed subsystem | Lifecycle checks depend on agent compliance where harness hooks exist | Typed hook events, duplicate prevention, timeouts, output budgets and tests |
| Security is checklist-driven | Findings lack stable identity, confidence, baseline drift and portable evidence | AgentShield-style findings, SARIF, policies, baselines and evidence packs |
| Review is one separate pass | Duplicate findings and uncertain high-severity claims can block or pass inconsistently | Dimension fan-out, evidence deduplication and adversarial verification |
| Memory is bounded but mostly narrative | Trust, provenance, target harness and links are not first-class | Scoped create-only memory records with doctor/search/promote boundaries |
| Learning is manual | Repeated corrections do not become reviewable candidate rules | Observation -> instinct -> verify -> promote -> rollback |
| Status is human-oriented Markdown | Editors, dashboards and external supervisors lack one stable payload | Versioned local status/HUD JSON contract |
| Domain coverage is intentionally narrow | Loop cannot route deep language/framework/data/ML expertise automatically | Signal-selected capability packs with health/eval metadata |
| No capability quality lifecycle | A skill can exist without measured activation precision or outcome value | Catalog health, scenario fixtures, verifier results and promotion thresholds |

## Target architecture

```text
User / coding harness
        |
        v
Public workflow commands and natural-language routing
        |
        v
Capability registry + deterministic router
  command -> phase -> capability packs -> risk policies -> validation contract
        |
        +----------------------+-----------------------+
        v                      v                       v
Product control plane     Execution plane        Assurance plane
plans/scopes/tasks        workers/worktrees      review/security/evals
gates/evidence/memory     events/queues/status   policies/baselines/SARIF
        |                      |                       |
        +----------------------+-----------------------+
                               v
                    Versioned evidence + status API
                               |
                               v
                 Harness adapters / hooks / dashboards
```

Product truth remains in `.loop-engineer/`. Capability definitions live in the Loop app.
Execution records, observations, scan output, and review traces are derived evidence and
must never become a second product backlog or silently mutate canonical decisions.

## Core design decisions

### 1. Add a capability registry, not hundreds of unconditional skills

Create `manifests/capabilities.yml` as the canonical graph. Each capability declares:

- stable ID, version, owner and maturity;
- public triggers and deterministic signals;
- commands, skills, agents, rules, hooks and scripts it owns;
- supported harnesses and degradation behavior;
- dependencies and conflicts;
- context cost estimate;
- risk class and approval requirements;
- test/eval fixtures and validation commands;
- output contract and evidence artifacts.

Generate command tables, router indexes, install profiles, reachability checks and
capability-health reports from this graph. Existing Markdown remains the human-readable
implementation; the registry owns wiring, not prose.

### 2. Organize expertise into packs selected by task signals

Initial packs:

| Pack | Existing Loop base | Add from ECC guidance |
|---|---|---|
| `core-plan` | plan-loop, council, ultraplan, spec workflow | codebase pattern grounding and approval artifact |
| `core-build` | implementation planner, TDD, develop phases | explicit repair lane and verification checkpoints |
| `core-review` | Spec/Standards reviewer | review dimensions, deduplication and verifier contract |
| `core-assurance` | QA, security/compliance, release check | structured finding/baseline/policy/evidence output |
| `architecture` | codebase-design, ADR template | architecture audit, contract-first and migration design |
| `frontend` | auto-selected motion/design skills | accessibility, performance, browser QA and design-system checks |
| `backend-data` | generic build/QA | API, datastore, migrations, caching and data-pipeline patterns |
| `ai-ml` | agent-builder, eval-loop | ML workflow, model/data evaluation, cost and regression packs |
| `research-docs` | research-search, docs | deep research, iterative retrieval and living-doc governance |
| `operations` | CI/CD, deploy, prod-gap | containers, infrastructure, observability and incident readiness |
| `regulated` | security/compliance | healthcare/PHI first; add other domains only with evidence owners |

Packs must be progressive-disclosure layers. A detected language or framework adds one
small reference pack; it must not fork the core planning/build/review lifecycle.

### 3. Introduce a portable hook/event subsystem

Define versioned events independent of harness syntax:

- `session.start`, `session.end`, `context.pressure`;
- `tool.before`, `tool.after`, `tool.failure`;
- `file.changed`, `test.completed`, `review.completed`;
- `worker.state`, `permission.requested`, `external.action`.

Each hook declares matcher, timeout, side-effect class, input schema, output budget,
failure policy and supported adapters. Default hooks are observational or validation-only.
Mutating hooks require opt-in and a named rollback.

Harness adapters translate only supported events. Unsupported hooks degrade to explicit
workflow steps. Installation must detect duplicate hook ownership and refuse double
registration.

### 4. Build Loop Shield as an assurance layer

Start with an adapter to AgentShield for immediate coverage, then add Loop-native policy
for product-state and execution invariants.

Structured finding schema:

- stable fingerprint, rule ID/version and category;
- severity plus runtime confidence;
- source path/line and redacted evidence;
- active-runtime, project-optional, template, docs-example or plugin-cache provenance;
- safe autofix flag and rollback;
- policy owner, exception, expiry and approval;
- task/scope/gate linkage.

Outputs: terminal summary, JSON, SARIF 2.1, baseline comparison, remediation queue and a
redacted checksum-backed evidence pack. Security gates fail only on policy-relevant new
findings, regressions, invalid evidence or expired exceptions—not on raw catalog counts.

Never auto-fix destructive permissions, hooks, MCP servers, secrets history or policy
exceptions. Safe fixes require diff preview and tests.

### 5. Deepen memory without creating another truth store

Extend `state.db` and current Markdown memory with portable `loop.memory.v1` records:

- scope: project, product-scope, team or user;
- kind: context, lesson, handoff, correction or candidate-instinct;
- source harness/session/task and target harness;
- trust: unreviewed, verified, superseded or rejected;
- links to tasks, decisions, evidence and earlier records;
- sensitivity classification and retention policy.

Writes are create-only; corrections supersede. Search excludes rejected/superseded records
by default. Recalled memory is untrusted context. Promotion means updating a governed
artifact through its existing parser/gate—not changing a trust flag and treating prose as
policy. Never ingest raw transcripts automatically.

### 6. Upgrade review to Review -> Deduplicate -> Verify -> Decide

Keep Loop's Spec and Standards axes. Add optional dimensions selected by risk:

- language/framework correctness;
- security/privacy/tenant isolation;
- data/migration safety;
- performance/reliability;
- accessibility/UX;
- operations/release.

Every finding must cite an observable artifact and stable location. Deduplicate on
normalized evidence plus rule/fingerprint, not reviewer wording. Independently verify
Critical/High findings; uncertainty keeps a blocker open. A failed review dimension makes
the aggregate incomplete and cannot yield clean approval. Builder identity and exact commit
binding remain mandatory.

### 7. Create a deterministic repair lane

Add `/repair-loop` for build, type, lint, test, migration and CI failures:

1. reproduce the failure;
2. classify it deterministically;
3. establish the smallest red feedback loop;
4. patch one failure class at a time;
5. rerun the narrow check, then the affected suite;
6. route unclear regressions to `/diagnose-loop`;
7. record repair evidence and prevent recurrence.

This is a phase inside development, not a parallel backlog and not permission for broad
dependency upgrades.

### 8. Publish a versioned status and evidence interface

Add `loop status --format json` using `loop.status.v1`:

- workspace/scope/feature/task/gate;
- active command and phase;
- workers, queues, worktrees and liveness;
- checks, review and security posture;
- blockers and approvals;
- context/memory pressure;
- recent bounded events and evidence paths.

Markdown status becomes a renderer over the same payload. Editor plugins, dashboards and
external supervisors consume JSON; no hosted telemetry is required.

### 9. Add a governed learning loop

```text
bounded observation
  -> candidate instinct with scope/confidence/evidence
  -> scenario replay and verifier
  -> human review
  -> capability/rule/skill proposal
  -> staged promotion
  -> outcome monitoring
  -> retain or rollback
```

Capture corrections, repeated successful repairs, failure patterns and workflow friction;
do not capture source bodies, secrets or full prompts. No confidence score grants authority.
Promotion requires cross-session evidence, regression fixtures, an owner, an expiry/review
date and a rollback path. Project observations never become global automatically.

### 10. Make installation profile-driven and transactional

Profiles: `minimal`, `product`, `full`, plus explicit packs. Installer flow:

1. inspect harnesses and repository signals;
2. resolve capability graph and conflicts;
3. show dry-run plan and context/tool budget;
4. verify source checksums and versions;
5. apply transactionally with ownership manifest;
6. validate hooks/routers/config syntax;
7. smoke-test installed surfaces;
8. rollback on failure;
9. uninstall only owned files.

Do not mirror canonical logic into every harness. Generate thin adapters from the registry
and test their declared capability matrix.

## Phased delivery plan

### Phase 0 — Baseline and contracts

- Inventory every current command, skill, script, state artifact and harness adapter.
- Define capability, hook-event, finding, memory and status schemas.
- Add golden invalid fixtures and schema validators.
- Record ADRs for canonical truth, hook authority, memory trust and security exceptions.

**Gate:** schemas and reachability tests pass; no runtime behavior changes.

### Phase 1 — Capability registry and health

- Create the registry and compiler.
- Generate command/skill map and install profile previews.
- Add orphan, duplicate owner, dependency-cycle, unsupported-harness and context-budget checks.
- Backfill the existing 37 skills before adding new packs.

**Gate:** current behavior is reproduced from the registry with zero lost commands.

### Phase 2 — Verification and repair

- Implement structured review findings and aggregate verdict schema.
- Add risk-selected dimensions, evidence deduplication and independent verifier runs.
- Add `/repair-loop` and integrate it into the build-phase router.
- Bind review/repair artifacts to task ID and exact commit.

**Gate:** injected duplicate/false/failed-review fixtures fail closed correctly.

### Phase 3 — Security assurance

- Integrate AgentShield as an optional external scanner with pinned-version preflight.
- Implement Loop-native rules for agent instructions, hooks, MCP/config, secrets, worker
  authority, task/gate transitions and tenant/sensitive-data constraints.
- Add policies, baselines, SARIF, exceptions with expiry and evidence packs.
- Wire relevant results into release-check and session manifest.

**Gate:** false-positive corpus, redaction tests, SARIF fixtures and baseline regression tests pass.

### Phase 4 — Hook/event adapters

- Implement the canonical local event bus and append-only event store.
- Ship session lifecycle, formatting/check notifications and security preflight hooks first.
- Add Claude, Cursor, OpenCode and Codex adapters only where executable support is verified.
- Detect double registration and cap runtime/output.

**Gate:** adapter contract tests prove exact-once or idempotent behavior and safe degradation.

### Phase 5 — Memory vault and handoff

- Add `loop.memory.v1` storage/index/search/doctor.
- Migrate current session summaries as linked records without deleting existing Markdown.
- Add target-harness handoffs and explicit promotion into canonical artifacts.
- Add secret/regulated-data rejection and retention checks.

**Gate:** trust-boundary, duplicate-ID, broken-link, symlink, redaction and cross-scope tests pass.

### Phase 6 — Domain capability packs

- Add architecture, backend/data, frontend quality, AI/ML, research/docs and operations packs.
- Each pack starts with one golden scenario, one activation test and one measured outcome.
- Add regulated packs only with a named domain owner and evidence validity window.
- Extend auto-skill routing to select packs by source tree, task language and risk.

**Gate:** activation precision is measured; irrelevant packs remain unloaded.

### Phase 7 — Observability and operator surface

- Ship `loop.status.v1`, JSON/Markdown renderers and fixtures.
- Add worker/check/risk/context summaries and bounded notifications.
- Expose read-only adapters for editors or dashboards.

**Gate:** status is reconstructable after restart and contains no secrets or private prompts.

### Phase 8 — Governed learning

- Capture bounded observations through supported hooks.
- Generate candidate instincts with provenance and project scope.
- Build scenario replay, verifier and staged promotion/rollback.
- Add review UI only after the file/CLI contract proves useful.

**Gate:** bad and cross-project-contaminated proposals are rejected by fixtures.

### Phase 9 — Distribution hardening

- Transactional profile installer, uninstall and rollback.
- Signed/checksummed capability releases and compatibility matrix.
- Windows/Linux/macOS CI for core profiles and supported harnesses.
- Upgrade/migration tests from every supported prior manifest version.

**Gate:** clean install, upgrade, downgrade and uninstall leave no unowned mutations.

## Acceptance metrics

| Area | Measure |
|---|---|
| Routing | >=95% golden-task pack selection precision; zero unowned commands |
| Context | Minimal/product profiles stay within declared context and tool budgets |
| Review | Duplicate-finding reduction measured; all Critical/High findings independently verified |
| Security | Stable fingerprints; zero secret leakage in evidence packs; baseline regressions fail CI |
| Hooks | No duplicate execution; bounded latency/output; safe degradation on unsupported harnesses |
| Memory | No raw transcript ingestion; all promoted knowledge links to governed evidence |
| Learning | Zero automatic global promotion; every promoted behavior has verifier and rollback |
| Portability | Declared adapter matrix backed by executable tests, not documentation claims |
| Reliability | Restart-safe status/worker/event reconstruction and idempotent transitions |
| Distribution | Transactional install/update/uninstall across supported profiles |

## Explicit non-goals

- Importing ECC's full catalog or maintaining hundreds of duplicated framework skills.
- Making Claude Code the canonical runtime.
- Installing all hooks, MCP servers or tools by default.
- Treating memory, observations, agent output or security scores as product truth.
- Hosted telemetry, billing, social relay or enterprise dashboards before local contracts work.
- Autonomous policy/skill promotion based only on confidence or model judgment.
- A second task system, gate system, evidence log or memory database.

## Council review

| Role | Strongest concern | Required constraint |
|---|---|---|
| Product | Catalog breadth can obscure Loop's simple public workflow | Keep workflow commands stable and route packs invisibly |
| Architect | Parallel registries could split truth | One capability graph; existing product state remains canonical |
| Distinguished Engineer | Hundreds of shallow skills increase maintenance cost | Every pack needs activation and outcome evidence |
| QA | More automation can create green-but-unproven gates | Golden scenarios, failure fixtures and exact artifact binding |
| Security | Hooks, MCPs and learned rules expand executable attack surface | Opt-in mutation, provenance, policy owners, redaction and expiry |
| Release | Cross-harness claims drift quickly | Executable adapter matrix with dated evidence |

**Verdict:** proceed with constraints. Begin with Phase 0 and Phase 1; do not add domain
catalog breadth until the capability registry, health checks and context budgets enforce
quality and reachability.

## First implementation slice after approval

1. Add schemas for capability records and install profiles.
2. Encode the existing 37 skills and 33 public command files without changing behavior.
3. Generate a command -> phase -> skill -> script map.
4. Extend template validation with ownership, reachability, dependency-cycle and context-budget checks.
5. Add `loop capabilities list|explain|doctor` as an internal deterministic bridge.
6. Produce `minimal`, `product` and `full` dry-run install plans.
7. Run the complete current suite plus golden registry fixtures.

This slice creates the control plane that every later ECC-inspired capability depends on,
while remaining reversible and behavior-preserving.
