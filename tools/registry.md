# Tool Registry

This is the **single canonical place** for named external tools, repos, and reference
sites Loop Engineer may point to. Nothing here is bundled or required - Loop Engineer
works standalone. Other files (skills, docs, commands) should link here rather than
naming or linking these externally again inline, so there is one place to update.

## How to read this file

| Section | Meaning |
|---------|---------|
| **Loop Engineer defaults** | Built into `/plan-loop`, `/product-develop`, `skills/`, and `~/.loop-engineer/data/` |
| **Optional external extensions** | Third-party tools you may wire in when a gate or product need justifies it |
| **Research paper sources** | Live sources `skills/research-search/SKILL.md` queries |
| **Agent skill hub references** | External skill/plugin marketplaces `skills/agent-builder/SKILL.md` may consult, read-only |

Do not add an external tool just because it is listed. Add it only when `/plan-loop` or `GATES.yml` requires the capability.

---

## Loop Engineer defaults (built-in)

| Loop phase | Capability | Default in Loop Engineer |
|------------|------------|---------------------------|
| Memory | Durable product state | `memories/`, `state.db`, `~/.loop-engineer/data/`, `<product-folder>/.loop-engineer/` |
| Skills | Procedural instructions | `skills/` + product `skills/` |
| AI agent development | Architecture, scaffolding, skill authoring | `skills/agent-builder`, `agent/` scaffold |
| Research grounding | Literature search for evidence-backed claims | `skills/research-search` |
| Planning | PRD, ADRs, tasks, feature specs | `/plan-loop`, `plan/main_plan.md`, `plan/`, `plan/features/` |
| Build | Implementation + gates | `/product-develop`, `TASKS.yml`, `GATES.yml` |
| Frontend motion / 3D | Built-in animation skills | `skills/frontend-animation`, `ui-motion`, `gsap-*`, `webgl-3d`, `react-3d` |
| Review | Code + security review | `skills/code-reviewer`, `skills/security-compliance` |
| Release | Deploy readiness | `/release-check`, `DEPLOYMENT_PLAN.md` |
| Session continuity | Recall + handoff | `/session-recall`, `/memory-review`, `HANDOFF.md` |

---

## Optional external extensions

Use these to extend Loop Engineer when the product plan needs more than the defaults above.

| Loop phase | Tool / Reference | Use |
|------------|------------------|-----|
| Memory | [GBrain](https://github.com/garrytan/gbrain) | Company brain, synthesis, citations, gap analysis, interview memory |
| Skill reuse | [OpenClaw agent-skills](https://github.com/openclaw/agent-skills) | autoreview, handoff, reusable agent workflows |
| Product agent production | [Agents Towards Production](https://github.com/NirDiamant/agents-towards-production) | production agent architecture, security, deployment, observability |
| Spec-driven development | [GSD Core](https://github.com/open-gsd/gsd-core) | phased specs, task discipline, planning structure |
| Skill format | [Anthropic Skills](https://github.com/anthropics/skills) | skill folder structure, progressive disclosure, portable instructions |
| Role agents | [GStack](https://github.com/garrytan/gstack) | CEO, PM, design, engineering manager, QA, release roles |
| Sandboxed execution | [NemoClaw](https://github.com/NVIDIA/NemoClaw) | safer long-running agents, network policy, sandbox lifecycle |
| RAG / retrieval | [NVIDIA RAG Blueprint](https://github.com/NVIDIA-AI-Blueprints/rag) | ingestion, hybrid search, reranking, RAGAS eval, guardrails |

### Frontend animation & 3D (one built-in core skill)

`skills/frontend-animation/` - a single core skill, nothing to install. Topic references inside cover the Motion library (React/Next UI motion), GSAP (tweens, timelines, ScrollTrigger, React, performance), Three.js/WebGL + React Three Fiber, and modern web design (a11y, Core Web Vitals), plus examples, starter scaffolds, and generator scripts.

Router: `scripts/frontend_skill_router.py` writes `plan/AUTO_SKILLS.md` during `/product-develop` - agents read the selected topic references automatically; users never pick a library manually. See `docs/FRONTEND_ANIMATION.md`.

### Suggested pairings (when you extend)

| Need | Loop Engineer now | Optional extension |
|------|-------------------|---------------------|
| Product memory | `memories/MEMORY.md`, `state.db` | GBrain for synthesis / dream cycles |
| Command routing | `commands/`, `skills/` | OpenClaw autoreview patterns |
| Planning structure | `plan/`, `plan/features/`, task compiler | Optional: [GitHub Spec Kit](https://github.com/github/spec-kit) in product repos only - not bundled |
| Role coverage | skills council, QA, security | GStack role agents |
| Long-running builds | `/loop-engine`, gates | NemoClaw sandbox |
| Evidence retrieval | `EVIDENCE_LOG.md` | NVIDIA RAG blueprint when RAG is in scope |
| Animated UI / 3D frontend | Built-in `skills/frontend-animation`, `ui-motion`, `gsap-*`, `webgl-3d` | - (already in Loop Engineer) |

---

## Research paper sources

Queried live by `skills/research-search/SKILL.md` (`loop research "<query>"`) - see `docs/RESEARCH_SEARCH.md` for verified API details per source.

| Source | URL | Method |
|--------|-----|--------|
| arXiv | <https://arxiv.org/> | Official Atom API, no key |
| Research Square | <https://www.researchsquare.com/> | Crossref REST API filtered to DOI prefix `10.21203`, no key |
| SSRN | <https://www.ssrn.com/> | No public API - URL-builder only, blocks automated fetches |

## Agent skill hub references

Read-only research for `skills/agent-builder/SKILL.md` step 8 when designing a product's own agent skills - **never vendor or install packages from these**, consult via `WebFetch` for pattern inspiration only.

| Hub | URL | Use |
|-----|-----|-----|
| ClawHub | <https://clawhub.ai/skills> | Skills/plugins marketplace for OpenClaw agents |
| Hermes Agent Skills Hub | <https://hermes-agent.nousresearch.com/docs/skills> | Browsable registry of skills for the Hermes Agent runtime |

---

## Rules

- Do not vendor external repos into Loop Engineer core.
- Keep named external tools/URLs in this file only - other skills/docs/commands should link here, not repeat the name/URL inline, so there is one place to update.
- Prefer deterministic parsers and validators before RAG or LLM workflows.
- Keep product memory in Loop Engineer paths; external tools are adapters, not replacements.
- Update this file when `/plan-loop` selects an integration and document the gate that required it.
