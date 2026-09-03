# /plan-reconcile

Reconcile a planning reform across every file its context upgrades.

## How To Interpret

If the user says `/plan-reconcile`, `reconcile the plan`, or a `/plan-loop` reform /
`/revise-plan` edit changed what other plan files still claim, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `plan/RETIRED.md` if it exists
3. `plan/RECONCILE_REPORT.md` if it exists

## Loop

```text
FANOUT (what does this reform touch?) -> EDIT EVERY FILE IT TOUCHES -> CHECK (drift clean?) -> RETIRE (dead items to the ledger)
```

## Scripts

Files a reform of one decision can affect (analysis only, no writes):

```bash
loop plan-reconcile fanout --decision D-M-063 --scope identity-and-access-platform
```

Deterministic drift across the plan surface (exit 1 while a blocker remains):

```bash
loop plan-reconcile check
loop plan-reconcile check --write   # also write plan/RECONCILE_REPORT.md
```

Record a dead planning item so it stops haunting live files (nothing is deleted):

```bash
loop plan-reconcile retire --id D-M-022 --by D-M-057 --reason "service, not library"
```

## What check enforces

- **Blockers:** a superseded or retired id cited as live; the same task/gate id with a
  different status in root vs scope files; a `PRODUCT_MAP.md` row claiming
  built/complete while `ULTRAPLAN_STATUS.md` lists missing artifacts for that step.
- **Needs review:** deployment decisions newer than `DEPLOYMENT_PLAN.md` (reconcile by
  hand - never blind-regenerate; the file carries its own warning); unsatisfied
  cross-scope blocks with no `plan/contracts/` record.

Append-only records (`CURRENT_STATE.md`, `HANDOFF.md`, `EVIDENCE_LOG.md`) are never
flagged: they narrate what past sessions believed. Validity of evidence itself is
owned by `loop evidence` and the reference graph.

## When To Run

- Inside `/plan-loop` after council/ultraplan edits, before task-compiler closes.
- Inside `/revise-plan` for every routed edit (fanout first, check after).
- Standalone after any reform that spans steps, scopes, or deployment.

## Output

1. `plan/RECONCILE_REPORT.md` path (with `--write`)
2. Blocker count (0 to proceed) + review items
3. Remaining live citations after a `retire`
4. Next command (`/develop-product` when blockers are 0)
