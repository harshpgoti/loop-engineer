# Decision Log

No product decisions yet. `/plan-loop` should add entries when the user makes product or architecture decisions.

## Entry format

```markdown
## D-001: Pricing is flat fee only
- **Date:** 2026-08-10
- **Decision:** No percentage of recovered revenue, in any market.
- **Rationale:** <why>
- **Supersedes:** DQ-007, DQ-020
```

**`Supersedes`** is read by the harness. Some decisions do not *answer* a question -
they remove the reason it was ever asked. List those doubt IDs here and they stop being
asked, in this workspace **and in any sub-product**, with the reason recorded:

```
DQ-007: superseded by D-001 (parent product) - not asked
```

One direction only: a main product can retire a question inside a sub-product, never the
reverse. It is applied at read time, so deleting the `Supersedes:` line reopens the doubt.

## Pending decisions (need evidence or counsel)

| Topic | Options | Blocker |
|-------|---------|---------|
| Product name | TBD | User input |
| First product step | TBD | User input |
| Product repo strategy | same repo vs new repo vs existing repo | User input |
| Stack | TBD | Product requirements |
| Sensitive data policy | synthetic only vs real data with controls | User input and risk review |
