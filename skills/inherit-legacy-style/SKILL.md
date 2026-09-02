---
name: inherit-legacy-style
description: Codify the style of a hand-written legacy codebase into .ai-style-rules.md with Golden Files, Naming and State-Control Rules, and explicit DONTs. Use after codebase-onboarding when the project is hand-written and not yet consistent with LE conventions; do not impose LE defaults on legacy code.
---

# Inherit Legacy Style

Inherits `docs/SKILL_CONTRACT.md`.

When a project is hand-written and not yet consistent with LE conventions, this skill
captures the existing style as a set of rules the chain follows. The goal is **not
to modernise the codebase**; the goal is to make the chain behave like a long-time
contributor who knows the project's quirks.

## When to use

- A legacy project is being onboarded and `codebase-onboarding` produced an
  architecture index but the conventions are not the LE defaults.
- The chain keeps producing code that does not match the surrounding style
  (naming, error handling, logging, file layout).
- A team is migrating incrementally and the chain must not yank patterns out
  from under the in-flight work.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A greenfield project with LE defaults | `codebase-onboarding` only |
| A targeted refactor of one area | `code-reviewer` + `refactor-cleaner` |
| A security-only audit | `security-compliance` |

## Two Branches

### Branch A - first-time full scan

Run on a project that has no `.ai-style-rules.md` yet. The scan walks the project
in four dimensions:

| Dimension | What to extract |
|---|---|
| File anatomy | directory conventions, file naming, header comments, license block |
| State and control flow | sync vs async, error shape, how nulls are expressed, how state is threaded |
| Infrastructure | config loading, secrets, logging style, env access, dependency injection |
| Error handling | typed vs exceptions, where errors are caught, how they are reported, what the user sees |

Each dimension produces a list of **observed patterns** with one example
citation per pattern. Patterns without citation are dropped.

Then the rules:

| Rule type | Source |
|---|---|
| Golden Files | the 3-5 most idiomatic files in the project (named explicitly) |
| Naming Rules | file, function, class, variable, constant conventions |
| State-Control Rules | the chosen async model, error shape, null convention |
| DONTs | the 3-10 things that are wrong-but-stable, the chain must not "fix" |

### Branch B - incremental sniff

Run on a project that already has `.ai-style-rules.md`. The sniff:

- reads the existing rules;
- diffs the new code against the rules;
- reports which rules still hold, which are stale, and which new ones emerged.

The output is a small delta against the existing file, not a full rewrite.

## Output File

```markdown
# Style rules for <project>

## Source of truth
- Generated: <date>
- Branch: A (first-time) | B (incremental)
- Generator: /inherit-legacy-style

## Golden Files
- <path>: <why this is golden>
- <path>: <why>

## Naming
- Files: <observed convention with example>
- Functions: ...
- Classes: ...
- Variables: ...
- Constants: ...

## State and control flow
- Async model: <observed>
- Error shape: <observed>
- Null convention: <observed>

## Error handling
- Throws / returns: <observed>
- Boundary: <where the boundary is>
- User-facing format: <what the user sees>

## DONTs
- <thing that looks wrong but is stable; do not fix>
- <thing>

## Evolution log
- <date>: <change>
```

The file lives in the active workspace, not in the app:

```
.ai-style-rules.md     # in repo root
```

The chain reads the file before any code change. `AGENTS.md` #9 (minimal diffs,
match surrounding conventions) is enforced by this file.

## Anti-Patterns

- **Imposing LE defaults on a legacy project.** A chain that writes async/await
  into a synchronous codebase is a chain that has not read the file. Read the
  file.
- **Citing a pattern that is not actually common.** A pattern with one example
  is a single data point, not a convention. Require at least three observations
  before recording a rule.
- **Listing "DONTs" that are obvious.** "Do not commit secrets" is in every
  project; it is not a project-specific DONT. Reserve the section for
  project-specific things the chain has been tempted to "fix."
- **Treating the file as a refactor backlog.** The DONTs are not a punch list;
  they are the boundary. Refactors belong in their own work.
- **Updating the file on every commit.** The file is updated by `/inherit-legacy-style`
  Branch B, not by routine commits. Stable style rules do not change weekly.

## Related Skills

- `codebase-onboarding` - the parent workflow that triggers this when needed.
- `code-reviewer` - per-PR checks against the recorded style.
- `codebase-design` - the seam vocabulary that sits underneath style.