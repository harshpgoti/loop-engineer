# /parallel-execution-optimizer

Decide whether a multi-step task should run sequentially or in parallel, and
how to parallelise safely. Use when planning a chain run with more than 2-3
independent steps, or when the runtime is bottlenecked by serial tool calls.

## How To Interpret

If the user says `/parallel-execution-optimizer`, `parallelise this`, `can this run
in parallel`, `find the parallel batches`, or asks how to speed up a multi-step
task, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/parallel-execution-optimizer/SKILL.md`
3. the active task list or step plan

## Loop

```text
IDENTIFY steps -> BUILD dependency graph -> COMPUTE parallel batches -> EMIT plan/PARALLEL_PLAN.md
```

## Output

A single Markdown file with the steps, the dependency graph, the parallel
batches, and notes on any synthesis overhead. The plan is the input to
the chain's run mode (sequential vs parallel).

## Continuation

A plan that is honestly parallel saves wall-clock time. A plan that
hides the synthesis cost does not help. The chain's run mode reads
`plan/PARALLEL_PLAN.md` (when present) and executes the batches.