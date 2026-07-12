# /ask-loop

Answer a free-form question about a plan or build that already exists - the user asks, the
agent answers from full plan context (and product code when needed), with citations, and
changes nothing.

## How To Interpret

If the user says `/ask-loop <text>`, execute this file and `skills/ask-loop/SKILL.md`.

Also treat plain language as this command whenever `plan/main_plan.md` is already past
`Status: INITIALIZED` and the user asks a question about the existing product rather than
requesting a change - e.g. "why did we pick this stack?", "what is the target user again?",
"how does auth work?", "where is the billing logic?", "what's built vs still pending?",
"explain the architecture / this decision / this step". Do not make the user type the slash
command explicitly.

This command is **read-only**: it never edits plan, spec, decision, doubt, gate, task, or
product-code files. If the answer implies a change the user wants made, hand off to
`/revise-plan` (plan) or `/product-develop` (code) - do not edit here.

## Required Reads

Full plan context, always all of it - no progressive disclosure - plus build artifacts and,
when a question is implementation-level, the product source code. See
`skills/ask-loop/SKILL.md` -> Required Reads for the exact list (`plan/main_plan.md`, all
`plan/step_*.md`, active feature folder, `DECISIONS.md`, `DOUBTS.md`, `EVIDENCE_LOG.md`,
`TASKS.yml`, `GATES.yml`, `CURRENT_STATE.md`, `HANDOFF.md`, `plan/PROD-GAP.md`,
`DEPLOYMENT_PLAN.md`, `docs/`).

## Wired From

- Any time after `/plan-loop` or `/product-develop` when the user wants to understand what
  exists rather than change it.
- `/status` points here for detail questions (it gives a fixed snapshot; this answers "why"
  and "how").
- `/revise-plan` points here when the user's statement is a question, not a correction.

## Loop

```text
READ FULL PLAN + BUILD CONTEXT -> PARSE QUESTION -> ANSWER FROM PLAN/DOCS
-> ESCALATE TO PRODUCT CODE IF NEEDED -> ROUTE BY INTENT (answer / handoff / flag drift)
-> CITE EVERY CLAIM
```

## Output

1. The answer, in plain language
2. Citations for each claim (file -> section, or code path:line)
3. Any drift or undecided item surfaced while answering
4. Suggested next command if the question implies an action - otherwise none
