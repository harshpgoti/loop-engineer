# /comment-analyzer

Verify comment accuracy and staleness. Classifies each comment as Inaccurate
(does not match code), Stale (was true, no longer), Incomplete (true but
partial), or Low-value (true but trivial). Read-only. Use in code review or
as a periodic documentation-quality signal.

## How To Interpret

If the user says `/comment-analyzer`, `check the comments`, `are the comments
accurate`, or asks to audit documentation quality, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/comment-analyzer/SKILL.md`
3. the active workspace's source tree

## Loop

```text
WALK the source files -> CLASSIFY each comment into 4 buckets -> EMIT a Markdown report
```

## Output

A Markdown report with the four-bucket classification and a per-comment
list with file, line, comment snippet, bucket, and suggestion.

## Continuation

The chain produces a report; the maintainer acts on the Inaccurate, Stale,
and Incomplete findings. The Low-value findings are suggestions, not
findings.