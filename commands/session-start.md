# /session-start

Always-on memory bootstrap - run **before** any loop work in any tool.

## Agent (mandatory)

```bash
loop session-start --command "<active-command>" --tool "<tool-name>"
```

This automatically syncs both ends of the product hierarchy. Then read
**`plan/SESSION_MANIFEST.md`** and every file listed there. In a sub-product,
The `## Scope` block names which sub-product this session is about; it is read during the
active command, not a manual follow-up.

## Tool names

Use `--tool` hint when known: `cursor`, `claude`, `codex`, `opencode`, `grok`, `api`, `other`.

## Required reads

1. `skills/session-lifecycle/SKILL.md`
2. `plan/SESSION_MANIFEST.md` (after script runs)

## Wired into

`/plan-loop`, `/develop-product`, `/loop-engine`, and ad-hoc product work - always run this first.

## Continuation

**Bootstrap, then run the command that triggered it.** `session-start` is a bookend,
never the whole turn: after the manifest is written, execute the active command and
carry it to its terminus. See `docs/CONTINUATION.md`.
