---
name: codebase-onboarding
description: 4-phase onboarding for a fresh project: Reconnaissance -> Architecture mapping -> Convention detection -> Generate onboarding guide + enhance (not replace) an existing CLAUDE.md. Use when adopting Loop Engineer on a project that has not been onboarded yet, or when the repo has changed enough that the prior onboarding is stale.
---

# Codebase Onboarding

Inherits `docs/SKILL_CONTRACT.md`.

A four-phase walk that turns an unknown codebase into a usable onboarding artifact
plus an enhanced (never overwritten) `CLAUDE.md`. The chain never edits an existing
`CLAUDE.md`; it appends, links, or surfaces a "this would be added" patch.

## When to use

- Loop Engineer is being adopted on a project for the first time.
- A project has substantially changed (framework swap, restructure) and the prior
  onboarding no longer matches the code.
- A new contributor is joining and `/setup-loop-engine` should produce a real
  starting point, not a generic template.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A review of a specific code area | `codebase-design` |
| A structural refactor | `implementation-planner` |
| A legacy codebase's style codification | `inherit-legacy-style` |

## Phase 1 - Reconnaissance

Parallel checks. Read-only.

| Signal | Where to look |
|---|---|
| Manifests | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `Package.swift`, `composer.json` |
| Frameworks | imports in the entry points, framework-specific config files |
| Entry points | `bin/`, `cmd/`, `src/index.*`, `app/main.*`, the script registered in the manifest |
| Test runner | `package.json` scripts, `Makefile`, `tox.ini`, `pytest.ini`, CI workflow files |
| CI | `.github/workflows/`, `.circleci/`, `buildkite.yml`, `Jenkinsfile` |
| Existing `CLAUDE.md` | repo root + sub-folders (most projects have a partial one) |
| Existing `AGENTS.md` | repo root + the Loop Engineer `app/` install, if any |

Each parallel check produces one line of structured output. The lines are the
raw material for Phase 2.

## Phase 2 - Architecture Mapping

Trace entry points to execution paths to architecture layers to dependencies.

```text
Entry points   -> HTTP/gRPC/CLI surface, server bootstrap, event handlers
Execution path -> a single request/job from entry to response, with one branch
Architecture   -> the named layers: presentation / application / domain / data
Dependencies   -> first-party modules + external packages the request touches
```

The output is a small **architecture index**, not a full diagram. The diagram
lives in the LE `plan-canvas` skill, not here. This phase produces the
textual index the diagram derives from.

## Phase 3 - Convention Detection

Read the existing code to extract the conventions the project actually uses.
Cite the file and line for every claim. Do not impose conventions the project
does not already follow.

- **File layout** - directory conventions, naming, `src/` vs flat, monorepo.
- **State and control flow** - sync vs async, callbacks vs promises vs
  coroutines, error handling shape.
- **Infrastructure** - config loading, logging, secrets, env management.
- **Error handling** - typed errors vs exceptions vs Result, where the boundary is.
- **Test conventions** - naming, fixtures, what gets tested vs what is not.
- **Existing `CONTEXT.md` vocabulary** - read the file; do not re-derive.

Each convention is recorded with one example citation (`<file>:<line>`) so the
reader can verify. Conventions without citation are dropped.

## Phase 4 - Generate Onboarding Guide + CLAUDE.md Patch

Two artifacts:

1. **`docs/ONBOARDING.md`** (always). The full onboarding narrative: what the
   project is, how to run it, how to test it, where the seams are, what the
   conventions are. Phase 1-3 outputs as the source.

2. **`CLAUDE.md` patch** (only if a `CLAUDE.md` does not already exist; if it
   does, the patch is **appended**, not replaced). The patch is a small,
   opinionated addition: "in this repo, also do X." It is not a full rewrite.

The patch is written under `.loop/pending/CLAUDE_PATCH.md` for the user to
review and apply, never auto-applied. A user who has already curated a
`CLAUDE.md` does not want the chain to overwrite it.

## Workflow

```text
DETECT existing CLAUDE.md
  +-- exists -> Phase 1-3 -> write docs/ONBOARDING.md -> write patch under .loop/pending/
  +-- missing -> Phase 1-3 -> write docs/ONBOARDING.md -> write CLAUDE.md candidate under .loop/pending/
```

## Anti-Patterns

- **Overwriting an existing `CLAUDE.md`.** The user curated it. Enhance or surface
  a patch; do not replace.
- **Inferring conventions without citation.** A convention without a `file:line`
  example is a guess. Drop it.
- **A 50-page onboarding doc.** The index is a navigational aid. The detail lives
  in the actual files it points to.
- **Skipping the existing-`CLAUDE.md` check.** A project that already has one
  deserves respect for what is there.
- **Single-agent sequence.** The four phases are parallelisable; do them as
  parallel sub-agents per Phase 1's table.

## Related Skills

- `codebase-design` - module, interface, and seam vocabulary.
- `inherit-legacy-style` - codify the style of a hand-written legacy codebase.
- `setup-loop-engine` - the command that triggers this skill.
- `plan-canvas` - the visual diagram that Phase 2's textual index feeds.