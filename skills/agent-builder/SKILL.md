---
name: agent-builder
description: Design and scaffold an AI agent (or agentic/dynamic workflow) as the product itself — architecture, tool/skill authoring convention, model provider, guardrails, and evals. Auto-activates during /plan-loop and /product-develop when agent-development signals are present; also runs for /agent-builder directly.
---

# Agent builder

Loop Engineer helps build **any product**; this skill activates when that product is, or includes, an AI agent — a chatbot, autonomous workflow, tool-using assistant, multi-agent system, or dynamic/branching automation. It is not about Loop Engineer's own operational skills (`skills/` at repo root) — it is about the agent **the user is building**.

## When this activates

Auto-detected by `scripts/agent_skill_router.py` from `TASKS.yml`, `plan/`, `HANDOFF.md`, `DECISIONS.md`, and the current user message. Signals: "AI agent," "agentic," "workflow automation," "dynamic workflow," "chatbot," "copilot," "multi-agent," "tool-use," "RAG," "cron agent," and similar. See `plan/AUTO_AGENT_SKILLS.md` after running `loop auto-agent-skills --write`.

Also runs directly on `/agent-builder`.

## Read first

1. `plan/AUTO_AGENT_SKILLS.md` (if present)
2. `agent/AGENT_ARCHITECTURE.md` (if present — reuse decisions already recorded)
3. `DECISIONS.md`
4. `skills/model-providers/SKILL.md`
5. `skills/research-search/SKILL.md`
6. `skills/qa-validation/SKILL.md`

## Workflow

1. Run `loop auto-agent-skills --write` (usually already done by `/plan-loop` or `/product-develop`) and read `plan/AUTO_AGENT_SKILLS.md` for the detected agent shape.
2. If `agent/AGENT_ARCHITECTURE.md` does not exist yet, run `loop agent scaffold` — creates `agent/AGENT_ARCHITECTURE.md`, `agent/skills/`, `agent/tools/`, `agent/evals/` from `templates/agent_architecture.template.md` and `templates/agent_skill.template.md`.
3. Fill `agent/AGENT_ARCHITECTURE.md`: agent type (single/multi/workflow), trigger, tools, memory, guardrails, model provider, eval plan. Reuse anything already answered in `DECISIONS.md` — don't re-ask.
4. Pick the model provider via `skills/model-providers/SKILL.md` (`loop model setup` / `loop model <provider>:<model>`) — record the choice in `agent/AGENT_ARCHITECTURE.md` and `DECISIONS.md`.
5. For each distinct capability the agent needs, author a skill under `agent/skills/<name>/SKILL.md` (copy `agent/skills/_template/SKILL.md`). One skill = one trigger + one job — don't build a mega-skill.
6. For any tool the agent can call, document it under `agent/tools/` with its JSON schema and whether it is destructive. Destructive/high-risk tools require human approval per **AGENTS.md rule 5** — say so explicitly.
7. When a design choice is non-obvious (an eval methodology, a safety pattern, a memory architecture), ground it with `skills/research-search/SKILL.md` (arXiv / Research Square) and cite the source in `EVIDENCE_LOG.md` — don't assert it from vibes.
8. Optionally research comparable skill patterns in the agent skill hubs listed in `tools/registry.md` via `WebFetch` — **read-only reference, never vendor or install their packages.** Loop Engineer's own agent-skill format (SKILL.md frontmatter) is deliberately a portable shape so patterns transfer without a dependency.
9. Wire evals: golden cases under `agent/evals/`, tied into `skills/qa-validation/SKILL.md` — an agent PR should not merge on code review alone if agent *behavior* is what changed.
10. Update `TASKS.yml`, `DECISIONS.md`, `HANDOFF.md` with what was decided/built.

## Rules

- **No vendoring.** Do not install, clone, or import any external agent runtime's or marketplace's packages into the product. The skill hubs in `tools/registry.md` are inspiration, not a dependency.
- **Reuse, don't re-ask.** If `agent/AGENT_ARCHITECTURE.md` or `DECISIONS.md` already answers a question (model provider, agent type, guardrails), reuse it.
- **Human approval for destructive tools** — ties directly to AGENTS.md rule 5. Never let an agent auto-approve its own high-risk action.
- **Evidence for non-obvious claims** — architecture/eval/safety claims grounded in published work go through `skills/research-search/SKILL.md` and into `EVIDENCE_LOG.md`, not asserted from memory.
- **Same skill format Loop Engineer itself uses** (SKILL.md frontmatter: `name` + `description`) — the agent being built should be able to author, discover, and load its own skills the same way this repo does.
- **Tests required** — an agent's tool-calling behavior is code; it needs the same test/eval bar as everything else in AGENTS.md rule 10.

## Output

- `agent/AGENT_ARCHITECTURE.md` status (created/updated)
- Agent type + shape (single/multi-agent, RAG, scheduled, dynamic workflow)
- Model provider chosen
- Skills authored under `agent/skills/`
- Tools documented under `agent/tools/`, flagged destructive/approval-required ones
- Eval status
- Next command
