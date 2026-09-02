---
name: chain-catalog
description: Render the full chain surface (skills, commands, roles, capabilities, profiles, harnesses) as a single Markdown catalog page. Use to onboard a maintainer, to evaluate a contribution, or to discover what's available without grepping the repo.
---

# Chain Catalog

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic skill that renders the chain's surface as one
Markdown page. The page is a single source of truth for "what does the
chain contain right now?" — useful for onboarding, for review, and for
discovery.

## When to use

- A new maintainer is onboarding; show them the chain as a page, not
  as 90 files to open.
- A contribution is being evaluated; the catalog surfaces where the
  new skill/command/role fits.
- A discovery question: "do we have a skill for X?" — the catalog
  answers it in one grep.
- A release-readiness review: the catalog is the diff against the
  previous release.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A per-skill or per-role discovery | `/skill-list` or `/roles` |
| A specific skill's body | read `skills/<name>/SKILL.md` |
| A benchmark of the chain's state over time | `/chain-bench` |

## Workflow

### 1. Generate the catalog

```bash
python scripts/chain_catalog.py --root <le-app>
```

The script walks `manifests/`, `skills/`, `commands/`, and `harnesses/`
and emits a single Markdown page with these sections:

- **Capabilities** — id, context cost, summary.
- **Skills** — name, class, owning capabilities, one-line summary.
- **Commands** — name, owning capabilities, one-line summary.
- **Roles** — id, class, model, `may_mutate`, skills, hand-off targets,
  independence boundaries.
- **Install Profiles** — id, summary, capabilities, context budget.
- **Harnesses** — id, trust level, invocation.

### 2. Save the catalog under `docs/CHAIN_CATALOG.md`

A generated file under `docs/` is the canonical reference. Update
the catalog after every round (the script is part of the post-round
checklist).

### 3. Diff against the previous catalog

Two consecutive catalogs, side by side, answer "what changed in
this round?" in a way that AGENTS.md's table cannot.

## Output

A single Markdown file with the six sections. The output is
deterministic: same input, same output. The script is safe to run
in CI.

## Anti-Patterns

- **A catalog that grows every round.** The chain is at 90 skills;
  adding 10 more per round is unsustainable. The catalog is the
  pressure to consolidate.
- **A catalog that hides the activation paths.** `/skill-list`
  shows activation paths; the catalog summarises. The summary must
  not hide the data.
- **A catalog that is auto-generated without review.** A generated
  catalog that lists dead skills is a maintenance lie. The catalog
  is a snapshot; the maintainer reviews it before publishing.
- **A catalog that drifts from the manifests.** The script reads
  the manifests; if the manifests are wrong, the catalog is wrong.
  The catalog is a mirror, not a source.

## Related Skills

- `agent-sort` - the DAILY vs LIBRARY classification; the catalog
  shows the totals that classification should reduce.
- `chain-bench` - the chain's own state benchmark; the catalog
  shows what the benchmark measures.
- `skill-list`, `roles` - the per-section discoveries; the catalog
  is the single-page union of both.