---
name: ml-engineering
description: Designs and validates ML datasets, training, evaluation, model registry, inference, monitoring, and rollback. Use when a product trains, selects, serves, or monitors learned models.
---

# ML Engineering

Inherits `docs/SKILL_CONTRACT.md`.

## Required method

1. Version dataset, code, configuration, environment, seed, and artifact provenance.
2. Separate train, validation, and test data; detect leakage and duplicated entities.
3. Define baseline, task and slice metrics, thresholds, and failure costs before training.
4. Record reproducibility limits and distinguish measured evidence from inference.
5. Stage deployment with shadow or canary evaluation, monitoring, and tested rollback.
6. Require human approval for high-impact decisions and sensitive-data use.

## Validation

- Frozen-dataset evaluation or a documented nondeterminism budget
- Leakage, drift, subgroup, robustness, latency, and cost checks where relevant
- Model-card, provenance, online/offline agreement, and rollback evidence

## Output

Return experiment identity, metrics versus baseline, slice results, provenance, validation
evidence, structured findings, deployment decision, and rollback conditions.
