# /decision-ledger

Append a revisit to the recursive decision ledger. Use when a recurring decision is
being re-examined and the chain needs an audit trail of how it arrived at the current
answer.

## How To Interpret

If the user says `/decision-ledger`, `append a revisit`, `record this revisit`, or asks
to log a re-examination of a prior decision, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/recursive-decision-ledger/SKILL.md`
3. `.loop/ledger/decisions.jsonl` (existing ledger)
4. `DECISIONS.md`
5. `docs/adr/` (the canonical ADRs)
6. `state.db` (search for prior revisits of the same id)

## Loop

```text
READ LEDGER -> DETERMINE OUTCOME (reaffirm | promote | supersede) -> APPEND ONE LINE -> MIRROR TO DECISIONS.MD AND/OR ADR
```

## Output Schema (locked, one JSON object per line)

```json
{
  "version": 1,
  "id": "<stable decision id>",
  "session_id": "<session that made this revisit>",
  "timestamp": "<ISO 8601 with timezone>",
  "prior_winner": "<short description>",
  "fresh_info": ["<piece of evidence>"],
  "search_space": ["<alternative considered>"],
  "trial_count": <int>,
  "outcome": "reaffirm | promote | supersede",
  "new_winner": "<if outcome is promote or supersede>",
  "coherence_mark": "<short note>",
  "approved_by": "<required for promote or supersede>"
}
```

## Promotion Gate

A new choice replaces the prior winner only when **all** are true:

1. The new evidence (`fresh_info`) was not available at the prior decision.
2. The new choice is recorded in `DECISIONS.md` or in an ADR with the same `id`.
3. The change is approved by a named approver.
4. The prior winner's status moves to `superseded` everywhere it appears.

If any is missing, the new choice does not enter as `promote`. Record it as
`fresh_info` on the next revisit until the gate is satisfied.

## Continuation

`reaffirm` → no further action; the ledger line is the record.
`promote` / `supersede` → mirror to `DECISIONS.md` and/or ADR, mark prior as superseded.

## Output

1. The appended ledger line
2. The mirrored updates to `DECISIONS.md` and/or ADR (if any)
3. The next action (if a promotion gate was missing)