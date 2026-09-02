---
name: parallel-execution-optimizer
description: Decide whether a multi-step task in the chain should run sequentially or in parallel, and how to parallelise safely. Use when planning a chain run that has more than 2-3 independent steps, or when the runtime is bottlenecked by serial tool calls.
---

# Parallel Execution Optimizer

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for deciding the run mode of a
multi-step task. The chain's default is sequential; this skill
identifies when parallel is safe, when it is not, and how to
parallelise without race conditions.

## When to use

- A chain run has more than 2-3 independent steps.
- The runtime is bottlenecked by serial tool calls (each tool waits
  for the previous).
- Multiple sub-tasks can be parallelised, but the user is unsure
  whether the chain's handoff discipline supports it.
- The user asks "can this run in parallel?" or "what's the fastest
  way to do X."

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A single tool call | run it |
| A chain run with dependencies between every step | run sequentially |
| A real production workload with strict latency SLAs | the harness's parallel runtime, not this skill |

## The Decision Rule

The chain's parallelism is **safe** when:

1. **Independent inputs** — the parallel steps do not read or write
   the same file or state.
2. **No shared workspace mutation** — the steps do not both run
   `git add` or `git commit` against the same workspace.
3. **No shared harness state** — the steps do not both invoke
   the same tool with conflicting arguments.
4. **Deterministic merge** — the post-step synthesis can combine
   the results without ambiguity.

When all four hold, the chain runs the steps in parallel. When
any one fails, the chain runs sequentially and surfaces the
dependency in `HANDOFF.md`.

## Workflow

### 1. Identify the steps

The chain parses the active task into a list of steps. Each step
is a tool call, a script invocation, or a sub-command.

### 2. Build the dependency graph

For each pair of steps, the chain checks:

- Does step B read a file that step A writes?
- Does step B invoke a tool that step A holds in a particular
  state?
- Does step B depend on the output of step A?

If yes to any, the edge is added to the graph.

### 3. Find the independent sets

The chain computes the topological order and groups steps that have
no edges between them. Each group is a parallel batch.

### 4. Run the batches

The chain runs each batch in parallel, then the next batch after
the previous one completes. The result is a serial-of-parallel
execution: as fast as possible given the dependencies.

## Output

A single plan emitted at `<workspace>/plan/PARALLEL_PLAN.md`:

```markdown
# Parallel Plan

## Steps
1. <step 1>
2. <step 2>
3. <step 3>
4. <step 4>

## Dependency graph
- 1 -> 3
- 2 -> 4

## Batches
- Batch 1: [1, 2]
- Batch 2: [3, 4]

## Notes
- <any reason a batch could not be further parallelised>
```

## Anti-Patterns

- **A "parallel" run that serialises anyway.** A chain that
  pretends to parallelise but waits for each step in order is
  slower than a clean sequential run. The plan must be honest.
- **A plan that hides the cost of synthesis.** Two parallel steps
  save wall-clock time only if the synthesis is fast. If the
  synthesis is the bottleneck, parallel does not help.
- **A plan that races on the same file.** Two steps both writing
  `plan/MAIN_PLAN.md` is a race; the second write wins. The
  dependency check must catch this.

## Related Skills

- `dynamic-workflow` - the harness design template; this skill is
  the runtime check that the plan is actually parallelisable.
- `plan-orchestrate` - the multi-plan DAG; this skill is the
  intra-plan parallelism check.