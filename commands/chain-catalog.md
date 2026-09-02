# /chain-catalog

Render the full chain surface (skills, commands, roles, capabilities, profiles,
harnesses) as a single Markdown catalog page. Use to onboard a maintainer, to
evaluate a contribution, or to discover what's available without grepping the
repo.

## How To Interpret

If the user says `/chain-catalog`, `catalog the chain`, `render the full surface`,
`what's in the chain`, or asks for a single-page overview of everything, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/chain-catalog/SKILL.md`
3. `scripts/chain_catalog.py`

## Loop

```text
READ manifests + skills + commands + roles + harnesses -> EMIT single-page catalog (Markdown by default; --json for tooling)
```

## Script

```bash
python scripts/chain_catalog.py --root <le-app>            # Markdown
python scripts/chain_catalog.py --root <le-app> --json    # JSON
python scripts/chain_catalog.py --root <le-app> --out docs/CHAIN_CATALOG.md
```

## Output

A single Markdown page with six sections: Capabilities, Skills, Commands,
Roles, Install Profiles, Harnesses. The output is deterministic and safe
to commit.

## Continuation

Save the output under `docs/CHAIN_CATALOG.md` at the end of each round.
Diff consecutive catalogs. A growing skill count is expected; growing
duplicate activation paths is a sign of drift.