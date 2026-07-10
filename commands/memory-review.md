# /memory-review

Curate bounded memory at loop closeout: enforce size limits, dedupe entries, detect drift, and optionally stage writes for approval.

## How To Interpret

If the user says `/memory-review`, `memory review`, or asks to curate or trim memory, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/memory-review/SKILL.md`
3. `memories/SOUL.md`
4. `memories/USER.md`
5. `memories/MEMORY.md`
6. `DOUBTS.md`
7. `DECISIONS.md`
8. `HANDOFF.md`
9. `plan/MEMORY_REVIEW.md` if it exists

## Loop

```text
ENSURE LAYOUT -> SCAN STATE -> CURATE -> WRITE MEMORY_REVIEW -> STAGE OR APPLY -> LOG SESSION
```

## Script

Review only (writes `plan/MEMORY_REVIEW.md`):

```bash
python scripts/memory_curator.py
loop memory review
```

Stage writes for approval (production-safe default):

```bash
python scripts/memory_curator.py --stage
loop memory review --stage
```

Apply directly:

```bash
python scripts/memory_curator.py --apply
loop memory review --apply
```

## When To Run

- At closeout of `/plan`, `/product-develop`, and `/loop-engine`
- When memory feels duplicated across `HANDOFF.md`, `COMPACT.md`, and `memories/MEMORY.md`
- After `/migrate-import`

## Output

Return:

1. `plan/MEMORY_REVIEW.md` path
2. Memory and user char usage vs limits
3. Drift warnings
4. Pending staged writes (if `--stage`)
5. Next action (`loop pending list` / approve / reject)
