---
name: recursive-decision-ledger
description: Append-only ledger for repeated rollouts where a single decision recurs across sessions and the chain must record prior winners, fresh evidence, search space, and promotion gates. Use when the same architectural or product decision is revisited and the chain needs a structured, append-only record of how it arrived at the current answer.
---

# Recursive Decision Ledger

Inherits `docs/SKILL_CONTRACT.md`.

A small, append-only JSONL ledger that records every revisit of a recurring decision.
The ledger is the source of truth for "why did we pick this when we did, and what
changed since?" Future sessions read the ledger before re-deciding; new evidence
either refines the prior winner or replaces it through a promotion gate.

## When to use

- a decision is being revisited for the second, third, or Nth time;
- the prior decision was made in a session whose memory is no longer authoritative;
- the chain needs an audit trail of how the decision evolved;
- a one-shot `DECISIONS.md` entry is not enough - the rationale spans sessions.

## When NOT to use

| Instead of this ledger | Use |
|---|---|
| A new architectural decision | `architecture-decision-records` (`/adr`) |
| A tactical implementation choice | commit message, `TASKS.yml` |
| A one-off product strategy decision | `plan/main_plan.md` and `DECISIONS.md` |
| The same question repeating inside one session | `DOUBTS.md` |

## File Layout

The ledger lives in the active workspace, not in the app:

```
.loop/
  ledger/
    decisions.jsonl    # one JSON object per revisit, append-only
```

Each line is a self-contained JSON object. The file is append-only; never rewrite an
existing line. New lines either reaffirm the prior winner or attempt a promotion.

## Record Schema

```json
{
  "version": 1,
  "id": "<stable decision id, e.g. 'data-engineering' or 'auth-model'>",
  "session_id": "<session that made this revisit>",
  "timestamp": "<ISO 8601 with timezone>",
  "prior_winner": "<the prior decision's code, name, or short description>",
  "fresh_info": [
    "<piece of evidence or context the prior decision did not have>"
  ],
  "search_space": [
    "<alternative the chain considered this round>"
  ],
  "trial_count": <how many times this decision has been revisited, including this one>,
  "outcome": "reaffirm" | "promote" | "supersede",
  "new_winner": "<if outcome is promote or supersede, the new code, name, or short description>",
  "coherence_mark": "<short user- or agent-supplied note; often empty>",
  "approved_by": "<who approved the outcome; required for promote or supersede>"
}
```

`fresh_info` is the differentiator. A revisit with no new evidence should `reaffirm`,
not invent a new choice. A revisit with new evidence that does not change the answer
should `reaffirm` and record what the new evidence was (so the next session can see
the chain of evidence).

## Promotion Gate

A new choice replaces the prior winner only when **all** of these are true:

1. The new evidence (`fresh_info`) was not available at the time of the prior winner.
2. The new choice is recorded in `DECISIONS.md` or in an ADR with the same `id`.
3. The change is approved by a named approver (the user, a `release-manager` role, or
   a `product-manager` role when delegated).
4. The previous decision's status moves to `superseded` in the same operation; the
   prior winner is never silently dropped.

If any of these is missing, the new choice does not enter the ledger as `promote`. It
is recorded as a `fresh_info` entry on the next revisit, until the gate is satisfied.

## Workflow

### 1. Detect a recurring decision

A revisit is signalled when:

- the user says "we decided X before, do we still want X?" or similar;
- a plan or task references a prior decision by id;
- the chain's session-recall surfaces a prior decision whose evidence has changed.

If the decision is new, **stop** and use `/adr` instead.

### 2. Read the existing ledger

```bash
grep '"id": "<decision id>"' .loop/ledger/decisions.jsonl
```

The most recent line is the prior state. If no line exists, this is the first record;
the `prior_winner` is the prior decision recorded in `DECISIONS.md` or an ADR.

### 3. Determine the outcome

- `reaffirm` - the prior winner still holds; the new evidence does not change the
  answer. Record what the new evidence was.
- `promote` - a new choice wins; the prior is superseded. Requires the promotion gate.
- `supersede` - the prior winner is replaced by an explicit external decision (e.g.,
  the company was acquired, the framework was deprecated). The new winner is named
  by the external source.

### 4. Append one line

Append a single JSON object to `decisions.jsonl`. The line is the entire revisit; do
not split it across multiple lines.

### 5. Mirror to the canonical place

If the outcome is `promote` or `supersede`:

- update `DECISIONS.md` with the new choice, the old one, and a `Supersedes:` line;
- write or update the ADR (see `architecture-decision-records`);
- the prior winner's status moves to `superseded` everywhere it appears.

If the outcome is `reaffirm`: do not change `DECISIONS.md` or the ADR; the ledger line
is the record that the decision was re-examined and held.

## Sensitive Data

- Never include secrets, customer data, or PII in the ledger.
- Truncate URLs to the host when they may carry credentials or tokens.
- The ledger is debug-readable by anyone with workspace access; do not write what
  should not be visible.

## Anti-Patterns

- **Re-deciding without reading the prior.** A revisit that ignores the prior winner
  is a fresh decision in disguise; use `/adr` instead.
- **Promoting without evidence.** A `promote` outcome without `fresh_info` is an
  unsourced reversal; the promotion gate rejects it.
- **Silently dropping the prior winner.** A decision replaced without `Supersedes:`
  is a lie future readers will believe.
- **One big file per decision.** The ledger is a single JSONL file; each line is a
  revisit. Do not split into one file per id.
- **Recording the rationale in chat only.** The ledger is the durable record. If the
  revisit is not in `decisions.jsonl`, it did not happen.

## Related Skills

- `architecture-decision-records` - the canonical artifact for the decision body.
- `plan-loop/phases/council.md` - the venue for re-deciding under adversarial review.
- `session-recall` - surfaces prior decisions from `state.db`.
- `learn` - records agent-level observations about decisions, not the decisions
  themselves.