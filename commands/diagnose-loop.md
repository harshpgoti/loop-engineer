# /diagnose-loop

Diagnose a hard bug or a performance regression by first building a feedback loop that
goes **red** on it, then hypothesising against that loop.

## How To Interpret

If the user says `/diagnose-loop`, `debug this`, `diagnose it`, `why is this failing`,
`it throws`, `it broke`, `it's flaky`, `it got slow`, or reports something not working,
execute this file directly.

Also run it, unasked, when a test that was green goes red and the cause is not obvious
from the diff - that is a diagnosis, not a fix.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone).
Read and write product-state files in the **active workspace**.

1. `AGENTS.md` - #6 sensitive data governs every command and log this skill produces
2. `skills/diagnose-loop/SKILL.md`
3. `CONTEXT.md` - the module vocabulary, so the report names things the way the repo does
4. `DECISIONS.md` - decisions in the area you are about to change
5. `plan/BUILD_CONTEXT.md` when a task is active
6. The failing output itself - not the whole test suite

## Loop

```text
SESSION-START -> BUILD A RED LOOP -> REPRODUCE -> MINIMISE -> HYPOTHESISE -> INSTRUMENT -> FIX + REGRESSION TEST -> CLEAN UP -> SESSION-END
```

## The one rule

**No red-capable command, no hypothesis.** Phase 1 of the skill ends when you can name one
command you have already run, that drives the real code path, asserts the reported symptom,
returns the same verdict every time, and finishes in seconds. Reading code to build a theory
before that command exists is the failure this command exists to prevent.

## Rules

- Redact every secret before showing a command, its output, or a captured artifact.
- Three to five ranked, falsifiable hypotheses before testing any of them.
- One variable per probe. Tag every debug log `[DEBUG-<id>]` so cleanup is one search.
- Performance work measures a baseline first, then bisects. Logs are the wrong tool there.
- The regression test goes red on the bug before the fix lands
  (`skills/tdd/SKILL.md`). A test never seen failing is evidence of nothing.
- No correct seam for the regression test? That is the finding. Record it - do not write a
  test that cannot fail.

## Continuation

Fixed and green → the active task resumes; `loop session-end` carries the finding.
Cannot build a loop without access, an environment, or a captured artifact → Stop Condition:
say what you tried, name what you need, record it with `loop doubts add`. See
`docs/CONTINUATION.md`.

## Output

1. The loop: the one command, and its output going red
2. The minimised repro
3. The ranked hypotheses, and which one survived
4. The fix, and the regression test that failed before it
5. Confirmation the probes are gone and the original repro is dead
6. The correct hypothesis, recorded in the commit and `memories/MEMORY.md`
