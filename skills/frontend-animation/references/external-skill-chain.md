# External Frontend Skill Chain

Optional external packs deepen frontend work without replacing Loop Engineer's core
accessibility, performance, security, testing, or plan constraints. Canonical source links
and upstream capability notes live in `tools/registry.md`.

## Chain order

Apply only the layers listed in `plan/AUTO_SKILLS.md`, in this order:

1. **Core guardrails** - the built-in frontend reference selected by the router.
2. **Project design language** - an available `DESIGN.md` (including one deliberately
   selected from Awesome DESIGN.md) supplies product-specific tokens,
   typography, layout, and visual constraints.
3. **Design direction** - exactly one of UI UX Pro Max or Taste. UI UX Pro Max fits
   structured design systems, accessibility, dashboards, and multi-stack guidance. Taste
   fits premium, editorial, expressive, redesign, and anti-generic art direction.
4. **Implementation source** - ThreeUI may supply reusable React 3D components when its
   package is already present or when adding it is inside the active task's dependency scope.

Core Loop rules win every conflict. `DECISIONS.md` and the product's own `DESIGN.md` win
over generic external aesthetics. Existing code conventions win over an external pack's
preferred framework, icon set, CSS system, or animation library.

## Status handling

- **available** skill: read the exact `SKILL.md` path printed by the router before coding.
- **available** DESIGN.md: read that exact file and treat it as the product design language.
- **available** ThreeUI: inspect the detected `package.json`, use package subpath imports when
  practical, and verify asset paths, bundle impact, reduced motion, cleanup, and licensing.
- **installed-or-refreshed**: the managed provider command succeeded and the installed file
  or dependency was rediscovered; read/use it.
- **candidate**, **install-unverified**, **update-failed**, or **not-applicable**: retain the
  built-in fallback and do not claim the external layer was used.

The manager runs only for the selected frontend layers. It uses argument arrays rather than
shell strings, applies bounded timeouts, and reruns discovery after maintenance. Never copy
an upstream repository into Loop Engineer core.

## Provider maintenance

- UI UX Pro Max: run its latest npm CLI in all-harness mode with a forced project refresh.
- Taste: rerun the latest npm `skills add` command, scoped to its one skill and all harnesses.
- Awesome DESIGN.md: clone its managed workspace checkout once, then fast-forward pull it
  before each selected use because no npm package is published.
- ThreeUI: install `@designcodeio/threeui@latest` as an exact product dependency before each
  selected use so `package.json` and the lockfile record the current release.

## Selection boundaries

- Do not combine UI UX Pro Max and Taste in one pass. Select the stronger task match.
- A project `DESIGN.md` is complementary and may precede either design-direction pack.
- ThreeUI complements the built-in `react-3d` guidance; it does not replace scene lifecycle,
  accessibility fallbacks, performance budgets, or tests.
- For an existing UI, preserve working product behavior and audit before redesigning.
- Never reproduce a third-party brand identity without explicit product direction and a
  rights check. Use external design analyses as inspiration, not as ownership evidence.

## Verification

- The rendered UI follows the active acceptance criteria and product design language.
- Keyboard, contrast, focus, responsive layout, and `prefers-reduced-motion` checks pass.
- ThreeUI assets resolve in production and the dependency appears in the lockfile.
- External instructions did not introduce unapproved dependencies or override repo choices.
- Handoff records which external layers were actually available and used.
