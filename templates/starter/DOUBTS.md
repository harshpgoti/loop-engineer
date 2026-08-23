# Doubts

This file captures open questions, user decisions, contradictions, and grill points. Agents must ask the user directly when available. If the user is not available, record the doubt here and proceed only with safe, reversible work.

## Rules

- Ask first if the answer changes product strategy, compliance posture, architecture, pricing, customer targeting, or irreversible build work.
- If the user is unavailable, write the question here with status `open`.
- **Never hand-edit a status.** Use the commands, so the count every other command reads actually moves:

  ```bash
  loop doubts ask                                   # this round only, each with its recommended answer
  loop doubts resolve DQ-001 "<answer>" --decision D-014
  loop doubts defer   DQ-002 "<why, and what it blocks>"
  loop doubts questionnaire                         # questions somebody else has to answer
  loop doubts lint                                  # entries whose status contradicts their content
  ```

- `/plan-loop`, `/develop-product`, and `/loop-engine` raise these for you - you do not have to read this file.
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
| `Depends on` | no | Doubt ids that must be settled first. Puts this question in a **later round** instead of the current one |
| `Ask` | no | Who holds the answer, when it is not the user. Takes the question off the build's critical path and into a questionnaire |

Only a **blocking** open doubt holds up task compilation. Mark a commercial or
nice-to-have question `Blocking: no` and it stays visible without stalling the build.

## Rounds, not a wall of questions

`loop doubts ask` asks the **frontier**: the blocking questions whose prerequisites are
already settled. Everything else waits, and the output says what it waits on.

```markdown
### DQ-009: Which PMS do we integrate first?
- **Status:** open
- **Blocking:** yes
- **Depends on:** DQ-005
- **Question:** Tebra, DrChrono, or WebPT?
- **Default if unavailable:** Whichever the design partner already runs.
```

Without the `Depends on:` line this gets asked in the same breath as DQ-005, and the only
honest answer is "ask me again once I have a partner". Resolving **or deferring** DQ-005
moves DQ-009 into the next round; a deferral counts, because going with the default is a
decision. Prerequisite loops are asked together rather than never, and reported by `lint`.

`lint` also catches the common case: a prerequisite written in prose
(`Default if unavailable: Decide when DQ-005 resolves.`) that no code can see.

## Questions that are not yours to answer

Some questions need a payer rep, a clinician, an accountant, a lawyer. Left unmarked they
block the build until that person happens to be in the room.

```markdown
- **Ask:** the clearinghouse rep
```

That doubt leaves the round entirely. `loop doubts questionnaire` writes
`plan/questionnaires/<who>.md` - their questions, why each one matters, and the assumption
we proceed on if they never reply - to send async. Answers come back through
`loop doubts resolve`, so the reply lands in the same place every other answer does.

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
