# /grill

Run the structured interview from `skills/plan-loop/phases/grill.md`. The
interview covers 11 categories of planning questions (product, pricing,
legal, ops, security, design, engineering, data, integrations, team, meta).
Each question has a `Default if unavailable` answer.

## How To Interpret

If the user says `/grill`, `run the grill`, `ask me the planning questions`,
or asks to start the planning interview, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/plan-loop/phases/grill.md` (the question catalog)
3. `scripts/grill.py` (the runtime)

## Loop

```text
READ the question catalog -> ASK each question (or use the default) -> WRITE answers to <workspace>/plan/GRILL_ANSWERS.md
```

## Script

```bash
python scripts/grill.py --workspace <ws> --non-interactive   # use defaults
python scripts/grill.py --workspace <ws> --render-only    # print as Markdown
python scripts/grill.py --workspace <ws>                   # interactive
```

## Output

A single Markdown file at `<workspace>/plan/GRILL_ANSWERS.md` with
the 66 questions across 11 categories, each with the question, the
default, and the user's answer.

## Continuation

`/plan-loop` reads `plan/GRILL_ANSWERS.md` (when present) as the
input to the planning phase. The grill answers feed the wedge, the
buyer, the user, the data, and the kill criterion that the plan
uses.