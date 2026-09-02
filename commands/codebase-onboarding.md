# /codebase-onboarding

4-phase onboarding for a fresh project: Reconnaissance -> Architecture mapping ->
Convention detection -> Generate onboarding guide + enhance (not replace) an
existing CLAUDE.md. Use when adopting Loop Engineer on a project that has not been
onboarded yet, or when the repo has changed enough that the prior onboarding is stale.

## How To Interpret

If the user says `/codebase-onboarding`, `onboard this repo`, `bootstrap the loop`,
or asks to bootstrap Loop Engineer on a fresh or significantly changed project, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/codebase-onboarding/SKILL.md`
3. `commands/setup-loop-engine.md` (the chain trigger that follows)
4. `plan/main_plan.md` (when present)
5. existing `CLAUDE.md` in the repo, if any

## Loop

```text
DETECT existing CLAUDE.md -> Phase 1 (parallel recon) -> Phase 2 (architecture) -> Phase 3 (convention detection with citation) -> Phase 4 (write ONBOARDING.md + CLAUDE.md patch under .loop/pending/)
```

## Output

1. `docs/ONBOARDING.md` (always)
2. `.loop/pending/CLAUDE_PATCH.md` (the suggested `CLAUDE.md` additions; never auto-applied)
3. Phase 1-3 summaries as evidence

## Continuation

The chain continues to `setup-loop-engine` for the LE workspace registration. The
`CLAUDE.md` patch is review-only; the user decides whether to apply it.