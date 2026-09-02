---
name: plan-orchestrate
description: Orchestrate a multi-plan run where several plans (or several sub-products) need to advance together, with explicit handoffs, ordering, and reconciliation. Use when a single /plan-loop is not enough - the work spans multiple plans, multiple features, or multiple sub-products with dependencies.
---

# Plan Orchestrate

Inherits `docs/SKILL_CONTRACT.md`.

A coordinator for runs that touch more than one plan. The skill does not replace
`/plan-loop` or `/feature-workflow`; it sequences them and reconciles the
artifacts they produce.

## When to use

- Two or more plans or features must advance together with explicit dependencies
  between them.
- A sub-product change requires a contract update in another sub-product
  (cross-scope coordination).
- A platform-scale product needs per-step orchestration across many
  `plan/step_NN_*.md` files with the ultraplan pack running through them.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A single plan with one feature | `/plan-loop` |
| A single feature spec to clarify | `/spec-clarify` |
| A sub-product switch with contract drift | `/scope` + `loop scope check` |
| A run that does not touch multiple plans | the per-plan commands directly |

## The Plan DAG

The skill's input is a **plan DAG**: nodes are plans/features, edges are
dependencies. The DAG is the source of truth; the orchestration runs the
DAG.

```yaml
nodes:
  - id: platform-auth
    plan: plan/step_03_platform_auth.md
    depends_on: []
  - id: user-portal
    plan: plan/step_07_user_portal.md
    depends_on: [platform-auth]
  - id: billing-portal
    plan: plan/step_09_billing_portal.md
    depends_on: [platform-auth]
  - id: launch
    plan: plan/step_99_launch.md
    depends_on: [user-portal, billing-portal]
```

Each node declares the plan it covers and the node ids it depends on. The
DAG is computed into a topological order; the orchestration runs nodes in
that order, parallelising where the DAG allows.

## Workflow

### 1. Build the plan DAG

Read `plan/PRODUCT_MAP.md` (if present) and `plan/products/<slug>/` to discover
the plans. Build the DAG with explicit `depends_on` per node. If a dependency
is implicit in the prose, surface a doubt in `DOUBTS.md` rather than guess.

### 2. Detect cross-scope contracts

For each edge, check whether the source produces a contract the consumer reads.
Run `loop scope check` per edge. A missing contract is a planning question,
not a build-time surprise.

### 3. Sequence and parallelise

Topological sort. A node with no unresolved dependencies is runnable. Multiple
runnable nodes are run in parallel as a single batch (per the LE chain's
parallel-execution model). A node that depends on a failed earlier node is
held; the chain reports the failure to the user.

### 4. Reconcile

After each batch, reconcile:

- `plan/main_plan.md` and per-plan files: any cross-cutting change is mirrored.
- `TASKS.yml`: cross-node tasks are linked with the DAG id.
- `GATES.yml`: a node's release gates are blocked until the dependencies pass.
- `HANDOFF.md`: the next batch's plan is set, plus what is in flight.

### 5. Closeout

When the DAG is drained, write `plan/ORCHESTRATION_LOG.md` with:

- the DAG (as-built);
- the order in which nodes actually ran;
- the cross-scope contracts that were created;
- the open doubts that block the next round;
- the next plan id to run (or "no further plans; release-ready").

## Output

- `plan/ORCHESTRATION_LOG.md` (created on closeout, appended each batch).
- A batch report per node: which plan, which features, which gates, which
  tasks closed.

## Anti-Patterns

- **Implicit dependencies.** "Platform-auth must come first" is fine in prose
  once, but the DAG must record it. An edge in the DAG is an edge the chain
  respects.
- **Sequential when parallel is possible.** If two nodes have no edge between
  them, they can run in the same batch. Sequential is the default only when
  the DAG requires it.
- **One giant orchestrator.** The orchestrator sequences; the per-plan
  commands do the work. Do not put plan content in this skill.
- **Skipping the contract check.** An edge in the DAG without a contract is a
  hidden contract. The chain will discover the missing contract at runtime;
  the discovery is a Stop Condition, not a bug.
- **Holding the chain on a single failure.** A failed node blocks its
  dependents but not its non-dependents. The DAG localises the failure.

## Related Skills

- `plan-loop` - per-plan work.
- `feature-workflow` - per-feature work.
- `scope` - sub-product switching and contract checks.
- `ultraplan-loop` - the platform-scale variant.
- `dev-team` - role-based review across the orchestration.