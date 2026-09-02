"""Tests for research_search.py parsing/dispatch logic (no live network calls).

Run: python scripts/test_research_search.py
"""

from __future__ import annotations

import json
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

SAMPLE_PUBMED_ESUMMARY = {
    "result": {
        "uids": ["42676745"],
        "42676745": {
            "uid": "42676745",
            "pubdate": "2026",
            "title": "Benchmarking publicly accessible LLMs for patient-facing acute pain guidance",
            "fulljournalname": "Frontiers in public health",
            "authors": [{"name": "Jiang B"}, {"name": "Sun H"}, {"name": "Chen L"}],
        },
    }
}

SAMPLE_PUBMED_ESEARCH = {"esearchresult": {"idlist": ["42676745", "42673790"]}}


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

    def test_rejects_entity_declarations(self) -> None:
        malicious = b'<!DOCTYPE feed [<!ENTITY x "expanded">]><feed>&x;</feed>'
        with self.assertRaisesRegex(rs.ET.ParseError, "DTD and entity"):
            rs.parse_arxiv_atom(malicious)


class TestHttpBoundary(unittest.TestCase):
    def test_rejects_non_http_and_unapproved_hosts_before_opening(self) -> None:
        with patch.object(rs.urllib.request, "urlopen") as opener:
            with self.assertRaisesRegex(ValueError, "not allowed"):
                rs._http_get("file:///etc/passwd")
            with self.assertRaisesRegex(ValueError, "not allowed"):
                rs._http_get("https://example.test/papers")
        opener.assert_not_called()


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


class TestParsePubmedSummary(unittest.TestCase):
    def test_parses_pubmed_item(self) -> None:
        papers = rs.parse_pubmed_summary(SAMPLE_PUBMED_ESUMMARY)
        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper.source, "pubmed")
        self.assertEqual(paper.title, "Benchmarking publicly accessible LLMs for patient-facing acute pain guidance")
        self.assertEqual(paper.authors, "Jiang B, Sun H, Chen L")
        self.assertEqual(paper.published, "2026")
        self.assertEqual(paper.url, "https://pubmed.ncbi.nlm.nih.gov/42676745/")
        self.assertIn("Frontiers in public health", paper.summary)

    def test_missing_uids(self) -> None:
        self.assertEqual(rs.parse_pubmed_summary({"result": {}}), [])
        self.assertEqual(rs.parse_pubmed_summary({}), [])

    def test_skips_author_entries_without_names(self) -> None:
        payload = {
            "result": {
                "uids": ["1"],
                "1": {"uid": "1", "title": "T", "authors": [{"name": ""}, {"name": "A B"}]},
            }
        }
        papers = rs.parse_pubmed_summary(payload)
        self.assertEqual(papers[0].authors, "A B")


class TestPubmedSearch(unittest.TestCase):
    def test_search_pubmed_two_step_fetch_and_parse(self) -> None:
        bodies = [
            json.dumps(SAMPLE_PUBMED_ESEARCH).encode("utf-8"),
            json.dumps(SAMPLE_PUBMED_ESUMMARY).encode("utf-8"),
        ]

        def fake_get(url: str, timeout: int = 20) -> bytes:
            self.assertIn("eutils.ncbi.nlm.nih.gov", url)
            return bodies.pop(0)

        with patch.object(rs, "_http_get", side_effect=fake_get):
            ok, papers, msg = rs.search_pubmed("acute pain LLM", limit=10)
        self.assertTrue(ok)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0].source, "pubmed")
        self.assertEqual(msg, "1 results")

    def test_search_pubmed_empty_idlist_short_circuits(self) -> None:
        with patch.object(
            rs, "_http_get", return_value=json.dumps({"esearchresult": {"idlist": []}}).encode("utf-8")
        ) as m:
            ok, papers, msg = rs.search_pubmed("nothing here")
        self.assertTrue(ok)
        self.assertEqual(papers, [])
        self.assertEqual(msg, "0 results")
        self.assertEqual(m.call_count, 1)

    def test_search_pubmed_reports_esearch_failure(self) -> None:
        with patch.object(
            rs, "_http_get", side_effect=rs.urllib.error.URLError("down")
        ):
            ok, papers, msg = rs.search_pubmed("acute pain")
        self.assertFalse(ok)
        self.assertEqual(papers, [])
        self.assertIn("down", msg)


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

    def test_default_sources_all_four(self) -> None:
        with patch.object(rs, "search_arxiv", return_value=(True, [], "0 results")), patch.object(
            rs, "search_research_square", return_value=(True, [], "0 results")
        ), patch.object(rs, "search_pubmed", return_value=(True, [], "0 results")):
            results = rs.search("agents")
        self.assertEqual(set(results.keys()), {"arxiv", "researchsquare", "pubmed", "ssrn"})

    def test_pubmed_dispatches_only_when_requested(self) -> None:
        with patch.object(rs, "search_pubmed", return_value=(True, [], "0 results")) as m_pubmed:
            results = rs.search("agents", sources=["pubmed"], limit=3)
        self.assertEqual(list(results.keys()), ["pubmed"])
        m_pubmed.assert_called_once_with("agents", 3)


if __name__ == "__main__":
    unittest.main()
