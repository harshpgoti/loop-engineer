---
name: memory-review
description: Curates bounded memory at loop closeout with size limits, dedupe, drift detection, and optional write-approval staging. Use when the user types /memory-review or at plan/develop/loop closeout.
---

# Memory Review

## Purpose

Keep `memories/MEMORY.md` and `memories/USER.md` within bounded char limits, deduplicated, and aligned with product-state files.

## Command

`/memory-review`

## Read First

1. `memories/SOUL.md`
2. `memories/USER.md`
3. `memories/MEMORY.md`
4. `DECISIONS.md`
5. `HANDOFF.md`
6. `DOUBTS.md`

## Limits

- `memories/MEMORY.md`: ~2,200 chars
- `memories/USER.md`: ~1,375 chars
- Entries separated by `§`

## Script

```bash
python scripts/memory_curator.py --stage
loop memory review --stage
```

## Closeout Rules

1. Product facts belong in `plan/main_plan.md` and step plans — not duplicated in memory diary entries.
2. User preferences belong in `memories/USER.md`.
3. Session progress diary belongs in `memories/MEMORY.md`.
4. Default to `--stage` for production workspaces; use `--apply` only when the user approves direct writes.
5. Log the review in `state.db` via the script.

## Output

- `plan/MEMORY_REVIEW.md`
- Usage vs limits
- Drift warnings
- Pending writes under `.loop/pending/` when staged
