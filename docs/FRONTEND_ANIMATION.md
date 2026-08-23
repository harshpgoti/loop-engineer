# Frontend Animation & 3D (Automatic)

Loop Engineer auto-selects frontend motion/3D guidance during `/develop-product`.
Users do not pick libraries or run skill commands. Everything lives in **one core
skill**: `skills/frontend-animation/`.

## How it works

After the agent selects a task, it runs:

```bash
python scripts/frontend_skill_router.py --write
```

This reads `HANDOFF.md`, `TASKS.yml`, `plan/step_*.md`, `DECISIONS.md`, and
`plan/main_plan.md`, scores signals, and writes **`plan/AUTO_SKILLS.md`** listing
the exact topic references to read. The agent reads them before implementation.
No user prompt required.

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

## Overrides

- **`DECISIONS.md`** - if a stack is already chosen (GSAP, Motion, R3F), the router locks to it.
- **Ambiguous scores** - router notes when two stacks tie; agent uses defaults (React→Motion, scroll pin→ScrollTrigger, 3D→R3F/Three.js).

## Acceptance for motion tasks

- `prefers-reduced-motion` supported
- Animate transform/opacity/filter only
- 60fps target; cleanup on unmount (GSAP `context.revert`, ScrollTrigger.kill)
- Record the primary library in `DECISIONS.md` on first use
