---
name: competitive-platform-analysis
description: Run a structured competitive analysis: identify direct / indirect / substitute competitors, map wedges and advantages, surface positioning. Use during early planning, before a pivot, or when the chain needs the market view alongside the technical view.
---

# Competitive Platform Analysis

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for competitive analysis. The skill
produces a competitor table with a clear wedge per competitor, an
advantage-or-disadvantage summary, and a positioning recommendation.
Every claim is cited; no claim is unsourced.

## When to use

- Early planning, when the chain needs the market view alongside
  the technical view.
- Before a pivot, when the chain is considering a new wedge.
- When the user asks "who are our competitors" or "what's our
  positioning" or "are we different from X."
- As a periodic maintenance signal: a quarterly competitive review
  to catch new entrants.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A market size estimate (TAM/SAM/SOM) | `market-research` |
| A product strategy decision | `product-manager` role |
| A sales pitch | out of LE's scope |

## The Three-Layer Map

| Layer | Definition | Example |
|---|---|---|
| **Direct** | Same product, same wedge, same user | A competing CRUD app for the same role |
| **Indirect** | Different product, same job | A spreadsheet solving the same user job |
| **Substitute** | No product, manual workflow | A team doing the work by hand |

A direct competitor is the hardest to differentiate from. An
indirect competitor is the most dangerous when the user is "good
enough" with the indirect. A substitute is the most dangerous when
the manual workflow is "free" and the new product has a cost.

## Workflow

### 1. State the wedge

One sentence: who is the user, what is the job, what is the
alternative, what is the advantage. The wedge sharpens the
competitor map.

### 2. Discover competitors

For each layer (direct, indirect, substitute), the chain lists
candidates. The list is built from:

- The user's own knowledge (informs `market-research`).
- `research-search` for arXiv / SSRN papers in the same area.
- Vendor comparison sites (G2, Capterra, etc. — the chain
  surfaces a list, the user verifies).
- The chain's prior `market-research` output (when present).

### 3. Map the wedge and the advantage

For each competitor, the chain records:

- **Their wedge** — who they serve, what they sell.
- **Their advantage** — what they do better than us.
- **Their disadvantage** — what they do worse than us.
- **Our position** — why a user would pick us over them.

The table is in `plan/COMPETITIVE.md`.

### 4. Synthesise positioning

A one-paragraph positioning statement that names the user, the
job, the alternative, and the advantage. The positioning drives
every downstream decision (marketing, sales, product).

## Output

A single Markdown table with one row per competitor, plus a
positioning paragraph at the top.

```markdown
# Competitive Map

## Positioning
<one paragraph: user, job, alternative, advantage>

## Competitors
| Name | Layer | Their wedge | Their advantage | Their disadvantage | Our position |
|------|-------|-------------|-----------------|--------------------|--------------|
| ... | direct / indirect / substitute | ... | ... | ... | ... |

## Sources
- <one URL or citation per competitor>
```

## Anti-Patterns

- **A competitive map with no sources.** A claim without a citation
  is a guess; the user cannot verify or update it.
- **A map that lists only direct competitors.** The most dangerous
  competitor is often an indirect or substitute. A map of just
  direct competitors is a self-comforting document.
- **A map that never updates.** Competitive maps go stale fast. The
  skill is for a periodic refresh, not a one-shot.
- **A map that conflates feature comparison with competitive
  positioning.** Feature comparison is "X has Y, we don't"; competitive
  positioning is "X serves A, we serve B." The former is a
  spreadsheet; the latter is strategy.

## Related Skills

- `market-research` - the market sizing skill; this skill is the
  competitor mapping.
- `product-manager` - the role that owns positioning; this skill
  is the data source.
- `plan-loop` - the planning chain; the competitive map feeds
  the wedge and the kill criterion.