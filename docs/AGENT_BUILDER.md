# Agent builder

Loop Engineer can plan and build **any** product, including one that is, or includes, an AI agent — a chatbot, autonomous workflow, tool-using assistant, multi-agent system, or dynamic/branching automation. This capability is auto-detected during `/plan-loop` and `/product-develop`, and can be run directly with `/agent-builder`.

It is separate from Loop Engineer's own operational skills (`skills/` at repo root, used to run the loop itself). This is about the agent the **user** is building, scaffolded into the product workspace under `agent/`.

## How detection works

`scripts/agent_skill_router.py` mirrors `scripts/frontend_skill_router.py`'s pattern: it reads `TASKS.yml`, `plan/`, `HANDOFF.md`, `DECISIONS.md`, and the current user message, scores them against agent-development signals ("AI agent," "agentic," "workflow automation," "dynamic workflow," "chatbot," "copilot," "multi-agent," "tool-use," "RAG," "cron agent," etc.), and — if matched — writes `plan/AUTO_AGENT_SKILLS.md` naming which agent "shape" it detected:

| Shape | Signals |
|-------|---------|
| `multi_agent` | multi-agent, agent swarm, orchestrator agent, sub-agent |
| `tool_use` | tool use, tool calling, function calling |
| `rag` | RAG, retrieval augmented, vector search/store |
| `scheduled` | cron, scheduled/background/recurring job |
| `dynamic_workflow` | dynamic/conditional/branching workflow, state machine agent |
| `chat_interface` | chatbot, chat interface, conversational agent |

```bash
loop auto-agent-skills --write
loop auto-agent-skills --text "build a multi-agent workflow automation chatbot" --write
```

## Scaffolding

```bash
loop agent scaffold
```

Creates, in the product workspace:

```text
agent/
  AGENT_ARCHITECTURE.md   # agent type, tools, memory, guardrails, model provider, evals
  skills/
    README.md
    _template/SKILL.md    # copy this per skill: agent/skills/<name>/SKILL.md
  tools/
    README.md              # tool/function definitions, destructive-tool flags
  evals/
    README.md              # golden cases, tied to skills/qa-validation/SKILL.md
```

Existing files are left alone unless `--force` is passed — this is a scaffold, not an overwrite.

## Skill format

A product's own agent skills use the same `SKILL.md` convention Loop Engineer uses for itself (frontmatter `name` + `description`, then a body) — a portable, self-describing format designed to transfer across tools without a dependency. See `templates/agent_skill.template.md`.

## Prior art — read-only reference, never vendored

`tools/registry.md`'s "Agent skill hub references" section lists external skill/plugin marketplaces useful for researching how others structure comparable capabilities. Treat any such research as a **read-only reference only** (e.g. via `WebFetch`) — never install, clone, or import another project's packages or runtime into the product. Loop Engineer's own convention is intentionally compatible in shape with the broader ecosystem, not a client of any specific registry. This mirrors the same "no vendoring" rule already applied to model-provider configuration (see `docs/MODEL_PROVIDERS.md`).

## Grounding design decisions in literature

Non-obvious agent-design claims (an eval methodology, a safety pattern, a memory architecture) should be grounded in published research, not asserted from memory — see `docs/RESEARCH_SEARCH.md` and `skills/research-search/SKILL.md`. Cite the source in `EVIDENCE_LOG.md`.

## Rules

- Reuse `agent/AGENT_ARCHITECTURE.md` / `DECISIONS.md` answers instead of re-asking the user.
- Destructive/high-risk tools require human approval (AGENTS.md rule 5) — document this per tool in `agent/tools/`.
- One skill = one trigger + one job; don't build a mega-skill.
- Agent behavior needs the same test/eval bar as any other code (AGENTS.md rule 10) — wire `agent/evals/` into `skills/qa-validation/SKILL.md`.

## Wiring

| Command | Behavior |
|---------|----------|
| `/plan-loop` | Runs `loop auto-agent-skills --write` early; reads `skills/agent-builder/SKILL.md` and `skills/research-search/SKILL.md` when signals present |
| `/product-develop` | Reads `plan/AUTO_AGENT_SKILLS.md` alongside `plan/AUTO_SKILLS.md`; runs `agent-builder` for the agent-loop development domain |
| `/loop-engine` | Routes to `skills/agent-builder/SKILL.md` when the product is/includes an AI agent |
| `/agent-builder` | Runs the full workflow directly |
