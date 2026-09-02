# /recursive-decision-ledger

Append a revisit to the recursive decision ledger. Use when a recurring
decision is being re-examined and the chain needs an audit trail of how it
arrived at the current answer.

## How To Interpret

If the user says `/recursive-decision-ledger`, `append a revisit`, `record this
revisit`, or asks to log a re-examination of a prior decision, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/recursive-decision-ledger/SKILL.md`
3. `<workspace>/.loop/ledger/decisions.jsonl` (the existing ledger)

## Loop

```text
READ the existing ledger -> DETERMINE outcome (reaffirm | promote | supersede) -> APPEND one line -> MIRROR to DECISIONS.md and/or ADR
```

## Output

A single line appended to `<workspace>/.loop/ledger/decisions.jsonl` and
a one-line update to `<workspace>/DECISIONS.md` (when the outcome is
promote or supersede).

## Continuation

The next session reads the ledger before any decision. A prior answer
that was reaffirmed is the default; a prior answer that was superseded
is the resolved answer; a prior answer that was deferred is a Stop
Condition for the next revisit.