# /research-search

Search arXiv, Research Square, and SSRN for published research to ground a claim in evidence.

## How To Interpret

If the user says `/research-search`, `research search`, `search arxiv`, `search papers`, `find research on`, or asks to look up published research/literature on a topic, execute this file directly.

## Required Reads

1. `skills/research-search/SKILL.md`

## One-shot commands

```bash
loop research "<query>"
loop research "<query>" --source arxiv
loop research "<query>" --source researchsquare
loop research "<query>" --source ssrn
loop research "<query>" --limit 20
```

## Rules

- Cite the returned URL in `EVIDENCE_LOG.md`, not just the search term.
- SSRN has no public API — `--source ssrn` only prints a search URL (unverified; SSRN blocks automated fetches). Open it yourself; do not report SSRN results you have not actually read.
- Prefer this over a generic web search when the claim is research-grounded (architecture pattern, eval methodology, benchmark result, safety finding).

## Output

Per-source result count and paper list (title, authors, published date, URL). Non-zero exit if a requested source's fetch failed.

## Handoff

Add cited sources to `EVIDENCE_LOG.md` when the result informs a product, architecture, or agent-design decision.
