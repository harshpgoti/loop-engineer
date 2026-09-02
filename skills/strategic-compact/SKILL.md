---
name: strategic-compact
description: Suggest /compact at phase boundaries (research -> planning, planning -> implementation, etc.) rather than arbitrary token thresholds. Reads the transcript usage and proposes the most valuable compact target. Use when a long session is approaching the context limit, when switching tools, or when planning /compact-loop.
---

# Strategic Compact

Inherits `docs/SKILL_CONTRACT.md`.

A heuristic for when to compact. The default "/compact at 80% of context" is
indiscriminate; it loses the recent reasoning that matters most. The
strategic version proposes a compact at a **phase boundary** where the
prior phase's work is durable on disk and the new phase needs a fresh
working set.

## When to use

- A session is approaching the context limit and `/compact-loop` is being
  considered.
- The chain is about to switch tools (Claude Code -> Cursor, etc.).
- The chain is moving from one phase to another (research -> planning,
  planning -> implementation, etc.) and a clean slate would help.

## When NOT to use

- A one-shot task that does not need a compact.
- Mid-implementation compaction that loses variable names, file paths,
  and partial state - the cost of the compact is higher than the cost
  of running the agent longer.
- After a failed approach, before the next attempt - clear the dead-end
  reasoning with a fresh start instead of a partial compact.

## Phase Boundaries That Are Good Compac Targets

| Transition | Why compact here |
|---|---|
| Research -> Planning | Research context is bulky (papers, scans, comparisons). The plan is the distilled output. The compact can drop the research. |
| Planning -> Implementation | The plan is written to disk (a file, or the task list if the agent has it). The implementation needs a fresh working set. |
| Implementation -> Testing | Tests reference recent code. Keep the implementation context; the tests can be re-derived. |
| Debugging -> Next feature | Debug traces pollute context. Compact before moving on; the finding lives in the commit and `memories/MEMORY.md`. |
| After a failed approach | The dead-end reasoning is the largest context consumer. A fresh start beats a partial compact. |

## Phase Boundaries That Are Not

- **Mid-implementation.** Losing variable names, file paths, and partial
  state is costly. Compact only when the work is on disk and the
  working set can be re-derived.
- **Mid-debugging.** The bug is in the recent context; the fix is in the
  recent context. Compact at the **end** of debugging, not the middle.
- **Mid-conversation with the user.** The user's questions and answers
  are the most recent context; compacting them is rude and lossy.

## Transcript Usage Threshold

The skill's input is the transcript-usage signal:

| Window size | Suggest compact at |
|---|---|
| 200k tokens | 160k |
| 1M tokens | 800k (or the phase boundary, whichever comes first) |

The threshold is conservative; the goal is to suggest before the
session is forced to compact mid-reasoning. The user may override the
threshold with `--threshold <n>`.

## What Survives the Compact

| Persists | Lost |
|---|---|
| `CLAUDE.md` instructions | Intermediate reasoning and analysis |
| Files on disk | File contents previously read (read again on demand) |
| Memory files (`~/.loop-engineer/data/memories/`, `state.db`) | Multi-step conversation context |
| Git state (commits, branches) | Tool call history and counts |
| The task list (only if the agent has a todo tool) | Nuanced user preferences stated verbally |
| The active feature pointer | `HANDOFF.md` content (re-read on demand) |

The "what persists" table is the survival kit. The "what is lost" table
is the cost. The compact is worth it when the cost is small relative
to the gain.

## Workflow

1. Read the transcript-usage signal.
2. If the signal is below the threshold, do nothing. Suggest again on
   the next phase boundary.
3. If the signal is above the threshold:
   - check whether the current state is a phase boundary;
   - if yes, propose the compact with the specific target (e.g.
     "compact now; the plan is in `plan/main_plan.md`; the implementation
     tasks are in `TASKS.yml`");
   - if no, wait for the next phase boundary; warn the user.
4. The user confirms. The harness runs `/compact` (or its tool-specific
   equivalent). The next phase begins with a smaller working set.

## Anti-Patterns

- **Compacting because the percentage is high.** The percentage is a
  signal, not a trigger. The trigger is a phase boundary at which the
  prior phase's work is durable.
- **Compacting in the middle of an active task.** Variable names and
  file paths are not on disk; the agent re-derives them or fails.
  Compact at a natural break, not at 80%.
- **Assuming `CLAUDE.md` is enough context.** `CLAUDE.md` is the
  instruction set, not the working memory. The working memory is
  `state.db` + `memories/MEMORY.md` + the active feature pointer.
- **Compacting instead of writing to memory.** If the agent is about to
  drop an important finding, it should write to `memories/MEMORY.md`
  *first*, then compact. The compact drops the finding; the memory
  preserves it.

## Related Skills

- `compact-loop` - the lower-level /compact-loop skill; this skill is
  the strategist that decides *when* to call it.
- `session-lifecycle` - the always-on session management.
- `memory-review` - the place findings land before a compact.
- `harness` adapters - the per-coding-agent /compact implementation.