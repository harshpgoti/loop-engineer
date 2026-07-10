---
name: frontend-animation
description: Loop Engineer's single core skill for frontend motion, animation, 3D, and modern web design. Auto-activated during /product-develop when task/plan signals animation, scroll effects, WebGL, or design work. Do not ask the user to pick a library — read plan/AUTO_SKILLS.md.
---

# Frontend Animation & 3D (Auto)

One skill, nine topics. Loop Engineer **automatically** selects the right topic
references from `TASKS.yml`, `plan/`, `HANDOFF.md`, and `DECISIONS.md`. The user
never runs skill CLI commands or picks a library.

## Auto activation

During `/product-develop`, after selecting a task, the agent **must** run:

```bash
python scripts/frontend_skill_router.py --write
```

Then read `plan/AUTO_SKILLS.md` and every reference listed there **before** coding.

Equivalent: `loop auto-skills --write`

## When it triggers

Signals include: animation, motion, parallax, hero, scroll effects, GSAP, Motion.dev, Three.js, WebGL, R3F, landing page UI, micro-interactions, 3D, design system.

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

`DECISIONS.md` stack choice overrides scoring when present.

## Agent rules

1. **Never ask** "GSAP or Motion?" unless `plan/AUTO_SKILLS.md` marks **Ambiguous** and `DECISIONS.md` is silent.
2. **Default:** React/Next motion → `ui-motion`; scroll pin/scrub → `scroll-animation`; 3D in React → `react-3d`.
3. Read the listed topic reference + one example file from `AUTO_SKILLS.md`.
4. Record the primary library in `DECISIONS.md` on first use.
5. Verify: `prefers-reduced-motion`, transform/opacity only, 60fps target.

## Verify before done

- `prefers-reduced-motion` respected
- Animate **transform, opacity, filter** only
- Cleanup on unmount (GSAP `context.revert`, ScrollTrigger.kill)
