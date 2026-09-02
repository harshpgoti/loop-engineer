---
name: market-research
description: Run market research for a new product or pivot. Defines TAM/SAM/SOM sizing, competitor analysis, customer interview synthesis, positioning. Use during the early planning phase, when validating a wedge, or when preparing a pivot.
---

# Market Research

Inherits `docs/SKILL_CONTRACT.md`.

A discipline for sizing a market, identifying competitors, and synthesising
customer interviews into a positioning. The skill produces evidence-backed
inputs for the product plan, not opinions. A market-research output that
cannot cite its sources is a market-research output that should be
discarded.

## When to use

- A new product is being planned and the chain needs to know whether
  the wedge is large enough.
- A pivot is being considered and the chain needs the evidence for
  the new direction.
- A go/no-go decision requires a market size estimate.
- The product plan needs a competitor analysis.
- A customer-interview corpus needs to be synthesised into a
  positioning.
- A wedge-sharpening session needs to know who the buyer is, what
  they pay for today, and what would change their mind.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A technical architecture decision | `architect` |
| A feature priority inside an existing product | `product-manager` |
| A go-to-market execution | (out of scope; LE is product engineering) |
| A sales pitch | (out of scope) |

## Required method

1. **State the wedge.** One sentence: who is the user, what do they
   pay for today, and what would change their mind. The wedge
   sharpens the rest of the research.
2. **Size the market.** TAM (top-down), SAM (bottom-up, your reachable
   slice), SOM (your realistic year-1 share). Cite the source for
   every number; an unsourced market size is a guess.
3. **Identify the competitors.** Direct (same product, same wedge),
   indirect (different product, same job), substitute (no
   product, manual workflow). For each, name the wedge and the
   advantage.
4. **Interview the customers.** 5-10 conversations, structured
   around the wedge. Record the verbatim quotes; the
   paraphrase is the second-order artefact.
5. **Synthesise the positioning.** One sentence: who is the user,
   what is the job, what is the alternative, what is the advantage.
   The positioning drives every downstream decision.
6. **Identify the kill criterion.** The number below which the
   chain recommends stopping. A market research output that does
   not name a kill criterion is one that the user can always
   argue with.

## Validation

- **Source citation** for every market number. A claim without a
  source is a guess; the chain records the source or drops the
  claim.
- **Verbatim quotes** for every customer interview insight. The
  paraphrase may be wrong; the verbatim is the evidence.
- **Independent review** by a non-author. A market-research
  output that only the author has read is one that has not been
  tested.
- **Kill-criterion test.** If the chain's number is below the
  kill criterion, the chain recommends stopping. A research
  output that does not name a kill criterion is one that the
  user can always argue with.

## Output

- TAM / SAM / SOM with citations
- Competitor analysis (direct, indirect, substitute) with
  wedges and advantages
- Customer interview synthesis with verbatim quotes
- Positioning statement
- Kill criterion
- Findings (with the Pre-Report Gate applied)
- Open questions for the next round of research

## Anti-Patterns

- **A market size without a source.** A TAM number is a guess
  until it has a citation; the chain records the source or drops
  the claim.
- **"Everyone is the customer."** A market research output that
  does not name a specific user is one that does not name a
  wedge. The wedge is the discipline.
- **Competitors named without a wedge.** "Competitor X" is a label;
  "Competitor X's wedge is Y, our advantage is Z" is a finding.
- **A positioning that does not name an alternative.** A
  positioning that says "we are the best" is a press release; a
  positioning that says "we are the best for user Y, job J,
  vs alternative A" is a strategy.
- **A market research output that reads as a sales pitch.** A
  research output that is optimistic by default is one that
  cannot be the input to a go/no-go decision. The output names
  the kill criterion; the user decides.
- **A kill criterion that the user can always argue with.** A
  kill criterion that is too soft is one that does not exist.
  The kill criterion is a number the chain and the user agreed
  to before the research started.

## Related Skills

- `product-manager` - the in-product priority; this skill is the
  out-of-product market view.
- `research-search` - the arXiv/SSRN literature search; this skill
  is the customer + competitor view.
- `architecture-decision-records` - the durable record; the
  positioning and kill criterion are recorded as ADRs.
- `plan-loop` - the planning chain; this skill feeds it.