# Doubts

This file captures open questions, user decisions, contradictions, and grill points. Agents must ask the user directly when available. If the user is not available, record the doubt here and proceed only with safe, reversible work.

## Rules

- Ask first if the answer changes product strategy, compliance posture, architecture, pricing, customer targeting, or irreversible build work.
- If the user is unavailable, write the question here with status `open`.
- Review this file at the start of `/plan-loop`, `/product-develop`, and `/loop-engine`.
- When the user answers, update status to `resolved` and add the decision to `DECISIONS.md` if it affects strategy or architecture.

## Open Doubts

### DQ-001: Product initialization
- **Status:** open
- **Question:** What product should this loop plan-loop and build?
- **Why it matters:** `plan/main_plan.md`, `plan/`, tasks, gates, and stack choices depend on the product.
- **Default if unavailable:** Do not invent a product. Prepare generic templates only.

### DQ-002: First product step
- **Status:** open
- **Question:** What is the smallest useful first product step/module?
- **Why it matters:** `/plan-loop` should create `plan/step_01_<slug>.md`.
- **Default if unavailable:** Leave step file uncreated.

### DQ-003: Sensitive data and compliance
- **Status:** open
- **Question:** Will this product handle secrets, regulated data, payment data, financial data, children’s data, or other sensitive data?
- **Why it matters:** Gates, logs, test data, storage, and deployment posture depend on it.
- **Default if unavailable:** Treat data as sensitive and use synthetic fixtures only.

## Resolved Doubts

None yet.
