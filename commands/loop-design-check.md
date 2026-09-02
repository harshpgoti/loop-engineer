# /loop-design-check

Apply a 5-failure-mode review to a closed loop's design. Use before locking a
new loop, when a loop is misbehaving, or as a scheduled review.

## How To Interpret

If the user says `/loop-design-check`, `check the loop`, `is this loop safe`,
or asks whether a loop is well-designed, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/loop-design-check/SKILL.md`
3. the loop's spec or `commands/<loop>.md`
4. the loop's eval or test suite, when present

## Loop

```text
IDENTIFY loop -> 5-QUESTION REVIEW -> PASS / CONDITIONAL / FAIL VERDICT
```

The 5 questions:

1. Is the done-criterion machine-verifiable?
2. Are boundary conditions defined alongside the done-criterion?
3. Does the loop have a failure fallback?
4. Is the goal layered?
5. Does the loop reconcile against an external anchor?

## Output

`plan/LOOP_DESIGN_CHECK.md` with the locked verdict:

- All 5 yes -> Pass.
- 1-2 nos -> Conditional; record the conditions.
- 3+ nos -> Fail; the loop is blocked; re-design.

## Continuation

A Pass means the loop is ready to run. A Conditional means the loop is
allowed to run with named conditions; the conditions land in
`DOUBTS.md`. A Fail means the loop is blocked; re-design before
re-running.