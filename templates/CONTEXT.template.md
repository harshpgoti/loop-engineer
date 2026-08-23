# Product Context

Project context loaded at every loop session start.

## Language

The product's own words. One opinionated name per concept, and the synonyms it displaces.
`loop glossary` reports where the plan still uses a displaced one.

Be opinionated: when several words exist for one concept, pick the best and list the rest
under `_Avoid_`. Keep definitions to a sentence or two - say what a thing **is**, not what it
does. Only terms specific to this product belong here; general programming concepts do not,
however much the product uses them.

```markdown
**Denial**
A claim the payer adjudicated and refused to pay.
_Avoid_: rejection, decline
```

When two words turn out to name genuinely different things, define both rather than
displacing one - the `_Avoid_` list is for synonyms, not for distinctions.

- TBD

## Repo Map

- TBD

## Active Step

- See `plan/main_plan.md` and active `plan/step_*.md`

## Do Not Touch

- TBD

## Conventions

- Match existing stack and coding conventions in the product repo
- Keep reusable loop logic in `loop-engineer/`, product data in the product workspace
