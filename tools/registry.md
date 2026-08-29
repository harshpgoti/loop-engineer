# Tool Registry

This is the **single canonical place** for named external tools, repos, and reference
sites Loop Engineer may point to. Nothing here is bundled or required - Loop Engineer
works standalone. Other files (skills, docs, commands) should link here rather than
naming or linking these externally again inline, so there is one place to update.

## How to read this file

| Section | Meaning |
|---------|---------|
| **Loop Engineer defaults** | Built into `/plan-loop`, `/develop-product`, `skills/`, and `~/.loop-engineer/data/` |
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
| Build | Implementation + gates | `/develop-product`, `TASKS.yml`, `GATES.yml` |
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
| Frontend design intelligence | [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT portable skill; design-system generation, UX guidance, searchable styles/colors/type, and broad stack coverage |
| Frontend art direction | [Taste Skill](https://github.com/Leonxlnx/taste-skill) | MIT portable skill collection; task-inferred visual direction, redesign guidance, motion/density/variance controls |
| Design-language references | [Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md) | MIT collection of project-readable design-system analyses; use a selected `DESIGN.md`, not the whole catalog |
| React 3D components | [ThreeUI Community](https://github.com/MengTo/threeui) | MIT React package/catalog for reusable Three.js/WebGL components; verify bundled asset and font notices |

### Frontend design, animation & 3D (core plus optional chain)

`skills/frontend-animation/` - a single core skill, nothing to install. Topic references inside cover the Motion library (React/Next UI motion), GSAP (tweens, timelines, ScrollTrigger, React, performance), Three.js/WebGL + React Three Fiber, and modern web design (a11y, Core Web Vitals), plus examples, starter scaffolds, and generator scripts.

Router: `scripts/frontend_skill_router.py` writes `plan/AUTO_SKILLS.md` during `/develop-product` - agents read the selected topic references automatically; users never pick a library manually. See `skills/frontend-animation/SKILL.md`.

The router can discover and manage UI UX Pro Max or Taste skills, a project `DESIGN.md`, the
Awesome DESIGN.md catalog, and the `@designcodeio/threeui` package. Before each selected use,
it installs missing layers or refreshes installed ones through provider-specific npm commands
(managed Git fallback for Awesome DESIGN.md), reruns discovery, and fails back to core
guidance when maintenance cannot be verified. Installation targets all supported harnesses;
the generated exact-path chain remains harness-neutral.

### Suggested pairings (when you extend)

| Need | Loop Engineer now | Optional extension |
|------|-------------------|---------------------|
| Product memory | `memories/MEMORY.md`, `state.db` | GBrain for synthesis / dream cycles |
| Command routing | `commands/`, `skills/` | OpenClaw autoreview patterns |
| Planning structure | `plan/`, `plan/features/`, task compiler | Optional: [GitHub Spec Kit](https://github.com/github/spec-kit) in product repos only - not bundled |
| Role coverage | skills council, QA, security | GStack role agents |
| Long-running builds | `/loop-engine`, gates | NemoClaw sandbox |
| Evidence retrieval | `EVIDENCE_LOG.md` | NVIDIA RAG blueprint when RAG is in scope |
| Animated UI / 3D frontend | Built-in `skills/frontend-animation`, `ui-motion`, `gsap-*`, `webgl-3d` | UI UX Pro Max or Taste for design direction; project DESIGN.md for visual language; ThreeUI for suitable React 3D components |

---

## Research paper sources

Queried live by `skills/research-search/SKILL.md` (`loop research "<query>"`), which records the verified access method for each source.

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
