# /skill-scout

Search the local skill pack and adjacent ecosystems for skills that already
cover a need, before creating a new one. Vet external skills for malicious
shell/writes. Rank candidates. Use when adding a new skill, before creating a
new agent, or when a recurring need surfaces that the chain does not yet cover.

## How To Interpret

If the user says `/skill-scout`, `does this skill already exist`, `find an
existing skill for X`, or asks to scout before creating, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/skill-scout/SKILL.md`
3. `skills/*/SKILL.md` (the local pack)
4. the need in plain language (provided by the user)

## Loop

```text
STATE THE NEED -> SEARCH LOCAL PACK -> SEARCH GITHUB ECOSYSTEMS -> WEB SEARCH (last resort) -> OUTPUT RANKED TABLE
```

## Output (locked)

```markdown
# Skill Scout Report: <need>

## Need
<one sentence>

## Candidates
| Rank | Source | Path | Trust | Coverage | Notes |
|------|--------|------|-------|----------|-------|
| 1 | local | skills/<name>/SKILL.md | high | full / partial | <one line> |
| 2 | github | <repo>/<path> | medium | ... | |
| 3 | web | <url> | low | ... | |

## Recommendation
- Adopt: <rank>; do not write a new skill.
- Extend: <rank>; promote the partial coverage to full.
- Write: <reason no rank above is sufficient>.
- Defer: <reason the need is not yet concrete enough>.
```

## Continuation

Adopt → link to the existing skill. Extend → file a task to add the
missing capability. Write → the new skill is added; the scout's report
becomes the rationale. Defer → the need is parked in `DOUBTS.md`.