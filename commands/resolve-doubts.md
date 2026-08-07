# /resolve-doubts

Interactively clear every open doubt and blocker across the plan, then give a
go/no-go for development. Plan-wide (not one feature spec), write-enabled (records
decisions), and interactive (drives to green).

## How To Interpret

If the user says `/resolve-doubts` (or "resolve doubts", "clear blockers", "are we
ready to build", "sort out open questions before development"), execute this file
and `skills/plan-loop/phases/resolve-doubts.md`.

Runs two ways:
- **Inside `/plan-loop`** as the final pre-development readiness sweep (the harness
  emits `PHASE: resolve-doubts` when planning is otherwise complete but `DOUBTS.md`
  still has open items).
- **Standalone**, anytime open doubts accumulate - same as `/spec-clarify` or
  `/ask-loop`.

## Required Reads

`DOUBTS.md`, `DECISIONS.md`, `EVIDENCE_LOG.md`, `GATES.yml`, `TASKS.yml`,
`plan/main_plan.md`, active feature `spec.md` / `clarifications.md`,
`plan/PROD-GAP.md` when present. See `skills/plan-loop/phases/resolve-doubts.md`.

## Wired From

- `/plan-loop` - terminal readiness phase before `/product-develop`.
- `/status`, `/ask-loop`, `/revise-plan` - point here when open doubts or blocked
  pre-development gates are detected.

## Loop

```text
GATHER OPEN ITEMS (DOUBTS.md + spec questions + blocked gates + weak evidence)
-> CLASSIFY blocking vs deferrable -> WALK blocking items with the user
-> RECORD resolutions (DOUBTS.md/DECISIONS.md/spec/EVIDENCE) -> RE-CHECK gates
-> GO / NO-GO
```

## Continuation

Terminus: **tasks compiled + go/no-go for build.** On **GO**, continue into
`task-compiler` if tasks aren't compiled yet (and, under `/loop-engine`, into
`/product-develop` when build gates pass). On **NO-GO**, stopping is correct -
that is a Stop Condition. See `docs/CONTINUATION.md`.

## Stop Conditions

- Blocking doubts remain that need user answers - report each question, not a
  command to run.
- A doubt is a strategic pivot - route to `skills/plan-loop/phases/council.md`.
- Sensitive/regulated data before `G-SENSITIVE-DATA` passes.

## Output

1. Resolved this session (and where recorded)
2. Gates moved to pass
3. Remaining blockers (if any)
4. Verdict: GO (clear to run `/product-develop`) or NO-GO (blockers remain)
5. Next command
