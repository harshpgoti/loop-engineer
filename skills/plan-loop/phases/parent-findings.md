# Phase: Parent Findings

> Loaded by `skills/plan-loop/SKILL.md` when `PHASE: parent-findings` - the main
> product's plan has moved and this sub-product has not answered for it yet. Answer
> first, or the rest of this loop plans on top of a constraint that has already changed.

## Purpose

This sub-product inherits the master plan's decisions. When the master plan changes -
or when the two plans contradict each other - the difference shows up here as a
**finding**. This phase turns each one into a question with a recommended answer, gets
a decision, and acts on it in this session.

Findings are **derived**, not queued: they are recomputed from both plans every
session. Nothing needs draining, and answering one records the decision, not a copy of
the question.

## Required Reads

- `plan/SESSION_MANIFEST.md` → **Parent findings** block
- `plan/PARENT_CONTEXT.md` (what this sub-product inherits)
- `plan/main_plan.md`, `DECISIONS.md`, `DOUBTS.md`, `TASKS.yml`, `GATES.yml`

```bash
loop findings ask      # each open finding as a question with a recommended answer
loop findings list     # the same, as plain text
```

## Process

1. **Get the questions**: `loop findings ask`. Each returns a finding id, the
   disagreement in both sides' own words, and a **recommended** answer with its reason.
   The recommendation is deterministic - derived from the finding's kind, never invented.

2. **Reuse, don't re-ask.** If `DECISIONS.md`, `plan/SESSION_RECALL.md`, or a resolved
   `DOUBTS.md` entry already settles one, apply that and tell the user - do not ask again.

3. **Apply the recommendation without asking when it is unambiguous** - a new platform
   constraint this plan says nothing about, nothing built against it yet, no gate
   reopened. Report what you applied. Asking about every finding is how the old
   approval queue died; `docs/CONTINUATION.md` requires you to cascade, not to
   interrogate.

4. **Ask, one at a time, when the answer is a real choice** - the two plans state
   different things and this workspace has evidence, or accepting would reopen a gate
   or invalidate in-progress work. Give the user:

   - **What disagrees** - both values, in the two plans' own words
   - **Recommended:** the suggested decision, and why
   - **What it costs** - which tasks, gates, or built code change if they accept
   - The three answers: **accept** (change this plan), **decline** (the master plan is
     wrong), **defer** (not now)

5. **Record every answer immediately:**

   ```bash
   loop findings resolve <finding-id> accepted --note "<what changed>"
   loop findings resolve <finding-id> declined --note "<why the master plan is wrong>"
   loop findings resolve <finding-id> deferred --note "<when this gets decided>"
   ```

   A decision is bound to the values it was made about. If the master plan changes that
   value again, the finding comes back for a fresh answer - a stale "no" can never
   silently suppress a new constraint.

6. **Reconcile the consequences in this same run** (`docs/CONTINUATION.md`):

   | Answer | Also do |
   |--------|---------|
   | **accepted** | Edit the plan file the finding names. Log it in `DECISIONS.md`. Reopen any `GATES.yml` entry it invalidates. Add rework `TASKS.yml` entries. |
   | **declined** | Record why in `DECISIONS.md` with the evidence. Raise it against the master plan - a doubt in this workspace, and tell the user to run `/revise-plan` in the main product. |
   | **deferred** | Add a `DOUBTS.md` entry with `loop doubts add`, including what it blocks and when it must be decided. |

7. **Confirm the inbox is clear**: `loop findings list` should report nothing open. Only
   then does this workspace's parent watermark advance - which is what stops the same
   change being raised again next session.

## Rules

- **A finding is a disagreement, not a verdict.** The master plan is not automatically
  right. A sub-product that discovered a real constraint the platform decision ignored
  is the side that should win.
- **Never edit the parent's files from here.** When the master plan is wrong, say so and
  route the user to `/revise-plan` in the main product.
- Never mark a finding resolved without doing what the answer implies. A recorded
  decision with no edit behind it is the failure mode this replaced.
- Do not batch questions into one wall of text. One finding, one question, one answer.

## Output

- Findings applied without asking, and what changed for each
- Findings asked about, the answer given, and the consequence executed
- `DECISIONS.md` entries written, gates reopened, tasks added
- Doubts raised for anything deferred
- Remaining open findings after the pass

## Continue automatically

Execute the branch - do not report it and stop:

- **Inbox clear** → continue the pipeline: load `phases/hierarchy.md` if this workspace
  has sub-products of its own with `error` findings, otherwise `phases/council.md` (or
  `phases/ultraplan.md` when `plan/PLAN_SCALE.md` is platform and a step is incomplete).
- **A finding needs a user decision** → that is Stop Condition #1. Name the finding,
  both values, the recommendation, and what accepting costs. See `docs/CONTINUATION.md`.
