#!/usr/bin/env python3
"""Three-round iterative retrieval against a corpus.

Each round builds on the prior round's results. The script is
deterministic (term-overlap relevance, no LLM). The output is a JSON
file with the three rounds, the candidate documents, the extracted
terms, the synthesis (placeholder for the agent), and the citations.

Usage:
    python scripts/iterative_retrieval.py \
        --workspace <ws> \
        --query "<the question>" \
        --corpus <corpus-dir> \
        --out plan/RETRIEVAL.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

STOP_WORDS = {
    "the", "and", "or", "of", "to", "a", "an", "in", "on", "for", "with",
    "is", "are", "be", "this", "that", "by", "from", "as", "at", "it",
    "its", "into", "if", "but", "not", "no", "yes", "we", "you", "they",
}


def _tokenize(text: str) -> list[str]:
    return [
        w.lower()
        for w in re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b", text)
        if w.lower() not in STOP_WORDS
    ]


def _score(query_tokens: set[str], doc_tokens: Counter) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    overlap = sum((query_tokens & set(doc_tokens.keys())).__len__() for _ in [None])
    # Simpler: sum of term frequencies for query terms present.
    return float(sum(doc_tokens[t] for t in query_tokens if t in doc_tokens))


def _read_corpus(corpus: Path) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    if not corpus.exists():
        return docs
    for p in sorted(corpus.rglob("*.md")):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        docs.append({
            "path": str(p.relative_to(corpus)),
            "tokens": Counter(_tokenize(text)),
            "first_line": text.strip().splitlines()[0] if text.strip() else "",
        })
    return docs


def _round(corpus: list[dict[str, Any]], query: str, top_k: int = 5) -> dict[str, Any]:
    qt = set(_tokenize(query))
    scored = sorted(
        ((_score(qt, d["tokens"]), d) for d in corpus),
        key=lambda kv: -kv[0],
    )[:top_k]
    candidates = [
        {"path": d["path"], "score": s, "first_line": d["first_line"]}
        for s, d in scored if s > 0
    ]
    new_terms = set()
    for c in candidates:
        new_terms.update(_tokenize(c["first_line"]))
    return {
        "query_used": query,
        "candidates": candidates,
        "terms": sorted(new_terms - qt)[:20],
    }


def _synthesize(candidates: list[dict[str, Any]], query: str) -> dict[str, Any]:
    citations = [
        {"path": c["path"], "score": c["score"]} for c in candidates
    ]
    return {
        "synthesis": (
            f"Based on {len(candidates)} candidates, the answer to "
            f"{query!r} is summarised in the cited documents. The chain "
            f"should synthesise a full answer with citation-by-citation."
        ),
        "citations": citations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--corpus", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    corpus = _read_corpus(args.corpus.resolve())
    if not corpus:
        print(f"No documents found in corpus: {args.corpus}", file=__import__("sys").stderr)
        return 1

    rounds: list[dict[str, Any]] = []
    r1 = _round(corpus, args.query)
    rounds.append({**r1, "round": 1})
    if r1["terms"]:
        r2_query = args.query + " " + " ".join(r1["terms"][:5])
        r2 = _round(corpus, r2_query)
        rounds.append({**r2, "round": 2})
    else:
        r2 = r1
    r3 = _round(corpus, r2.get("query_used", args.query))
    rounds.append({**r3, "round": 3})

    all_candidates = []
    seen: set[str] = set()
    for r in rounds:
        for c in r["candidates"]:
            if c["path"] not in seen:
                seen.add(c["path"])
                all_candidates.append(c)

    synthesis = _synthesize(all_candidates, args.query)
    confidence = "high" if len(all_candidates) >= 5 else "medium" if all_candidates else "low"

    report = {
        "version": 1,
        "query": args.query,
        "corpus": str(args.corpus),
        "timestamp": int(time.time()),
        "rounds": rounds,
        "synthesis": synthesis["synthesis"],
        "citations": synthesis["citations"],
        "confidence": confidence,
    }
    output = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())