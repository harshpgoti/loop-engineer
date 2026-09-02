# /iterative-retrieval

Run a three-round retrieval loop against a corpus. Each round refines the
query based on the prior round's results. Use for multi-faceted questions
where a single-shot retrieve-and-answer returns low-quality results.

## How To Interpret

If the user says `/iterative-retrieval`, `multi-round retrieval`, `stitch
docs`, `find X across docs`, or asks for a multi-document answer, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/iterative-retrieval/SKILL.md`
3. `scripts/iterative_retrieval.py`
4. the corpus (a directory of documents)

## Loop

```text
STATE the question -> ROUND 1 (seed retrieval) -> ROUND 2 (expand query) -> ROUND 3 (synthesise) -> EMIT plan/RETRIEVAL.json
```

## Script

```bash
python scripts/iterative_retrieval.py --workspace <ws> --query "<the question>" --corpus <dir> --out plan/RETRIEVAL.json
```

## Output

A single JSON file with the three rounds, the candidate documents, the
extracted terms, the synthesis, and the citations. The chain surfaces
the synthesis to the user; the user may accept or push back.

## Continuation

`/ask-loop` consumes the synthesis; the user's push-back triggers
another round with a refined question. The skill is bounded at 3 rounds
per call; low confidence after 3 rounds is a Stop Condition.