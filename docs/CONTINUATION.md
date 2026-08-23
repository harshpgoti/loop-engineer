# Continuation Contract

**A loop command runs to its terminus, not to the end of its own chunk.**

This is what makes Loop Engineer a loop engine rather than a set of scripts the
user has to chain by hand. If a command finishes its slice and replies *"now run
`/spec-checklist`"* for work it could have done itself, that is a defect - fix the
command, don't ask the user to compensate.

## The three rules

### 1. Run to terminus

Every command declares a **terminus**: the furthest state it owns. The agent
cascades automatically through intermediate phases until it reaches the terminus
or hits a Stop Condition.

> **Never end a turn by instructing the user to run a command you could have run.**

The next phase is not a suggestion to relay - it is the next thing to execute.
`scripts/plan_phase.py` recomputes the phase deterministically from state, so
after finishing a phase, recompute and continue.

### 2. Reconcile side effects in the same run

Work rarely affects only one file. If what you did invalidates something else,
fix it now - do not leave the workspace inconsistent for the next session:

| You changed | Also reconcile |
|---|---|
| A spec / requirement | `spec.md`, `clarifications.md`, and the tasks derived from it |
| Anything behind a passed gate | Set that `GATES.yml` entry back to `blocked` with a `note:`, and add the rework tasks |
| Scope of a built feature | `TASKS.yml` entries for the rework + flag drift for `/feature-converge` |
| A durable decision | `DECISIONS.md`, plus the doubt it resolves in `DOUBTS.md` |
| Anything at all | `memories/MEMORY.md`, `HANDOFF.md` at closeout |

If a consequence genuinely cannot be executed now (needs the build, needs the
user), **record it as a task or doubt** - that still counts as reconciling. What
is forbidden is silently leaving stale state.

### 3. Stop only on a Stop Condition - and say why

Legitimate reasons to stop before the terminus:

1. **User decision required** - a real choice the plan/code cannot settle
   (strategic pivot, irreversible scope call, vendor lock-in).
2. **Human-approval gate** - `GATES.yml` requires explicit approval, or the action
   is high-risk/external/irreversible (deploy, spend, send, publish, delete).
3. **Sensitive-data boundary** - regulated data before `G-SENSITIVE-DATA` passes.
4. **Missing information** that cannot be safely defaulted, with no evidence
   available.
5. **Context exhaustion** - run `/compact-loop` first, then continue.

When you stop, report **which condition fired and what you need** - not a bare
"run `/x` next". A stop is a question to the user, never a chore assignment.

## Termini

| Command | Cascades through | Terminus |
|---|---|---|
| `/plan-loop` | grill → council → (ultraplan) → spec-clarify → spec-checklist → resolve-doubts → task-compiler | Tasks compiled + go/no-go for build |
| `/spec-clarify` | → spec-checklist → resolve-doubts → task-compiler | Same as above |
| `/spec-checklist` | → resolve-doubts → task-compiler | Same as above |
| `/resolve-doubts` | → task-compiler (on GO) | Same as above |
| `/ultraplan-loop` | one step's pack → feature spec → clarify → checklist | Step's pack complete, spec ready |
| `/develop-product` | task → diff → tests → review → QA → security → converge → prod-gap | Task done, gates evaluated, drift checked |
| `/loop-engine` | plan terminus **→ crosses into build when gates pass** | Build slice complete |
| `/revise-plan` | edit → reconcile gates/tasks | Plan consistent, rework tasks created |
| `/feature-new` | → spec-clarify → … | Planning terminus |
| `/setup-loop-engine` | setup → wire agents | Workspace ready |

**Read-only commands do not cascade** (`/ask-loop`, `/status`, `/doctor`,
`/prod-gap`, `/release-check`): they report and hand off by design. They must
still state the recommended next command - that is their product, not a
continuation failure.

## Applying it in a command file

Every mutating command carries both sections:

```markdown
## Continuation

Terminus: <furthest state this command owns>.
After this work, continue automatically to <next>; do not stop and ask the user
to run it. Recompute the phase (`scripts/plan_phase.py`) and keep going until
terminus or a Stop Condition.

## Stop Conditions

- <condition> - report what is needed and why
```

## Anti-patterns

- ❌ "Planning is complete. Now run `/spec-checklist`." → ✅ run it, then report both.
- ❌ Ending after one phase because the phase file said `Next phase: X`.
- ❌ Changing a requirement and leaving `TASKS.yml` describing the old one.
- ❌ Marking a gate passed while its criteria are unmet, to keep the cascade going.
- ❌ Cascading past a human-approval gate because "the loop should continue".
