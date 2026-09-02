# /ml-engineering

Run the ML engineering review: dataset versioning, training, evaluation, model
registry, inference, monitoring, rollback. Use when a product trains, selects,
serves, or monitors learned models. The skill is wired into the chain; this
command is for direct invocation.

## How To Interpret

If the user says `/ml-engineering`, `ML review`, `model check`, `eval set
review`, or asks for an ML pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/ml-engineering/SKILL.md`
3. `GATES.yml`, `DOUBTS.md`
4. the model registry, eval set, monitoring dashboards

## Loop

```text
READ dataset + model + eval state -> VERIFY versioning, leakage, baseline, threshold -> VERIFY shadow/canary + rollback -> EMIT findings
```

## Output

- Experiment identity
- Metrics versus baseline
- Slice results
- Provenance
- Validation evidence (frozen-dataset, leakage, drift, subgroup, robustness, latency, cost)
- Model-card, online/offline agreement, rollback evidence
- Deployment decision and rollback conditions
- Findings (with the Pre-Report Gate applied)

## Continuation

A model deployment requires shadow or canary evaluation plus tested
rollback before the model is allowed to take traffic. A model without
provenance is not deployable.