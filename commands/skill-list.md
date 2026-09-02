# /skill-list

List every skill in the Loop Engineer chain with its class, owning capability,
and activation paths. Use to discover the chain's surface, audit wiring, or
prepare a change.

## How To Interpret

If the user says `/skill-list`, `what skills are there`, `list the chain's
skills`, `show the surface`, or asks what the chain has, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `manifests/skill_policy.json`
3. `manifests/capabilities.json`

## Loop

```text
WALK skills/ -> READ manifests -> BUILD owner + activation map -> EMIT table
```

## Script

```bash
python scripts/skill_list.py                # Markdown table
python scripts/skill_list.py --json        # JSON
python scripts/skill_list.py --class assurance   # filter
```

## Output (Markdown)

A single table with one row per skill: name, class (`read-only` / `stateful` /
`mutating` / `assurance`), owning capability, and the list of activation
sources (AGENTS.md, command files, and other skills that reference it).

A skill with no activation path is reachable only via direct human
invocation or via the harness's role-pick; surface those in audit.

## Continuation

A skill with no activation path is a candidate for `agent-sort` (move
to LIBRARY) or for deletion. A skill with multiple owners is a
candidate for `skill-stocktake` (merge or keep with documented split).
The list is read-only; the chain does not modify skills from this command.