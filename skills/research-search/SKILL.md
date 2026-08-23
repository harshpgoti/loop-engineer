---
name: research-search
description: Search arXiv, Research Square, and SSRN for published research to ground product, architecture, or agent-design claims in evidence. Use for /research-search, fact-checking during /plan-loop, or literature grounding during agent-builder work.
---

# Research search skill

Search public research-paper sources without vendoring a scraper or paying for an aggregator API.

## When to use

- `/plan-loop` step 8 ("Validate claims with sources") when a claim is research-grounded, not just a vendor doc or product page.
- `skills/agent-builder/SKILL.md` when justifying an agent architecture, evaluation method, or safety pattern with published work.
- Any time the user asks to search arXiv, SSRN, or Research Square directly.

## Sources and how each works

| Source | Method | Coverage |
|--------|--------|----------|
| arXiv | Official Atom API (`export.arxiv.org/api/query`) - no key | CS/physics/math/stats preprints |
| Research Square | Crossref REST API filtered to DOI prefix `10.21203` - no key | Multidisciplinary preprints |
| SSRN | **No public API.** `papers.ssrn.com` returns HTTP 403 to every automated fetch attempted. `ssrn_search_url()` only builds a best-effort browser URL - open it yourself or fetch with a tool that has browser-grade access. Do not attempt to bypass its bot protection. | Social science, law, economics preprints |

## Commands

```bash
loop research "<query>"                          # all three sources
loop research "<query>" --source arxiv
loop research "<query>" --source researchsquare
loop research "<query>" --source ssrn            # prints a search URL only
loop research "<query>" --limit 20
python scripts/research_search.py "<query>" --source arxiv --limit 5
```

Importable: `scripts/research_search.py` exposes `search(query, sources=None, limit=10) -> dict[str, (ok, papers, message)]`.

## Follow every claim to the source that owns it

Investigate against **primary** sources: the paper, the specification, the regulator's own
text, the vendor's own API docs, the source code. A blog post summarising a study, an
analyst's write-up of a survey, a comparison article - each is somebody else's reading, and
the number you need is usually a paraphrase of a paraphrase.

When a secondary source is all you have, cite it as one and say so. `EVIDENCE_LOG.md` treats a
claim's confidence as real; a secondary citation recorded as a verified fact quietly launders
somebody's summary into your plan.

The tell that you have not reached the source yet: you can quote the figure but cannot say
what was measured, on whom, or when.

## Rules

- Cite the returned `url` (arXiv abstract page or DOI link) in `EVIDENCE_LOG.md` - never just the search query.
- Treat SSRN results as unverified until a human opens the link; do not report SSRN paper titles you have not actually seen.
- Prefer arXiv/Research Square for anything with a DOI or arXiv ID; only fall back to a general web search when neither source has coverage.
- This is a read-only literature lookup, not a citation-formatting or PDF-fetching tool - fetch the actual PDF/abstract with `WebFetch` only if the content itself is needed.

## Output

- Per-source result count and list of papers (title, authors, published date, url).
- Non-zero exit if any requested source's fetch failed (network/HTTP error) - check the printed message.
