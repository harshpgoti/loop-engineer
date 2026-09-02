# /tdd

Run the TDD discipline: test the behaviour through the interface, not around
it. RED -> GREEN -> REFACTOR. The skill is wired into the chain; this
command is for direct invocation when the user wants a focused TDD pass.

## How To Interpret

If the user says `/tdd`, `red-green-refactor`, `write the test first`, or
asks for a TDD discipline pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/tdd/SKILL.md`
3. the active task's acceptance criteria
4. the test runner configuration

## Loop

```text
READ acceptance -> WRITE failing test (RED) -> IMPLEMENT minimum passing change (GREEN) -> REFACTOR -> COMMIT checkpoints
```

## Output

- Failing test (with the spec it covers)
- Minimum implementation
- Refactor notes
- Test commit (RED) and fix commit (GREEN) and refactor commit (REFACTOR) identifiers
- Coverage delta

A test that does not clear the tdd bar (interface-level, behaviour-level,
not implementation-coupled) is a finding — not the test, the test's
contract.

## Continuation

The TDD discipline is the bar `AGENTS.md` #10 is measured against. A task
without a TDD-grade test is not done.