# /competitive-platform-analysis

Run a structured competitive analysis: identify direct / indirect /
substitute competitors, map wedges and advantages, surface positioning. Use
during early planning, before a pivot, or as a periodic maintenance signal.

## How To Interpret

If the user says `/competitive-platform-analysis`, `competitor analysis`, `market
map`, `who are our competitors`, `positioning`, or asks for the competitive view,
execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/competitive-platform-analysis/SKILL.md`
3. the user's current product (the wedge is implicit in their ask)
4. the prior `market-research` output (when present)

## Loop

```text
STATE the wedge -> DISCOVER competitors (direct / indirect / substitute) -> MAP wedge + advantage per competitor -> SYNTHESISE positioning -> EMIT plan/COMPETITIVE.md
```

## Output

A single Markdown file with the positioning statement, the
competitor table, and the sources. Every claim is cited.

## Continuation

The competitive map feeds `/plan-loop` (the wedge and the kill
criterion) and `/product-manager` (positioning). The map is updated
quarterly; stale maps are Stop Conditions in the next release.