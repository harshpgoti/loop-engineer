# Agent Architecture

Filled in by `skills/agent-builder/SKILL.md` during `/plan-loop` or `/product-develop` when the product is, or includes, an AI agent. Reuse answers already in `DECISIONS.md` - do not re-ask the user once recorded.

## Agent type

- [ ] Single agent, single tool loop
- [ ] Single agent, multiple tools
- [ ] Multi-agent (orchestrator + sub-agents)
- [ ] Workflow/graph (deterministic steps with an LLM node, not a free-running agent loop)

## Workflow shape

- Trigger: (user message / cron / webhook / event queue)
- Dynamic vs fixed: (does the next step depend on model output, or is the sequence fixed?)
- Long-running: (single request/response, or a session that persists across turns?)

## Model provider

- Provider / model: record the chosen provider:model pair for the agent product here (a product decision, logged in `DECISIONS.md`).
- Fallback chain (if any): record here.

## Tools

| Tool | Purpose | Destructive? | Requires approval? |
|------|---------|--------------|---------------------|
|      |         |              |                     |

## Memory

- Session memory: (none / in-context / external store)
- Long-term memory: (none / vector store / structured DB) - name the store and retention policy.

## Guardrails

- Human approval required for: (list destructive/high-risk actions per AGENTS.md rule 5)
- Rate limits / spend limits:
- Sandboxing / permission scoping for tool execution:
- PII/sensitive-data handling: see AGENTS.md rule 6

## Skills (this product's own agent skills, not Loop Engineer's)

Location: `agent/skills/<name>/SKILL.md` - see `templates/agent_skill.template.md` for the per-skill format.

| Skill | Trigger | Tools used |
|-------|---------|------------|
|       |         |            |

## Evaluation

- Golden cases / eval set location:
- Eval cadence: (per-PR / nightly / manual)
- Tie into `skills/qa-validation/SKILL.md` for the product's test suite.

## Evidence

Cite any research (arXiv / Research Square / SSRN via `skills/research-search/SKILL.md`, or vendor docs) that informed a non-obvious architecture choice, in `EVIDENCE_LOG.md`.

## Prior art consulted (read-only, not vendored)

- [ ] Checked the agent skill hubs in `tools/registry.md` for comparable skill patterns
- Notes:
