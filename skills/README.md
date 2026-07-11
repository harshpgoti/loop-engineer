# Skills

This folder is the canonical, tool-neutral skill pack.

Adapters for Cursor, Claude Code, Codex, OpenCode, Grok Build, and direct LLM API calls must point here. Do not make any tool-specific folder the source of truth.

## Skill Index

| Skill | Use |
|-------|-----|
| `setup-loop-engine` | First-time setup: register product workspace and seed missing state files |
| `plan` | Product planning, evidence, grilling, PRD, ADRs, task planning |
| `product-develop` | Product engineering: frontend, backend, DB, agents, QA, security, compliance, CI/CD |
| `loop-engine` | All-in-one loop: chooses planning or development based on gates |
| `prod-gap` | Analyze technical and non-technical product gaps into `plan/PROD-GAP.md` |
| `status` | Quick workspace/product/gate/task snapshot into `STATUS.md` |
| `doctor` | Health-check runtime and workspace into `DOCTOR.md` |
| `sync-loop-state` | Reconcile drift across memory, handoff, tasks, gates, and compact state |
| `release-check` | Pre-production release readiness check into `RELEASE_CHECK.md` |
| `deployment-plan` | Cloud/LLM/deployment plan into `DEPLOYMENT_PLAN.md` |
| `session-lifecycle` | Always-on session-start / session-end (any tool) |
| `session-recall` | Past session search (included in session-start) |
| `memory-review` | Memory curation (included in session-end) |
| `compact-loop` | Compact long-running context into `COMPACT.md` |
| `frontend-animation` | Single core skill for all frontend motion/3D/design - topic references (Motion, GSAP, Three.js, R3F, web design) auto-routed via `plan/AUTO_SKILLS.md` |
| `feature-workflow` | Feature spec folders under `plan/features/` |
| `spec-clarify` | Structured clarification on active feature |
| `spec-checklist` | Spec quality gate before feature-plan |
| `feature-converge` | Post-build drift check vs spec/tasks |
| `ultraplan` | Platform-scale deep planning per sub-product/agent |
| `migrate-import` | Import external workspace memory/skills into product paths |
| `upgrade-loop-engineer` | Safely update tool files while preserving product-state files |
| `agent-builder` | Design/scaffold an AI agent (or agentic/dynamic workflow) as the product itself |
| `research-search` | Search arXiv, Research Square, and SSRN to ground claims in evidence |
| `model-providers` | Configure AI model providers for API-hosted inference |
| `product-council` | Senior role review across strategy, PM, CTO, engineering, design, QA, security, release |
| `product-grill` | Ask hard product questions and track doubts |
| `task-compiler` | Convert plans into tasks, gates, acceptance criteria, and test plans |
| `implementation-planner` | Plan the smallest safe engineering diff before coding |
| `code-reviewer` | Review changes for correctness, tests, maintainability, and risk |
| `qa-validation` | Tests, evals, golden cases, post-development validation |
| `security-compliance` | Product-specific security, privacy, sensitive-data, and compliance reviews |
| `docs` | PRDs, ADRs, runbooks, API docs, handoffs |
| `cicd-release` | CI/CD, staging, rollback, deployment readiness |
| `tool-orchestrator` | Use supporting tools and external references inside the loop |

## Portable Command Mapping

| Command | Skill |
|---------|-------|
| `/setup-loop-engine` | `skills/setup-loop-engine/SKILL.md` |
| `/plan-loop` | `skills/plan-loop/SKILL.md` |
| `/product-develop` | `skills/product-develop/SKILL.md` |
| `/loop-engine` | `skills/loop-engine/SKILL.md` |
| `/prod-gap` | `skills/prod-gap/SKILL.md` |
| `/status` | `skills/status/SKILL.md` |
| `/doctor` | `skills/doctor/SKILL.md` |
| `/sync-loop-state` | `skills/sync-loop-state/SKILL.md` |
| `/release-check` | `skills/release-check/SKILL.md` |
| `/deployment-plan` | `skills/deployment-plan/SKILL.md` |
| `/compact-loop` | `skills/compact-loop/SKILL.md` |
| `/frontend-animation` | `skills/frontend-animation/SKILL.md` |
| `/feature-new` | `skills/feature-workflow/SKILL.md` |
| `/spec-clarify` | `skills/plan-loop/phases/spec-clarify.md` |
| `/spec-checklist` | `skills/plan-loop/phases/spec-checklist.md` |
| `/feature-converge` | `skills/feature-converge/SKILL.md` |
| `/ultraplan-loop` | `skills/plan-loop/phases/ultraplan.md` |
| `/migrate-import` | `skills/migrate-import/SKILL.md` |
| `/upgrade-loop-engineer` | `skills/upgrade-loop-engineer/SKILL.md` |
| `/agent-builder` | `skills/agent-builder/SKILL.md` |
| `/research-search` | `skills/research-search/SKILL.md` |
| `/manage-model` | `skills/model-providers/SKILL.md` |

## Adapter Rule

Every tool-specific adapter should be thin:

1. Read `AGENTS.md`.
2. Read the matching file in `skills/`.
3. Execute the command.
4. Update `memories/MEMORY.md`, `DOUBTS.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.

## Product-Specific Files

This skill pack is reusable. Product specifics live in:

- `plan/main_plan.md`
- `plan/`
- `EVIDENCE_LOG.md`
- `DECISIONS.md`
- `TASKS.yml`
