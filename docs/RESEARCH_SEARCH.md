# Research search

Loop Engineer can search public research-paper sources to ground product, architecture, or agent-design claims in evidence — without vendoring a scraper or paying for an aggregator API.

## Sources

| Source | Method | Verified | Coverage |
|--------|--------|----------|----------|
| arXiv | Official Atom API (`export.arxiv.org/api/query`) — no key | Confirmed live: `search_query=all:<term>` returns real results | CS/physics/math/stats preprints |
| Research Square | Crossref REST API filtered to DOI prefix `10.21203` — no key | Confirmed live: prefix `10.21203` returns "Research Square Platform LLC" publisher, and `query=` filters correctly | Multidisciplinary preprints |
| SSRN | **No public API.** `papers.ssrn.com` returned HTTP 403 on every automated fetch attempted during implementation (bot protection on `/sol3/DisplayAbstractSearch.cfm`, `/sol3/results.cfm`, `/index.cfm/en/`) | Not verified — URL builder only | Social science, law, economics preprints |

## Commands

```bash
loop research "<query>"                 # all three sources
loop research "<query>" --source arxiv
loop research "<query>" --source researchsquare
loop research "<query>" --source ssrn   # prints a search URL only, does not fetch
loop research "<query>" --limit 20
```

Importable: `scripts/research_search.py` — `search(query, sources=None, limit=10)` returns `{source: (ok, [Paper, ...], message)}`.

## Why SSRN is URL-only

SSRN actively blocks automated fetches (confirmed by repeated 403s across every endpoint tried). Rather than attempt to bypass its bot protection — which would edge into detection-evasion territory this project avoids — `ssrn_search_url(query)` builds a best-effort browser search URL from the historically documented pattern (`papers.ssrn.com/sol3/results.cfm?npage=1&term=<query>`). This is **not** programmatically verified. Open it in a browser, or fetch it with a tool that has browser-grade access, and read the results yourself before citing anything from SSRN.

## Rules

- Cite the returned `url` (arXiv abstract page or `https://doi.org/<doi>`) in `EVIDENCE_LOG.md` — never just the search term.
- Never report SSRN results you have not actually seen — the tool only gives you a URL to check manually.
- Prefer arXiv/Research Square when the claim has a DOI or arXiv ID; fall back to a general web search only when neither source has coverage.

## Wiring

- `/plan-loop` step 8 ("Validate claims with sources") uses this for research-grounded claims.
- `skills/agent-builder/SKILL.md` step 7 uses this to ground non-obvious agent-architecture/eval/safety claims.
- `/research-search` runs it directly.
