---
name: product-tree
description: Shows the sub-product scopes in one product workspace, their plan/build state, dependency order, and unsatisfied contracts. Use for /product-tree or questions about how sub-products fit together.
---

# Product Tree

Inherits `docs/SKILL_CONTRACT.md`.

## Purpose

Show the platform and every sub-product from the unified workspace. A sub-product's plan
lives under `plan/products/<slug>/`; only its code may live in another directory or repo.
There is no parent/child plan synchronization or second `.loop-engineer/` workspace.

## Read First

1. `commands/product-tree.md`
2. `plan/SESSION_MANIFEST.md`
3. `plan/PRODUCT_MAP.md`
4. `plan/products/*/scope.json`
5. `plan/contracts/*`
6. Root and scope-local `TASKS.yml`, `GATES.yml`, and `DOUBTS.md`

## Run

Use `loop scope list` for dependency order and scope state, then `loop scope check` for
contract integrity. Use `loop scope show <slug>` when one scope needs detail. The shell
commands are internal runtime operations; run them for the user.

## What to report

- platform root;
- each scope's map id, plan folder, code folder, status, and immediate task/gate;
- dependency order and any cycles;
- contracts provided and consumed;
- contract findings: unprovided, unimplemented, breaking, or consumer-unnotified;
- the next actionable scope or shared-platform task.

## Rules

- Resolve scope before any write.
- Never infer a missing scope selection as shared-platform work.
- Cross-scope interfaces live in `plan/contracts/`; do not infer them from prose.
- A scope's deep product pack is its folder. Its internal steps and features live under
  that folder's `steps/` and `features/`.
- `loop scope absorb` is the one-way migration path for a legacy sub-product that still
  has its own `.loop-engineer/`; it is not a second supported steady-state layout.

## Closeout

Report the scope table, dependency order, contract findings, and one next action.
