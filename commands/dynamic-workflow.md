# /dynamic-workflow

Design a task-local harness for a recurring multi-step task using the
{Objective, Inputs, Loop, Eval, Handoff, Human_gate} template.

## How To Interpret

If the user says `/dynamic-workflow`, `design a harness`, `recurring workflow`, or asks
to formalise a multi-step task that keeps recurring without an obvious skill, execute
this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/dynamic-workflow-mode/SKILL.md`
3. `state.db` (search for prior invocations of the same task)
4. `plan/main_plan.md` (project context)
5. `TASKS.yml` (existing tasks)
6. `capabilities.json` (what tools are reachable)

## Loop

```text
DETECT RECURRING TASK -> FILL TEMPLATE -> PICK HARNESS SHAPE -> DECIDE STOP CONDITIONS -> WRITE HARNESS FILE
```

## Template

```yaml
objective: <one sentence - what "done" means for one run>
inputs: <what this run needs to start; concrete files, queries, decisions>
loop: <the deterministic steps; numbered, each with success criterion>
eval: <how a run is scored; pass@k, pass^k, or a fixed rubric>
handoff: <what the run produces; the next consumer, file, or command>
human_gate: <if any, what blocks the chain from continuing automatically>
```

## Decision Tree

| Question | Action |
|---|---|
| Single focused change? | Do it inline. No harness. |
| Has a written spec / RFC? | DAG (ralphinho-rfc-pipeline) or continuous-agent-loop depending on parallel value. |
| Many variations of the same thing? | Infinite-loop with eval gate. |
| Default | Sequential with a de-sloppify pass. |

## Stop Conditions (mandatory)

Every harness must declare:
- `max_iterations` (typical: 5 adversarial, 20 sequential);
- `max_cost` in tokens or dollars;
- `max_duration` in wall-clock;
- `completion_signal` - the observable event declaring "done";
- `fail_signal` - the observable event declaring "escalate to user."

## Output

1. The filled template
2. The picked harness shape and the LE skill that executes it
3. Stop conditions with named observable signals
4. The path of the harness file (typically `<workspace>/.loop/harnesses/<name>.md`)

## Continuation

If the harness recurs a third time, promote it to a permanent skill in `skills/`. If the
work becomes a product feature, route through `/feature-new` instead.