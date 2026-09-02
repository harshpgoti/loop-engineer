# /roles

List every role in the Loop Engineer chain with its class, model tier, skills,
handoff targets, and independence boundaries. Use to discover the chain's
responsibility matrix or to plan a role addition or handoff change.

## How To Interpret

If the user says `/roles`, `who is in the chain`, `list the roles`, `show the
responsibility matrix`, or asks how the chain is composed, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `manifests/agents.json`

## Loop

```text
READ agents.json -> FILTER by class (optional) -> EMIT table
```

## Script

```bash
python scripts/roles_list.py                 # Markdown
python scripts/roles_list.py --json         # JSON
python scripts/roles_list.py --class assurance  # filter
```

## Output (Markdown)

A single table with one row per role: id, class, model tier
(`opus` / `sonnet` / `haiku`), `may_mutate`, the role's skills, the
`hands_off_to` list, and the `independent_from` list. The independence
boundary is the chain's `autoreview` enforcement; the hand-off list
names which other roles this role escalates to.

## Continuation

A role with no `independent_from` and class `assurance` is a violation of
the autoreview rule; the agent-registry validator already flags it. A
role with no `hands_off_to` is an island; consider wiring it to a
sibling. The list is read-only; the chain does not modify roles from
this command.