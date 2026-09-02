---
name: frontend-animation
description: Auto-route frontend design, motion, animation, and 3D work through Loop Engineer's core guidance plus compatible installed external design skills, DESIGN.md references, and component packs. Use during frontend implementation; read plan/AUTO_SKILLS.md instead of asking the user to pick a pack or library.
---

# Frontend Design, Animation & 3D (Auto)

Inherits `docs/SKILL_CONTRACT.md`.

One core skill with optional external layers. Loop Engineer **automatically** selects the
right built-in references and compatible available external packs from `TASKS.yml`, `plan/`,
`HANDOFF.md`, `DECISIONS.md`, installed skill locations, project `DESIGN.md`, and package
metadata. The user never runs skill CLI commands or picks a library.

## Auto activation

During `/develop-product`, after selecting a task, the agent **must** run:

```bash
python scripts/frontend_skill_router.py --write
```

This writes `plan/AUTO_SKILLS.md` with the core references plus every
compatible external layer it detected. Then read the file and every
available reference listed there **before** coding.

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
- one design-direction layer, chosen by task signals;
- a reusable component layer for suitable React 3D work, when one is locally available.

External layers are third-party MIT-licensed packs credited in
`references/external-skill-chain.md` (author, repository, license per pack).
The chain **detects and selects** them; it never downloads, executes, or
modifies a pack. A selected-but-missing pack appears as `candidate` in
`AUTO_SKILLS.md` with the catalog entry naming what to fetch. Install/update
failures retain the built-in fallback and must not be claimed as successful
external use.

`DECISIONS.md` stack choice overrides scoring when present.

## Agent rules

1. **Never ask** "GSAP or Motion?" unless `plan/AUTO_SKILLS.md` marks **Ambiguous** and `DECISIONS.md` is silent.
2. **Default:** React/Next motion → `ui-motion`; scroll pin/scrub → `scroll-animation`; 3D in React → `react-3d`.
3. Read the listed topic reference + one example file from `AUTO_SKILLS.md`.
4. Confirm each selected external layer is **available** before use; a pack marked
   `candidate` is not installed - surface its catalog entry from
   `references/external-skill-chain.md` in the handoff instead of inventing its
   guidance. Never use `not-applicable` layers.
5. Record the primary library in `DECISIONS.md` on first use.
6. Verify: `prefers-reduced-motion`, transform/opacity only, 60fps target.

## Verify before done

- `prefers-reduced-motion` respected
- Animate **transform, opacity, filter** only
- Cleanup on unmount (GSAP `context.revert`, ScrollTrigger.kill)

## Pre-Report Gate (for review and audit passes)

When a reviewer or assurance role runs against an animation change, each HIGH or
CRITICAL must clear four questions before it ships. Drop or downgrade if any answer
is "no":

1. Can I name the exact file, line, and animation target under concern?
2. Can I describe the user-visible failure mode - what the user sees, for whom, in
   what scenario (slow device, reduced-motion preference, missing asset)?
3. Have I confirmed the rule still applies against the current component code, not
   against a refactored hook or a renamed state variable?
4. Is the severity defensible at this stage of the product, not just in principle?

A clean review is a valid outcome. Manufacturing findings to justify the call is the
failure this gate prevents.

## Common False Positives

Skip these unless the UI or stage of work shows otherwise. Each is a pattern the LLM
reviewer will reach for; in this codebase or stage, it is almost always wrong.

- "Add `prefers-reduced-motion` handling" on a UI that has no animation, transition,
  or transform. The reviewer should cite the actual motion before flagging.
- "Animate transform/opacity only" on a non-animated element. Layout-property animation
  is only a smell when the element is actually animated.
- "Use GSAP timeline" on a CSS transition that is one-shot and <200ms. Timelines pay
  back for sequenced motion; a single-property transition does not need one.
- "Add 60fps target" on a static element. Frame rate is an animation concern.
- "Use Motion.dev for gestures" on a hover state. Hover is a CSS concern; gestures
  (drag, swipe, pinch) are when Motion.dev pays off.
- "Add scroll-linked animation" on a non-scrolling surface. ScrollTrigger is for
  scroll surfaces; the reviewer should cite the scroll container.
- "Use Web Workers for animation" on a non-CPU-bound animation. Workers fix
  computation, not paint; cite the profiler before flagging.
- "Use `will-change` for everything" on a static element. `will-change` is a hint for
  the compositor; over-application costs memory.
- "Replace the SVG with an icon font" on a single-color decorative icon. The
  trade-off only flips at scale.
- "Add a loading state" on an action that completes in <100ms. Spinners for
  imperceptible latencies are UX noise.
- "Lazy-load the 3D scene" on a scene with one mesh and <5KB of geometry. Lazy-load is
  for assets whose download dominates render time.
- "Reduce motion on iOS Safari" when the design already uses transform/opacity and the
  browser handles it. The reviewer should cite the actual jank before flagging.


## Stop Conditions and Rollback

A mutating skill declares when to halt and how to revert, before it runs. This section
is required by the canonical skill contract (`docs/SKILL_CONTRACT.md` "Risk and approval")
and is the E3 pattern adopted in round 4.

### When to stop

- **Three failed attempts at the same step.** Retrying past three means the
  hypothesis is wrong, not the execution. Stop, record what was tried, and
  escalate to the user as a doubt.
- **A change introduces more errors than it resolves.** Net negative progress
  is a regression, not a fix. Revert the change; record the failure mode.
- **A gate fails that the plan said must pass.** A gate is a contract; a
  failing gate is the chain telling you the work is not done. Stop and resolve.
- **The active task's `acceptance` criteria become unreachable** because of
  upstream changes. The plan is no longer valid; the task needs re-design,
  not more attempts.
- **Cost drift outside the budget.** A skill that consumes tokens or dollars
  unboundedly is a runaway; stop and report.

### When to escalate to the user

- **High-risk external actions** (publish, deploy, spend, destructive,
  privileged) require explicit user approval per `AGENTS.md` #5. The skill
  prepares the change, names the risk, and waits.
- **A blocker that is human-owned.** The blocker is a question only the
  user can answer (a stakeholder's call, a missing credential, a sign-off).
  Record it in `DOUBTS.md` and `HANDOFF.md`; do not invent an answer.
- **A goal-direction change.** The plan no longer matches what the user
  wants. The chain halts; the user re-plans.

### Rollback path

- **A single-task rollback** is `git revert <task-sha>` (or `git restore` for
  staged-only changes) followed by re-running the active feature's
  `converge-report` to confirm the rollback did not regress the rest of
  the build.
- **A multi-task rollback** is a feature-level revert: identify the feature
  commit range from `.loop/active-feature.json`, revert the range, then run
  `feature-converge` to confirm the surface is clean.
- **A state-only rollback** (files, configs, but no code) is a `git restore
  <path>` + `git clean -fd <path>` for the recorded paths. The skill's
  output records which paths it touched; the rollback reverses exactly
  those.
- **A data-only rollback** is database- and tenant-scoped; record the
  affected rows in the change record, run the inverse migration, and
  verify the diff matches the change record before declaring done.
- **A deploy rollback** is the prior version's artifact promoted through
  the same path the deploy took; `cicd-release/SKILL.md` carries the
  per-deploy rollback procedure.

A rollback that cannot be performed in one step is a planning problem.
Stop and re-plan; do not chain partial rollbacks.
