# Phase: Test

> Loaded by `skills/product-develop/SKILL.md` when `BUILD PHASE: test`.
> Load only this file.

## Purpose

Make the acceptance criteria in `plan/BUILD_CONTEXT.md` actually verifiable, and run them.

## Read First

1. `plan/BUILD_CONTEXT.md` - the task's `acceptance` list is the specification
2. `skills/qa-validation/SKILL.md`
3. `docs/TEST_PLAN.md`, `docs/ACCEPTANCE_CRITERIA.md` when they exist
4. Active feature `tasks.md`

## Process

1. **Test the acceptance criteria, not the implementation.** Each line under
   `acceptance:` should map to at least one test.
2. **Run what exists** before writing more - a failing existing test is a higher
   priority than a new one.
3. **Record the real result.** A skipped suite is reported as skipped, never as
   passing (`AGENTS.md` #10).
4. **Fix or file.** A failure you cannot fix without a product decision becomes a
   doubt: `loop doubts add`, marked blocking, with what it holds up.

## Continue automatically

- **Green** -> continue into `phases/converge.md`; do not stop to report a pass.
- **Red, and the fix is technical** -> fix it here, in this session.
- **Red, and the fix needs a product decision** -> Stop Condition. Name the failure and
  the decision required.

## Output

Suites run and their real results, tests added, failures fixed, anything filed as a doubt.
