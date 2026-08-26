---
name: frontend-animation
description: Auto-route frontend design, motion, animation, and 3D work through Loop Engineer's core guidance plus compatible installed external design skills, DESIGN.md references, and component packs. Use during frontend implementation; read plan/AUTO_SKILLS.md instead of asking the user to pick a pack or library.
---

# Frontend Design, Animation & 3D (Auto)

One core skill with optional external layers. Loop Engineer **automatically** selects the
right built-in references and compatible available external packs from `TASKS.yml`, `plan/`,
`HANDOFF.md`, `DECISIONS.md`, installed skill locations, project `DESIGN.md`, and package
metadata. The user never runs skill CLI commands or picks a library.

## Auto activation

During `/develop-product`, after selecting a task, the agent **must** run:

```bash
python scripts/frontend_skill_router.py --write
```

This installs or refreshes every selected external layer before writing
`plan/AUTO_SKILLS.md`. Then read the file and every available reference listed there
**before** coding.

Equivalent: `loop auto-skills --write`

## When it triggers

Signals include: animation, motion, parallax, hero, scroll effects, GSAP, Motion.dev,
Three.js, WebGL, R3F, landing page UI, dashboards, typography, redesign, micro-interactions,
3D, and design systems.

No signals → router writes nothing; skip this skill.

## Topics (selected for you)

All under `skills/frontend-animation/references/`:

| Reference | Covers | Typical auto-match |
|-----------|--------|--------------------|
| `ui-motion.md` | Motion library (React/Next) | UI motion, springs, gestures |
| `gsap-animation.md` | GSAP: tweens, timelines, ScrollTrigger, React, performance | Scroll pin/scrub, parallax, sequenced motion, 60fps |
| `3d-rendering.md` | Three.js/WebGL + React Three Fiber | 3D scenes, vanilla or React |
| `modern-web-design.md` | Design systems, a11y, Core Web Vitals | Landing page design, design system |

Deep-dive references in the same folder: `motion-reference.md` (Motion API +
spring physics), `3d-reference.md` (Three.js/R3F/Drei API, materials,
optimization), `design-patterns.md` (trends + interaction patterns),
`quality-checklists.md` (accessibility + performance).

Supporting material: `examples/motion-patterns.md` (copy-paste motion patterns),
`templates/` (component library, Next.js page), `assets/` (Three.js + R3F starter
scaffolds), `schema/` + `scripts/` (motion config validation, scene/component
generators, design audit).

## Optional external chain

When the router lists external layers, read
`references/external-skill-chain.md` and the exact available path printed in
`AUTO_SKILLS.md`. The router treats the integrations by role:

- project `DESIGN.md` - product-specific design language;
- UI UX Pro Max **or** Taste - one design-direction layer, chosen by task signals;
- ThreeUI - preferred reusable component layer for suitable React 3D work.

Selected external packs are installed automatically when missing and refreshed before every
use. npm-based upstream installers are preferred; Awesome DESIGN.md uses a managed Git
checkout because it has no npm package. Install/update failures retain the built-in fallback
and must not be claimed as successful external use.

`DECISIONS.md` stack choice overrides scoring when present.

## Agent rules

1. **Never ask** "GSAP or Motion?" unless `plan/AUTO_SKILLS.md` marks **Ambiguous** and `DECISIONS.md` is silent.
2. **Default:** React/Next motion → `ui-motion`; scroll pin/scrub → `scroll-animation`; 3D in React → `react-3d`.
3. Read the listed topic reference + one example file from `AUTO_SKILLS.md`.
4. Confirm each selected external layer is **available** or **installed-or-refreshed** after
   maintenance, then read it in chain order. Never use `update-failed`, `not-applicable`, or
   `install-unverified` layers.
5. Record the primary library in `DECISIONS.md` on first use.
6. Verify: `prefers-reduced-motion`, transform/opacity only, 60fps target.

## Verify before done

- `prefers-reduced-motion` respected
- Animate **transform, opacity, filter** only
- Cleanup on unmount (GSAP `context.revert`, ScrollTrigger.kill)
