# Frontend Design, Animation & 3D (Automatic)

Loop Engineer auto-selects frontend design, motion, and 3D guidance during
`/develop-product`. Users do not pick libraries or run skill commands. Built-in guardrails
live in **one core skill**, while optional external packs are layered behind the same router
seam.

## How it works

After the agent selects a task, it runs:

```bash
python scripts/frontend_skill_router.py --write
```

This reads `HANDOFF.md`, `TASKS.yml`, `plan/step_*.md`, `DECISIONS.md`,
`plan/main_plan.md`, installed portable skill locations, project `DESIGN.md`, and
`package.json`. It scores signals, installs or refreshes selected external layers, reruns
discovery, and writes **`plan/AUTO_SKILLS.md`** listing exact files to read, maintenance
status, precedence, and reasons. No user prompt is required.

Equivalent: `loop auto-skills --write` (also runs automatically at `loop session-start`).

## Skill structure

```text
skills/frontend-animation/
├── SKILL.md                     # umbrella: activation, topics, rules
├── references/
│   ├── ui-motion.md             # Motion library (React/Next UI motion)
│   ├── gsap-animation.md        # GSAP: tweens, timelines, ScrollTrigger, React, performance
│   ├── 3d-rendering.md          # Three.js/WebGL + React Three Fiber
│   ├── modern-web-design.md     # design systems, a11y, Core Web Vitals
│   ├── motion-reference.md      # deep dive: Motion API + spring physics
│   ├── 3d-reference.md          # deep dive: Three.js/R3F/Drei API, materials, optimization
│   ├── design-patterns.md       # deep dive: trends + interaction patterns
│   └── quality-checklists.md    # deep dive: accessibility + performance
├── examples/motion-patterns.md  # copy-paste motion examples
├── templates/                   # component library, Next.js page
├── assets/                      # Three.js + R3F starter scaffolds
├── schema/ + scripts/           # motion config validation, generators, design audit
```

## Topic routing

| Router topic | Reference selected | Auto-selected when |
|--------------|--------------------|--------------------|
| `ui-motion` | `ui-motion.md` | React/Next hero, gestures, springs |
| `scroll-animation`, `animation-timelines`, `web-animation`, `react-animation`, `animation-performance` | `gsap-animation.md` | Scroll pin/scrub/parallax, sequenced motion, general tweens, GSAP+React, 60fps |
| `webgl-3d`, `react-3d` | `3d-rendering.md` | 3D scenes (vanilla or React) |
| `modern-web-design` | `modern-web-design.md` | Design systems, Core Web Vitals |

## External chain routing

External projects have different roles and are not treated as interchangeable skills:

| Layer | Auto-selection rule | Availability evidence |
|-------|---------------------|-----------------------|
| Project design language | Use when `DESIGN.md` exists | Exact `DESIGN.md` path |
| Structured design intelligence | UI UX Pro Max when installed and dashboard, accessibility, design-system, or multi-stack signals dominate | Exact installed `SKILL.md` path |
| Expressive design direction | Taste when installed and premium, editorial, redesign, or anti-generic signals dominate | Exact installed `SKILL.md` path |
| React 3D implementation | Prefer ThreeUI for reusable React 3D hero/component/catalog work | `@designcodeio/threeui` in `package.json` |

UI UX Pro Max and Taste compete for one design-direction slot. Project `DESIGN.md` and
ThreeUI are complementary. A missing selected pack is installed automatically; an installed
selected pack is checked/refreshed before every use. The router uses npm-based providers
where available and a managed Git checkout for Awesome DESIGN.md. If maintenance fails or
cannot be verified, it continues with built-in guidance. Upstream links and researched
capability notes are centralized in `tools/registry.md`.

Portable discovery checks workspace and common global locations for Codex, Claude, Cursor,
Windsurf, OpenCode, Grok, PI, Gemini, Continue, Factory, and `.agents` layouts. Provider
installation targets all supported harnesses, while `AUTO_SKILLS.md` gives every Loop
adapter the same exact files to read.

## Maintenance on every use

`loop session-start` performs read-only selection. Immediately before frontend coding,
`loop auto-skills --write` performs selected install/update maintenance and writes the
verified chain. Direct `python scripts/frontend_skill_router.py --write` has the same
behavior. `--no-install` exists only for diagnostics and offline routing.

- UI UX Pro Max: latest npm CLI, all-harness refresh.
- Taste: latest npm skills installer, one-skill/all-harness refresh.
- Awesome DESIGN.md: managed shallow checkout, fast-forward update.
- ThreeUI: latest exact npm product dependency and lockfile update.

## Overrides

- **`DECISIONS.md`** - if a stack is already chosen (GSAP, Motion, R3F), the router locks to it.
- **Core precedence** - Loop accessibility, security, tests, acceptance criteria,
  `DECISIONS.md`, and project `DESIGN.md` override conflicting external defaults.
- **Ambiguous scores** - router notes when two stacks tie; agent uses defaults (React→Motion, scroll pin→ScrollTrigger, 3D→R3F/Three.js).

## Acceptance for motion tasks

- `prefers-reduced-motion` supported
- Animate transform/opacity/filter only
- 60fps target; cleanup on unmount (GSAP `context.revert`, ScrollTrigger.kill)
- Record the primary library in `DECISIONS.md` on first use
- Record which external layers were actually available and used in `HANDOFF.md`
