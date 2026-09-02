---
name: learn-curator
description: Promote eligible observations to the recursive-decision ledger or to skill/command proposals. Implements the v2 promotion gate (3+ distinct sessions, 0.8 average confidence) and writes a staged record under .loop/pending/. Use at /session-end when learning candidates exist; complements the existing continuous-learning-v2 documentation skill.
---

# Learn Curator

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic skill that promotes eligible observations from
`.loop/learning/observations.jsonl` to staged records. The
`continuous-learning-v2` skill documents the v2 model; this skill is the
runtime that does the work.

## When to use

- At `/session-end` when `.loop/learning/observations.jsonl` has new
  entries that may be eligible.
- After a session with several corrections from the user, when
  pattern-matching the corrections against past observations would
  produce a candidate.
- When a doubt has been resolved two or more times the same way
  and the user wants to lock that resolution as an instinct.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| Recording a one-off observation | `learn` (the user's intent for the v2 model) |
| Reviewing the memory budget | `/memory-review` |
| Archiving the session | `/session-end` |

## Promotion Gate

A candidate observation is eligible when **all** are true:

- Same fingerprint in **3+ distinct sessions** (the promotion count).
- Average confidence across sessions **≥ 0.8** (the promotion threshold).
- The pattern + evidence contain no sensitive data (regex pre-check).
- The pattern is not a per-product fact; the candidate is a general
  pattern, not a per-build configuration.

A candidate that fails the gate stays in `observations.jsonl` and is
re-evaluated on the next curator run.

## Workflow

### 1. Read the observations

```bash
python -c "import sys; sys.path.insert(0, 'scripts'); from learning_candidates import candidates, observations; print(len(observations(repo_root)), 'observations')"
```

(Or the equivalent in the active workspace.)

### 2. Compute candidates

The candidates function returns a sorted list of `(fingerprint, sessions, confidence)`
tuples. Sort by session count descending, then confidence descending.

### 3. Apply the promotion gate

For each candidate, check the three pre-conditions. The first candidate
that passes is the next one to surface to the user. Surface one at a
time; do not batch.

### 4. Surface the candidate to the user

A Stop Condition with multiple-choice options:

```text
LEARN_CANDIDATE eligible: <pattern>

| Promotion gate | Value |
|---|---|
| Sessions | <count> |
| Average confidence | <0..1> |
| Sensitive data | clean |
| General pattern | yes |

What should we do?

1. **Stage a promotion record under .loop/pending/** _(recommended)_
2. Promote directly to memories/MEMORY.md
3. Defer for the next 30 days
4. Reject — observation should stay an observation
```

### 5. Stage the promotion

The staged record is the durable artefact. It is the input to the next
session's `memory-review`:

```yaml
# .loop/pending/learning-<fingerprint>.json
{
  "version": 1,
  "fingerprint": "<the candidate's fingerprint>",
  "pattern": "<the candidate's pattern text>",
  "evidence": "<one verbatim example>",
  "distinct_sessions": <int>,
  "average_confidence": <0..1>,
  "sensitivity_check": "clean",
  "approved_by": "<user identity>",
  "status": "pending-review",
  "curated_at": "<ISO 8601 timestamp>"
}
```

The next `memory-review` reads pending records, applies the
`ContinuousLearning-v2` promotion rules, and either commits to
`memories/MEMORY.md` (project-scope) or rejects with a reason.

## Output

- One promotion record per session (or zero, when no candidate is eligible).
- A short report: `# Learn Curator Digest` with the candidate's pattern,
  sessions, confidence, and sensitivity status.
- The staged record at `.loop/pending/learning-<fingerprint>.json`.

## Sensitive Data

The regex pre-check rejects any candidate whose pattern + evidence
contains:

- `api_key`, `password`, `secret`, `bearer`, `token[:=]`
- Anything matching `SECRET_PATTERN` (see `learning_candidates.py`)

A candidate that fails the pre-check stays in `observations.jsonl` and
is not surfaced. The chain does not surface sensitive data even for
internal review.

## Anti-Patterns

- **A curator that auto-promotes.** Promotion is a user decision; the
  curator surfaces the candidate; the user decides. Auto-promotion
  is the failure the v2 model exists to prevent.
- **A curator that surfaces everything.** A curator that surfaces
  every observation is a curator that surfaces nothing useful.
  The gate is the discipline.
- **A curator that doesn't re-evaluate the gate.** The gate's
  threshold is configurable; a session that lowers the threshold
  for a specific category is a config change, not a one-off
  exception. Record the new threshold in the staged record.
- **A curator that promotes per-product facts.** Per-product facts
  are configuration, not instincts. A per-product fact that
  recurs 3+ times is a config bug, not a learning.

## Related Skills

- `continuous-learning-v2` - the v2 model documentation; this skill
  is the runtime.
- `memory-review` - the consumer of the staged records; runs the
  actual promotion to `memories/MEMORY.md`.
- `recursive-decision-ledger` - the analogous skill for architecture
  decisions; this skill is for behavioural patterns.
- `/session-end` - the typical entry point; the curator runs as
  part of session-end closeout.