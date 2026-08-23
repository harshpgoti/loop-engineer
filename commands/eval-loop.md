# /eval-loop

Score the product's golden cases, record the run, find what regressed, and let the
failure pattern decide what to build next.

## How To Interpret

If the user says `/eval-loop`, `run the evals`, `score the eval set`, `did that make
it worse`, `why is the eval gate blocked`, or asks whether a model or prompt change
helped, execute this file directly.

Also run it, unasked, after any change to **agent behaviour** - a prompt, a model, a
tool definition, a retrieval strategy. Code review and unit tests do not see those.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone).
Read and write product-state files in the **active workspace**.

1. `AGENTS.md`
2. `skills/eval-loop/SKILL.md`
3. `plan/SESSION_MANIFEST.md` → the `## Evals` block when present
4. `plan/EVAL_ANALYSIS.md` (previous run's failures, grouped)
5. `agent/AGENT_ARCHITECTURE.md` → eval plan
6. The failing cases only - not every case file

## Loop

```text
SESSION-START -> SCORE CASES -> RECORD RUN -> COMPARE -> ANALYSE -> DECIDE ONE THING -> BUILD -> SESSION-END
```

## Scripts

```bash
loop eval                 # cases, last score, gate status, regressions
loop eval cases           # discovered case ids, by suite
loop eval record <file>   # persist a scored run: {"case-id": {"pass": bool, "kind": ..., "why": ...}}
loop eval analyse         # write plan/EVAL_ANALYSIS.md
```

The harness does not define a case format. Any JSON list of objects with an `id`
under `agent/evals/` is a suite - keep whatever domain fields the product needs.

## Gate Check

An eval gate is satisfied by a recorded run: every case exercised, score at or above
the threshold. Not by a claim that the work looks done.

A **regression blocks build work** the same way a failing test does. Fix it in the
session that caused it.

## Rules

- Deterministic checks before LLM-as-judge, judged before human (`AGENTS.md` #4).
- A failing judged or human verdict must record **why** - the harness rejects one
  that does not.
- New cases come from observed failures, not from imagination.
- Never raise a score by deleting a failing case or moving the threshold. If the bar
  is wrong, change it in `DECISIONS.md` with the reason.

## Continuation

Green with no regressions → continue the pipeline. Regressions present → fixing them
is the work of this session. A failure that needs a product decision is a Stop
Condition: name the case, both candidate behaviours, and what you need. See
`docs/CONTINUATION.md`.

## Output

1. Score and how it moved since the previous run
2. What regressed and what was fixed
3. The dominant failure category, and what you concluded from it
4. The one change you made as a result
5. Gate status and the next command
