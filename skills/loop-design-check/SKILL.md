---
name: loop-design-check
description: Design quality check for any closed loop in the chain (build-test-fix cycle, eval-driven TDD, gan-eval, council feedback). Applies a 5-failure-mode review (anti-Goodhart, missing boundaries, no fallback, no layering, no reconciliation). Use before locking a new loop, when a loop is misbehaving, or as a scheduled review.
---

# Loop Design Check

Inherits `docs/SKILL_CONTRACT.md`.

A short checklist for designing or auditing a closed loop. Loops fail in
predictable ways; the five questions below are the diagnostic. The skill is
named after a Norbert Wiener reference: useful loops are designed, not
discovered.

## When to use

- A new loop is being designed (eval-driven TDD, GAN eval, build-fix loop,
  continuous PR).
- A loop is misbehaving and the cause is not obvious from a single iteration.
- Before locking a new loop into the chain as a stage.
- As a scheduled review of the loops currently in the chain.

## When NOT to use

- A one-shot task that does not loop.
- A loop whose design is already well-known and tested in the chain
  (`/plan-loop`, `/develop-product`).

## The 5-Question Review

Each question is a fail-mode; a pass requires all five.

### 1. Is the done-criterion machine-verifiable?

The loop has to terminate on an **observable**, **deterministic** signal. A
vague "looks right" is not a signal. "Tests pass" is. "Eval score >= 7.0"
is. "Approved by reviewer" is, if the reviewer is the loop's only writer.

A loop with a non-machine-verifiable done-criterion is a human-in-the-loop
masquerading as an autonomous loop. Make the human explicit, or change the
criterion.

### 2. Are the boundary conditions defined alongside the done-criterion?

The done-criterion names what the loop must achieve. The boundaries name what
the loop must NOT do. Without boundaries, the loop is free to "achieve" the
done-criterion by cheating.

Boundaries are usually phrased as inputs the loop must reject, states it
must not enter, or behaviours it must not exhibit. Anti-Goodhart: do not
let a metric become the target.

### 3. Does the loop have a failure fallback?

A loop that retries forever is broken. A loop that retries N times then
escalates to a human is correct. A loop that retries N times and then
silently passes is a bug.

The fallback answers: what happens when the loop cannot reach its
done-criterion? The answer is: do this, then escalate.

### 4. Is the goal layered?

A single goal is brittle. A loop with one goal is one bug away from being
useless. Layered goals: "pass the unit test" then "pass the integration
test" then "pass the eval" then "pass the council review" then "ship."

The layering is a hierarchy of trust: the lowest level is the strongest
signal, the highest is the weakest. A loop that achieves only the lowest
level is still useful; a loop that achieves only the highest is vanity.

### 5. Does the loop reconcile against an external anchor?

The loop's verdict must be reconciled against something **outside** the loop.
A test that passes because the test was wrong is not a test that passed.
A eval score that improved because the eval was gamed is not an improvement.

Reconciliation anchors: golden samples, upstream totals, financial
tie-out, platform back-office numbers, customer-reported reality. The
anchor is the proof that the loop's verdict is not an illusion.

## Pass / Fail Outcomes

```markdown
## Loop design check: <loop name>

| # | Question | Pass / Fail | Evidence |
|---|----------|-------------|----------|
| 1 | Done-criterion machine-verifiable | <yes/no> | <one-line> |
| 2 | Boundaries defined | <yes/no> | <one-line> |
| 3 | Failure fallback | <yes/no> | <one-line> |
| 4 | Goal layered | <yes/no> | <one-line> |
| 5 | External anchor | <yes/no> | <one-line> |

## Verdict
- Pass: all five yes.
- Conditional: 1-2 nos; record the conditions and the rationale.
- Fail: 3+ nos; the loop is not ready; re-design.
```

## Anti-Patterns

- **A loop with a human in the loop, hidden.** "Approve" is a stop condition,
  not a done-criterion. The human is the boundary; name them.
- **A loop that overfits to its eval.** The loop is right when the eval is
  *one of several* signals, not the only one. Reconciliation against an
  external anchor is the only defence.
- **A loop that retries forever.** "Try harder" is not a fallback. The
  fallback escalates.
- **A loop that does not write its own state.** A loop that re-derives its
  state from scratch on every iteration is a loop that pays the full cost
  every time. Persist between iterations.
- **A loop named after a verb, not a noun.** "Improve" is a verb. "Build-test-
  ship" is a noun. The loop is a thing that runs, not a thing the agent does.

## Related Skills

- `agent-architecture-audit` - 12-layer stack diagnostic for agent failures.
- `council` - adversarial review of a loop's design.
- `gan-style-harness` - the canonical closed-loop harness.
- `eval-harness` - the eval-driven discipline the loop relies on.