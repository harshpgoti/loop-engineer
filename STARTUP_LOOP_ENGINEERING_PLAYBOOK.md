# Loop Engineering Playbook

Operating summary for agents. Product details live in `plan/main_plan.md` and `plan/`; reusable loop behavior lives in `commands/`, `skills/`, and `GATES.yml`.

## Philosophy

| Prompt engineering | Loop engineering |
|--------------------|------------------|
| What do I tell the model? | What must it remember, verify, test, and hand off? |

Design patterns used in this OS:

- **Separated app and data** — updatable tool under `~/.loop-engineer/app/`, durable memory outside it
- **Gate-driven loops** — planning and build advance only when `GATES.yml` allows
- **Portable skills** — instructions in `skills/` with YAML frontmatter
- **Evidence before decisions** — claims land in `EVIDENCE_LOG.md`
- **Explicit handoff** — every session updates `HANDOFF.md` and memory files

## Two-Step Loop

### Step 1 — Discovery (`/plan`)

Initialize product → brainstorm → evidence → interviews → score → PRD → ADR → tasks

**Exit:** `G-INIT-01`, `G-DISCOVERY-*`, and `G-ARCH-01`

### Step 2 — Build (`/product-develop`)

Scaffold → platform → first product step → UI → QA → security → CI/CD → staging → pilot

**Exit:** `G-PILOT-01` (synthetic demo + design partner identified)

## CI/CD gates (product repo)

Every PR: lint, tests, security scans, typecheck where configured, migration tests when applicable.

Release: staging deploy, smoke, rollback drill, audit log check.

## Risk And Compliance Baseline

Industry-neutral template. Replace during `/plan` with product-specific requirements.

- Do not store secrets in git.
- Do not put sensitive data in logs, fixtures, screenshots, or prompts.
- Define retention and deletion requirements.
- Add access control and audit logs for private data.
- Get legal/compliance review for regulated domains.

## Research Pointers

Use primary sources and standards for product-specific evidence. Use arXiv and Research Square for architecture/eval patterns, not market sizing — `loop research "<query>"` (`skills/research-search/SKILL.md`) searches both plus SSRN, and cites into `EVIDENCE_LOG.md`.

## AI agent as the product

If the product itself is, or includes, an AI agent (chatbot, workflow automation, multi-agent system), `skills/agent-builder/SKILL.md` auto-activates during `/plan` and `/product-develop` — see `docs/AGENT_BUILDER.md`. It scaffolds `agent/AGENT_ARCHITECTURE.md`, `agent/skills/`, `agent/tools/`, `agent/evals/` and wires in `skills/model-providers/SKILL.md` for the model choice.

## Current Tasks

See `TASKS.yml`.
