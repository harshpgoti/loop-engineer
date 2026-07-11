# /agent-builder

Design and scaffold an AI agent (or agentic/dynamic workflow) as the product itself.

## How To Interpret

If the user says `/agent-builder`, `build an agent`, `build an ai agent`, `develop an agent`, `agent architecture`, or describes a product that is a chatbot/assistant/copilot/workflow-automation/multi-agent system, execute this file directly. This also auto-activates during `/plan-loop` and `/product-develop` - see `skills/agent-builder/SKILL.md`.

## Required Reads

1. `AGENTS.md`
2. `skills/agent-builder/SKILL.md`
3. `skills/model-providers/SKILL.md`
4. `skills/research-search/SKILL.md`
5. `plan/AUTO_AGENT_SKILLS.md` (if present)
6. `agent/AGENT_ARCHITECTURE.md` (if present)
7. `DECISIONS.md`

## One-shot commands

```bash
loop auto-agent-skills --write          # detect agent-development signals -> plan/AUTO_AGENT_SKILLS.md
loop agent scaffold                     # create agent/AGENT_ARCHITECTURE.md, agent/skills/, agent/tools/, agent/evals/
loop model setup                        # pick the agent's model provider
loop research "<topic>"                 # ground a design choice in published work
```

## Loop

```text
DETECT SIGNALS -> SCAFFOLD (if missing) -> FILL ARCHITECTURE -> PICK MODEL -> AUTHOR SKILLS/TOOLS -> WIRE EVALS -> RECORD DECISIONS
```

## Rules

- No vendoring of the external agent skill hubs listed in `tools/registry.md` - research there is a read-only reference (`WebFetch`), not a dependency.
- Reuse `agent/AGENT_ARCHITECTURE.md` / `DECISIONS.md` answers instead of re-asking.
- Destructive/high-risk tools require human approval (AGENTS.md rule 5).
- Ground non-obvious architecture/eval/safety claims via `skills/research-search/SKILL.md` and cite in `EVIDENCE_LOG.md`.

## Output

`agent/AGENT_ARCHITECTURE.md` status, agent shape, model provider, skills/tools authored, eval status, next command.

## Handoff

Continue with `/product-develop` to build the agent's tools/skills, or `/spec-clarify` if the agent's requirements are still unclear.
