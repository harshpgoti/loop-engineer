"""Search public research-paper sources: arXiv, Research Square, SSRN.

Stdlib only, no vendoring, no scraping of sites that block automated access.

- arXiv: official Atom API (export.arxiv.org) - no key needed.
- Research Square: Crossref REST API filtered to Research Square's DOI prefix
  (10.21203, confirmed live: publisher field returns "Research Square Platform LLC").
- SSRN: no public search API, and papers.ssrn.com returns HTTP 403 to automated
  fetches on every endpoint tried. `ssrn_search_url()` only builds a best-effort
  browser URL (unverified) - open it yourself or fetch it with a tool that has
  browser-grade access.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

ARXIV_API = "http://export.arxiv.org/api/query"
RESEARCH_SQUARE_DOI_PREFIX = "10.21203"
CROSSREF_PREFIX_API = f"https://api.crossref.org/prefixes/{RESEARCH_SQUARE_DOI_PREFIX}/works"
SSRN_SEARCH_URL = "https://papers.ssrn.com/sol3/results.cfm"
USER_AGENT = "loop-engineer-research-search/1.0 (https://github.com/; mailto:none@example.com)"

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


@dataclass
class Paper:
    source: str
    title: str
    authors: str
    url: str
    published: str
    summary: str = ""

    def format(self) -> str:
        head = f"[{self.source}] {self.title}"
        lines = [head]
        if self.authors:
            lines.append(f"  authors: {self.authors}")
        if self.published:
            lines.append(f"  published: {self.published}")
        if self.url:
            lines.append(f"  url: {self.url}")
        return "\n".join(lines)


def _http_get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_arxiv_atom(body: bytes) -> list[Paper]:
    root = ET.fromstring(body)
    papers: list[Paper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        title = " ".join(title.split())
        summary = (entry.findtext("atom:summary", default="", namespaces=ATOM_NS) or "").strip()
        summary = " ".join(summary.split())
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS) or ""
        authors = ", ".join(
            (a.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
            for a in entry.findall("atom:author", ATOM_NS)
        )
        link = ""
        for l in entry.findall("atom:link", ATOM_NS):
            if l.get("rel") == "alternate":
                link = l.get("href", "")
                break
        if not link:
            link = entry.findtext("atom:id", default="", namespaces=ATOM_NS) or ""
        papers.append(Paper("arxiv", title, authors, link, published[:10], summary[:400]))
    return papers


def search_arxiv(query: str, limit: int = 10) -> tuple[bool, list[Paper], str]:
    params = {"search_query": f"all:{query}", "start": "0", "max_results": str(limit)}
    url = ARXIV_API + "?" + urllib.parse.urlencode(params)
    try:
        body = _http_get(url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        return False, [], str(e)
    try:
        papers = parse_arxiv_atom(body)
    except ET.ParseError as e:
        return False, [], f"invalid XML: {e}"
    return True, papers, f"{len(papers)} results"


def parse_crossref_items(payload: dict) -> list[Paper]:
    items = ((payload.get("message") or {}).get("items")) or []
    papers: list[Paper] = []
    for item in items:
        title = " ".join(item.get("title") or []) or "(untitled)"
        authors = ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in (item.get("author") or [])
        )
        doi = item.get("DOI", "")
        published = ""
        for date_field in ("published", "published-print", "published-online"):
            parts = ((item.get(date_field) or {}).get("date-parts") or [[]])[0]
            if parts:
                published = "-".join(str(p) for p in parts)
                break
        abstract = (item.get("abstract") or "").replace("<jats:p>", "").replace("</jats:p>", "").strip()
        papers.append(
            Paper(
                "researchsquare",
                title,
                authors,
                f"https://doi.org/{doi}" if doi else "",
                published,
                abstract[:400],
            )
        )
    return papers


def search_research_square(query: str, limit: int = 10) -> tuple[bool, list[Paper], str]:
    params = {
        "query": query,
        "rows": str(limit),
        "select": "DOI,title,author,published,published-print,published-online,abstract",
    }
    url = CROSSREF_PREFIX_API + "?" + urllib.parse.urlencode(params)
    try:
        body = _http_get(url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        return False, [], str(e)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        return False, [], f"invalid JSON: {e}"
    papers = parse_crossref_items(payload)
    return True, papers, f"{len(papers)} results"


def ssrn_search_url(query: str) -> str:
    """Best-effort SSRN search URL - NOT programmatically verified.

    papers.ssrn.com returns HTTP 403 to every automated fetch attempted
    (bot protection), so this cannot be confirmed the way arXiv/Crossref were.
    Open the URL in a browser, or fetch it with a tool that has browser-grade
    access, and read the results yourself.
    """
    return SSRN_SEARCH_URL + "?" + urllib.parse.urlencode({"npage": "1", "term": query})


SOURCES = ("arxiv", "researchsquare", "ssrn")


def search(
    query: str, sources: list[str] | None = None, limit: int = 10
) -> dict[str, tuple[bool, list[Paper], str]]:
    sources = sources or list(SOURCES)
    results: dict[str, tuple[bool, list[Paper], str]] = {}
    if "arxiv" in sources:
        results["arxiv"] = search_arxiv(query, limit)
    if "researchsquare" in sources:
        results["researchsquare"] = search_research_square(query, limit)
    if "ssrn" in sources:
        results["ssrn"] = (True, [], f"no public API - open manually: {ssrn_search_url(query)}")
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Search arXiv, Research Square, and SSRN.")
    parser.add_argument("query", help="Search terms")
    parser.add_argument(
        "--source",
        action="append",
        choices=SOURCES,
        dest="sources",
        help="Limit to one source (repeatable). Default: all.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Max results per source.")
    args = parser.parse_args(argv)

    results = search(args.query, args.sources, args.limit)
    exit_code = 0
    for source in args.sources or list(SOURCES):
        ok, papers, msg = results[source]
        print(f"== {source} ({msg}) ==")
        if not ok:
            exit_code = 1
        for paper in papers:
            print(paper.format())
            print()
        if not papers and ok and source != "ssrn":
            print("  (no results)")
        print()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
