# Doubts

This file captures open questions, user decisions, contradictions, and grill points. Agents must ask the user directly when available. If the user is not available, record the doubt here and proceed only with safe, reversible work.

## Rules

- Ask first if the answer changes product strategy, compliance posture, architecture, pricing, customer targeting, or irreversible build work.
- If the user is unavailable, write the question here with status `open`.
- **Never hand-edit a status.** Use the commands, so the count every other command reads actually moves:

  ```bash
  loop doubts ask                                   # blocking doubts, each with its recommended answer
  loop doubts resolve DQ-001 "<answer>" --decision D-014
  loop doubts defer   DQ-002 "<why, and what it blocks>"
  loop doubts lint                                  # entries whose status contradicts their content
  ```

- `/plan-loop`, `/product-develop`, and `/loop-engine` raise these for you - you do not have to read this file.
- Add the decision to `DECISIONS.md` too when it affects strategy or architecture.

## Entry format

Every entry needs an `### DQ-NNN: title` heading and these fields. Anything else is
invisible to the parser, and therefore to every command:

| Field | Required | Meaning |
|-------|----------|---------|
| `Status` | yes | `open`, `resolved`, or `deferred`. First word only - qualifiers after it are free text |
| `Blocking` | no | `yes` / `no`. Whether development can safely start. Absent, it is inferred from the wording, defaulting to blocking |
| `Question` | yes | The question itself |
| `Why it matters` | no | What it affects |
| `Default if unavailable` | no | **This is the recommended answer** the agent offers when it raises the question. Write it as the thing you would actually do |

Only a **blocking** open doubt holds up task compilation. Mark a commercial or
nice-to-have question `Blocking: no` and it stays visible without stalling the build.

## Questions that stop mattering

Some questions are not answered - a later decision removes the reason they were asked.
Record that on the **decision**, not here:

```markdown
## D-014: Pricing is flat fee only
- **Supersedes:** DQ-007, DQ-020
```

Those doubts stop being raised, with the reason shown. A **main product's** decision can
retire a question inside a sub-product this way, which is how a platform-level call
closes questions in the workspaces it governs.

## Open Doubts

### DQ-001: Product initialization
- **Status:** open
- **Blocking:** yes
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
