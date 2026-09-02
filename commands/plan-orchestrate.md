# /plan-orchestrate

Orchestrate a multi-plan run where several plans or sub-products need to advance
together. Builds a plan DAG, sequences and parallelises nodes, reconciles
artifacts. Use when a single /plan-loop is not enough.

## How To Interpret

If the user says `/plan-orchestrate`, `orchestrate the plans`, `run these plans
together`, `coordinate platform-auth + user-portal + billing`, or asks to
sequence multiple plans, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/plan-orchestrate/SKILL.md`
3. `plan/PRODUCT_MAP.md` (when present)
4. `plan/products/<slug>/` (per sub-product)
5. `TASKS.yml`, `GATES.yml`
6. `DOUBTS.md`

## Loop

```text
BUILD PLAN DAG -> DETECT CROSS-SCOPE CONTRACTS -> SEQUENCE + PARALLELISE -> RECONCILE -> CLOSEOUT
```

## Output (per batch)

- The DAG (as-built)
- The order in which nodes actually ran
- The cross-scope contracts created
- The open doubts blocking the next round
- The next plan id to run (or "release-ready")

`plan/ORCHESTRATION_LOG.md` accumulates the per-batch reports.

## Continuation

A failed node blocks its dependents but not its non-dependents. The DAG localises
failure. The chain reports the failure to the user with a Stop Condition; the
user decides whether to re-design the node or skip it.