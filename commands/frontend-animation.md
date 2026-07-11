# /frontend-animation

Built-in motion/3D skills are **auto-selected** during `/product-develop`. This command is for explicit animation work outside the normal build loop.

## How To Interpret

User mentions animation, GSAP, Motion.dev, scroll effects, Three.js, WebGL - or types `/frontend-animation`.

## Agent steps (automatic - user does nothing)

1. Run `python scripts/frontend_skill_router.py --write` with the user's message as `--text` if helpful.
2. Read `plan/AUTO_SKILLS.md`.
3. Read every topic reference listed there.
4. Implement. Do not ask which library unless **Ambiguous** in AUTO_SKILLS and `DECISIONS.md` is empty.

## Required reads

- `skills/frontend-animation/SKILL.md`
- `plan/AUTO_SKILLS.md` (after router runs)
- Topic references listed in AUTO_SKILLS

## Output

- Auto-selected topic references used
- Implementation summary
- Motion acceptance checklist
- `DECISIONS.md` update if stack was new
