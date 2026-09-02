# /market-research

Run market research for a new product or pivot. Use during the early planning
phase, when validating a wedge, or when preparing a pivot.

## How To Interpret

If the user says `/market-research`, `size the market`, `competitor analysis`,
`customer interviews`, or asks for a market view, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/market-research/SKILL.md`
3. `plan/main_plan.md` (the current product)
4. `EVIDENCE_LOG.md` (existing research)
5. `DECISIONS.md` (existing positioning)

## Loop

```text
STATE the wedge -> SIZE TAM/SAM/SOM with sources -> IDENTIFY direct/indirect/substitute competitors -> INTERVIEW customers (verbatim quotes) -> SYNTHESISE positioning -> NAME the kill criterion
```

## Output

- TAM / SAM / SOM with citations
- Competitor analysis (direct, indirect, substitute)
- Customer interview synthesis with verbatim quotes
- Positioning statement
- Kill criterion
- Findings (with the Pre-Report Gate applied)
- Open questions for the next round of research

## Continuation

The positioning and kill criterion are durable and become ADRs (see
`architecture-decision-records`). The TAM/SAM/SOM feeds `plan/main_plan.md`.
The competitor analysis feeds the wedge-sharpening round in `plan-loop`.