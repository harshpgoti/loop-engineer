"""Tests for research_search.py parsing/dispatch logic (no live network calls).

Run: python scripts/test_research_search.py
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import research_search as rs

SAMPLE_ARXIV_ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2101.00001v1</id>
    <title>  Attention Is All You Need Again
    Revisited  </title>
    <summary>  A follow-up study on
    transformer attention mechanisms.  </summary>
    <published>2021-01-01T00:00:00Z</published>
    <author><name>Ada Lovelace</name></author>
    <author><name>Alan Turing</name></author>
    <link rel="alternate" href="http://arxiv.org/abs/2101.00001v1"/>
    <link title="pdf" rel="related" href="http://arxiv.org/pdf/2101.00001v1"/>
  </entry>
</feed>"""

SAMPLE_CROSSREF_PAYLOAD = {
    "message": {
        "items": [
            {
                "DOI": "10.21203/rs.3.rs-123456/v1",
                "title": ["Cross-sectional study of agentic workflows"],
                "author": [{"given": "Grace", "family": "Hopper"}],
                "published": {"date-parts": [[2023, 5, 1]]},
                "abstract": "<jats:p>An abstract about agentic workflows.</jats:p>",
            }
        ]
    }
}


class TestParseArxivAtom(unittest.TestCase):
    def test_parses_entry_fields(self) -> None:
        papers = rs.parse_arxiv_atom(SAMPLE_ARXIV_ATOM)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper.source, "arxiv")
        self.assertEqual(paper.title, "Attention Is All You Need Again Revisited")
        self.assertIn("transformer attention", paper.summary)
        self.assertEqual(paper.authors, "Ada Lovelace, Alan Turing")
        self.assertEqual(paper.published, "2021-01-01")
        self.assertEqual(paper.url, "http://arxiv.org/abs/2101.00001v1")

    def test_empty_feed(self) -> None:
        empty = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
        self.assertEqual(rs.parse_arxiv_atom(empty), [])


class TestParseCrossrefItems(unittest.TestCase):
    def test_parses_research_square_item(self) -> None:
        papers = rs.parse_crossref_items(SAMPLE_CROSSREF_PAYLOAD)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper.source, "researchsquare")
        self.assertEqual(paper.title, "Cross-sectional study of agentic workflows")
        self.assertEqual(paper.authors, "Grace Hopper")
        self.assertEqual(paper.published, "2023-5-1")
        self.assertEqual(paper.url, "https://doi.org/10.21203/rs.3.rs-123456/v1")
        self.assertNotIn("<jats:p>", paper.summary)

    def test_missing_items(self) -> None:
        self.assertEqual(rs.parse_crossref_items({"message": {}}), [])
        self.assertEqual(rs.parse_crossref_items({}), [])


class TestSsrnSearchUrl(unittest.TestCase):
    def test_builds_url_with_encoded_query(self) -> None:
        url = rs.ssrn_search_url("multi agent systems")
        self.assertTrue(url.startswith(rs.SSRN_SEARCH_URL))
        self.assertIn("term=multi+agent+systems", url)


class TestSearchDispatch(unittest.TestCase):
    def test_dispatches_only_requested_sources(self) -> None:
        with patch.object(rs, "search_arxiv", return_value=(True, [], "0 results")) as m_arxiv, patch.object(
            rs, "search_research_square", return_value=(True, [], "0 results")
        ) as m_rs:
            results = rs.search("agents", sources=["arxiv"], limit=5)
        self.assertEqual(list(results.keys()), ["arxiv"])
        m_arxiv.assert_called_once_with("agents", 5)
        m_rs.assert_not_called()

    def test_ssrn_never_hits_network(self) -> None:
        results = rs.search("agents", sources=["ssrn"])
        ok, papers, msg = results["ssrn"]
        self.assertTrue(ok)
        self.assertEqual(papers, [])
        self.assertIn("no public API", msg)

    def test_default_sources_all_three(self) -> None:
        with patch.object(rs, "search_arxiv", return_value=(True, [], "0 results")), patch.object(
            rs, "search_research_square", return_value=(True, [], "0 results")
        ):
            results = rs.search("agents")
        self.assertEqual(set(results.keys()), {"arxiv", "researchsquare", "ssrn"})


if __name__ == "__main__":
    unittest.main()
