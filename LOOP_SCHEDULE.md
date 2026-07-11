# Loop schedule - mixed runtime handoffs

## Fixed loops (Cursor)

```text
/loop 2h /plan-loop - Step 1 task from HANDOFF.md
/loop 1h /product-develop - Step 2 task from HANDOFF.md (after G-ARCH-01)
/loop 30m Check GitHub Actions + update HANDOFF if red
/loop 4h /compact-loop - refresh COMPACT.md during long sessions
```

## Dynamic self-pace

Agent picks delay based on work:

| Situation | Next wake |
|-----------|-----------|
| Waiting on CI | 10-15 min |
| Long test suite | After CI completes (watch workflow) |
| Customer outreach | 24h - check for replies |
| Research sprint | End of session only |
| Overnight build | 2h heartbeat + git diff watcher |
| Tool switch / context pressure | run `/compact-loop` first |

## Tool switch protocol

1. Commit or stash WIP.
2. Update `HANDOFF.md` with exact file paths and next command.
3. In the new tool, type `/plan-loop`, `/product-develop`, or `/loop-engine`.
4. The adapter should read `AGENTS.md`, `skills/`, memory files, and `HANDOFF.md` automatically.

## Optional sandboxed runs

For long isolated build loops, use your team's approved sandbox or CI runner. Apply network egress policy for external services only after approval.

## Optional overnight consolidation

Schedule a job to refresh `COMPACT.md`, run `/memory-review --stage`, and reconcile `DOUBTS.md` against `DECISIONS.md` - only if your workflow needs it.
