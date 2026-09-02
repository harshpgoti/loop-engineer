---
name: iterative-retrieval
description: Run a multi-round retrieval loop that progressively refines a query against a corpus (RAG over a project knowledge base, a vendor API doc set, or the active workspace's docs/). Use when a single-shot retrieval returns low-quality results, when the question is multi-faceted, or when the answer requires stitching across multiple documents.
---

# Iterative Retrieval

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for multi-round retrieval against a
corpus. A single-shot retrieve-and-answer leaves recall on the table
when the question is multi-faceted or the corpus is large. This skill
runs **multiple rounds** of retrieval, each round informed by the
prior round's results.

## When to use

- A question is multi-faceted: "what's the role of X in the
  architecture, and how does it interact with Y?"
- A single retrieve-and-answer returns only one or two relevant
  documents; the answer needs more.
- The corpus is large (>100 documents) and the first query is
  under-specified; the chain narrows the query through rounds.
- The user wants evidence-cited answers and the evidence is spread
  across documents.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A single-fact question | a direct lookup |
| A corpus with <20 documents | one round is enough |
| A real-time system that can't afford multi-round latency | a faster, single-shot approach |

## The Three-Round Loop

The skill is a three-round loop. The chain can stop early if a round
returns high-confidence results.

### Round 1: Seed the corpus

The chain formulates the question and runs one retrieval pass. The
output is a list of candidate documents, ranked by relevance score.

The chain **does not** answer from this list. The chain **does**
extract candidate terms from the top results: entities, file names,
section headings, technical terms. These terms are the seed for
round 2.

### Round 2: Expand the query

The chain takes the candidate terms from round 1 and builds a broader
query. The query expansion is rule-based:

- Add the candidate terms as OR clauses.
- Add any cross-references the candidate documents mention
  (e.g. "see also: <other>").
- Remove terms that are obviously noise (e.g. "the", "and", common
  stop words).

The chain runs a second retrieval pass. The output is a richer list
of candidate documents, some of which were missed in round 1.

### Round 3: Synthesise the answer

The chain takes the candidate documents from rounds 1 + 2, deduplicates
them, and synthesises the answer. The synthesis must:

- Cite the source document + section for every claim.
- Disagree with itself when the documents disagree.
- Flag low-confidence claims explicitly.

If the answer is still incomplete after round 3, the chain returns
the best available answer with a "low confidence" flag. The chain
**does not** loop indefinitely.

## Workflow

### 1. State the question

In one sentence: what is the user asking? The chain refuses vague
questions ("tell me about the project") and asks one clarifying
question.

### 2. Run the three rounds

```bash
python scripts/iterative_retrieval.py --workspace <ws> --query "<the question>" --corpus <dir> --out plan/RETRIEVAL.json
```

The script runs the three rounds and emits a JSON snapshot:

```json
{
  "version": 1,
  "query": "<the question>",
  "rounds": [
    {"round": 1, "query_used": "<expanded query 1>", "candidates": [...], "terms": [...]},
    {"round": 2, "query_used": "<expanded query 2>", "candidates": [...], "terms": [...]},
    {"round": 3, "synthesis": "<the answer>", "citations": [...]}
  ],
  "confidence": "high" | "medium" | "low"
}
```

### 3. Surface the answer

The answer is in `plan/RETRIEVAL.json` with citations. The chain
presents the answer to the user; the user may accept or push back.
A push-back triggers another round (the question is refined based
on the user's correction).

## Anti-Patterns

- **A loop that runs forever.** The skill is bounded at 3 rounds.
  Low confidence after 3 rounds is a Stop Condition; the chain
  surfaces the partial answer.
- **A loop that ignores the user's question.** The loop refines the
  query based on the corpus, not based on the user's intent. The
  question is fixed.
- **A loop that doesn't cite.** A multi-round answer without
  citations is a hallucination. Cite or do not answer.
- **A loop that uses LLM-as-judge for relevance.** The skill is
  deterministic; relevance is a heuristic (term overlap, position,
  length). The LLM is the final synthesis step, not the retrieval
  step.

## Related Skills

- `research-search` - the literature search; this skill is the
  in-workspace equivalent.
- `ask-loop` - the question-answering skill; the output of
  `iterative-retrieval` feeds into `ask-loop`'s synthesis.
- `safeguard` - the prompt-level defence; the synthesis step
  applies the E7 baseline to untrusted corpus content.