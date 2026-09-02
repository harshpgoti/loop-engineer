# /council-multi-model

Run an external-model critique on a council decision. Labels the provider
relationship honestly, requires explicit consent, and degrades to a
"review absent" branch on failure. Use after a council decision that needs
an outside check.

## How To Interpret

If the user says `/council-multi-model`, `external critique`, `cross-provider
review`, or asks for an outside check on a council decision, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/council-multi-model/SKILL.md`
3. `plan/COUNCIL_BUNDLE.json` (the prior council output)
4. `skills/safeguard/SKILL.md`

## Loop

```text
LOAD the council bundle -> NAME host, reviewer, label, cost -> CONSENT gate -> WRAP draft in untrusted-data envelope -> RUN review -> UPDATE synthesis
```

## Output

`plan/COUNCIL_MULTI_MODEL.md` with the locked provider-relationship label,
the cost estimate, the reviewer's response, and the updated synthesis
naming what the external critique changed.

A `review absent` branch is the default; a successful review is the
explicit opt-in. The chain does not pretend a review happened.

## Continuation

A `review absent` outcome is recorded as such; the original council
verdict stands. A `cross-provider external critique` outcome updates the
synthesis and lands the decision in `DECISIONS.md` or an ADR.