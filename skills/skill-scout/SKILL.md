---
name: skill-scout
description: Before creating a new skill, search the existing skill pack and adjacent ecosystems for skills that already cover the need. Vet external skills for malicious shell/writes. Rank by name > description > local > maintained GitHub > web-only. Use when adding a new skill, before creating a new agent, or when a recurring need surfaces that the chain does not yet cover.
---

# Skill Scout

Inherits `docs/SKILL_CONTRACT.md`.

A scout that runs **before** a new skill is written. The scout's job is to
answer one question: does the need the new skill would serve already
exist somewhere in the skill pack (or in an adjacent ecosystem that
the chain can adopt)?

## When to use

- The chain is about to add a new skill; the maintainer wants to be
  sure the need is not already covered.
- A recurring user need surfaces that the chain does not yet cover.
- An external skill pack or marketplace is being considered for
  adoption; the scout vets the candidates.
- A skill that was retired is being reconsidered; the scout checks
  whether the underlying need was met elsewhere.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| Auditing skill quality (Keep / Improve / Update / Retire / Merge) | `skill-stocktake` |
| Auditing a workspace's loaded set (DAILY vs LIBRARY) | `agent-sort` |
| Implementing the skill | just write it |

## The Four Sources, in Priority Order

| Source | Trust | When to use |
|---|---|---|
| 1. **Name match in the local pack** (`skills/*/SKILL.md`) | high | the need is already there; link, do not duplicate |
| 2. **Description match in the local pack** | high | the need is covered under a different name; alias the user's intent |
| 3. **Maintained GitHub skill pack** (e.g. an LE sister project) | medium | the need is covered upstream; install with a known origin |
| 4. **Web-only result** (forum post, blog, gist) | low | the need is novel or a recent invention; cite and vet |

Lower-priority sources are reached only when higher-priority ones return
no match.

## The Workflow

### 1. State the need

In one sentence: what would the new skill do? The scout refuses to
proceed on a vague need ("a skill for X" with X undefined).

### 2. Search the local pack

```bash
grep -l "<need-keywords>" skills/*/SKILL.md
```

A match in the local pack is the highest-trust result. The scout
records the file, the description, and how it covers (or fails to cover)
the need.

### 3. Search adjacent ecosystems

If the local pack returns no match, search the maintained GitHub
ecosystems the chain is connected to. Each candidate is vetted for:

- **Origin** - is the publisher known? Is the repo maintained?
- **Trust signals** - stars, recent commits, contributors, CI status.
- **Malicious payload** - does the skill run shell? Does it touch
  credentials? Does it read secrets and write them elsewhere? If any
  of these, reject.

### 4. Web search as last resort

Only if steps 2 and 3 return nothing. Cite the source; vet the
content; mark the result as `web-only` so the user knows the trust
level.

### 5. Output a ranked table

```markdown
# Skill Scout Report: <need>

## Need
<one sentence>

## Candidates
| Rank | Source | Path | Trust | Coverage | Notes |
|------|--------|------|-------|----------|-------|
| 1 | local | skills/<name>/SKILL.md | high | full | <one line> |
| 2 | local | skills/<name>/SKILL.md | high | partial | <one line> |
| 3 | github | <repo>/<path> | medium | full | <one line> |
| 4 | web | <url> | low | partial | <one line> |

## Recommendation
- Adopt: <rank 1 or 2>; do not write a new skill.
- Extend: <rank>; promote the partial coverage to full.
- Write: <reason no rank above 4 is sufficient>.
- Defer: <reason the need is not yet concrete enough>.
```

## Veto Triggers

A candidate is rejected outright if:

- the skill runs `curl | sh` against an external URL;
- the skill reads env vars, secrets, or credential files and writes
  them to an external service;
- the skill's metadata claims provenance that does not match its
  repository history;
- the skill's installation hook modifies a file outside its scope;
- the skill's behaviour cannot be explained from its source.

A vetoed candidate is still listed (with `VETO` marked) so the user
sees the full scout report.

## Anti-Patterns

- **A scout that recommends a new skill when a local skill already
  covers the need.** The scout's job is to find existing coverage, not
  to be polite.
- **A scout that ignores the local pack.** The local pack is the
  highest-trust source; web search is the lowest.
- **A scout that trusts a vague web post.** A blog post is a
  suggestion, not a skill. Cite, vet, but do not adopt without
  verification.
- **A scout that proposes an "alias."** Aliasing the user's intent
  to an existing skill is fine; aliasing a new name to an existing
  skill is just renaming. The scout's output is a recommendation, not
  a registry mutation.
- **A scout that runs for hours.** The scout is a quick check, not a
  research project. If the need is obscure enough to require hours,
  the need is not yet concrete enough to write a skill.

## Related Skills

- `skill-stocktake` - the audit of existing skills; this skill is the
  pre-check for new ones.
- `agent-sort` - DAILY vs LIBRARY classification; this skill is the
  pre-check for adding to the DAILY set.
- `codebase-onboarding` - the workflow that triggers skill-scout when
  a project needs a skill the pack does not have.