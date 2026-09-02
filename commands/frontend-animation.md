# /frontend-animation

Built-in motion/3D skills are **auto-selected** during `/develop-product`. This command is for explicit animation work outside the normal build loop.

## How To Interpret

User mentions frontend design, redesign, UI/UX, animation, GSAP, Motion.dev, scroll effects,
Three.js, WebGL - or types `/frontend-animation`.

## Agent steps (automatic - user does nothing)

1. Run `python scripts/frontend_skill_router.py --write` with the user's message as `--text`
   if helpful. This writes `plan/AUTO_SKILLS.md` with the core references plus every
   external layer it detects (third-party MIT packs credited in
   `skills/frontend-animation/references/external-skill-chain.md`).
2. Read `plan/AUTO_SKILLS.md`.
3. Read every built-in topic reference and each **available** external file listed there.
   Follow `external-skill-chain.md`; use only `available` layers. A `candidate` layer is
   not installed - surface its catalog entry in the handoff instead of inventing its guidance.
4. Implement. Do not ask which library unless **Ambiguous** in AUTO_SKILLS and `DECISIONS.md` is empty.

## Required reads

- `skills/frontend-animation/SKILL.md`
- `plan/AUTO_SKILLS.md` (after router runs)
- Topic references listed in AUTO_SKILLS
- External skill/reference paths listed as available in AUTO_SKILLS

## Output

- Auto-selected topic references used
- Implementation summary
- Motion acceptance checklist
- External layers selected, available, and actually used
- `DECISIONS.md` update if stack was new

## Required Reads

1. `AGENTS.md`
2. `commands/frontend-animation.md` (this file)
3. `skills/frontend-animation/SKILL.md`
4. `plan/AUTO_SKILLS.md` when the manifest lists it

## Loop

1. RUN `python scripts/frontend_skill_router.py --write`
2. READ the resulting `plan/AUTO_SKILLS.md`
3. READ every reference the router listed
4. IMPLEMENT the animation, motion, or 3D work
