# /inherit-legacy-style

Codify the style of a hand-written legacy codebase into `.ai-style-rules.md`. Use
after `codebase-onboarding` when the project is hand-written and not yet consistent
with LE conventions.

## How To Interpret

If the user says `/inherit-legacy-style`, `capture legacy style`, `codify this
codebase's quirks`, or asks the chain to behave like a long-time contributor on a
legacy project, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/inherit-legacy-style/SKILL.md`
3. `docs/ONBOARDING.md` (when present)
4. existing `.ai-style-rules.md`, if any
5. the project's source tree

## Loop

```text
DETECT existing .ai-style-rules.md -> Branch A (first-time) | Branch B (incremental sniff) -> WRITE .ai-style-rules.md
```

## Branch A (first-time)

1. Walk four dimensions: file anatomy, state and control flow, infrastructure,
   error handling.
2. Cite `file:line` for every observed pattern; drop uncited patterns.
3. Identify 3-5 Golden Files (most idiomatic in the project).
4. List Naming, State-Control, and explicit DONTs.

## Branch B (incremental)

1. Read existing rules.
2. Diff new code against the rules.
3. Emit a small delta: which rules still hold, which are stale, which new ones
   emerged.

## Output

`.ai-style-rules.md` in the active workspace, with:

- Source of truth block (date, branch, generator)
- Golden Files
- Naming / State / Error handling / DONTs
- Evolution log

## Continuation

The chain reads `.ai-style-rules.md` before any code change. Subsequent
`/code-reviewer` runs cite the file when a rule is enforced.