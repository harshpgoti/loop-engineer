---
name: code-reviewer
description: Review changed product code on two separate axes - Spec (does it do what the task asked?) and Standards (is it built the way this repo builds things?). Use after /develop-product changes and before marking a task complete.
---

# Code Reviewer

Two axes, reported separately.

- **Spec** - does the change do what the task asked for?
- **Standards** - is it built the way this repo builds things?

A change can pass one and fail the other: code that follows every convention while
implementing the wrong thing, or code that does exactly what was asked while breaking the
codebase's conventions. Report them under separate headings and **do not merge or re-rank
across them** - one axis masking the other is what the separation prevents.

## Required Reads

| Axis | Source of truth |
|------|-----------------|
| both | the diff or changed files |
| Spec | the active task in `plan/BUILD_CONTEXT.md` - its `acceptance` list is the spec |
| Spec | the active feature's `spec.md`, when one exists |
| Spec | `GATES.yml` for the gate this task sits behind |
| Standards | `CONTEXT.md` - the repo's own vocabulary and conventions (`loop glossary`) |
| Standards | `DECISIONS.md` - decisions in the area being changed |
| Standards | `skills/codebase-design/SKILL.md` - module, interface, seam, depth |
| Standards | `skills/tdd/SKILL.md` - the bar the tests have to clear |
| both | the test output |

The acceptance criteria are the spec. The harness records them per task, so this axis is
never a guess about intent.

## Spec axis

Report, quoting the criterion for each finding:

1. **Missing or partial** - what the task asked for that is not there.
2. **Scope creep** - behaviour in the diff nobody asked for. Speculative generality counts.
3. **Wrong** - a criterion that looks implemented but the implementation does not satisfy.

Also: does the change satisfy its gate, or does the gate need to move?

## Standards axis

First, whatever `CONTEXT.md` and `DECISIONS.md` document. **A documented repo standard always
wins** - where it endorses something the baseline below would flag, the standard is right and
the flag is suppressed. Skip anything tooling already enforces.

Then the harness rules that do not depend on the repo documenting anything:

- Tests exist and are meaningful (`AGENTS.md` #10) - and clear the `tdd` bar: not
  implementation-coupled, not tautological, at an agreed seam.
- Sensitive data and secrets protected (`AGENTS.md` #6).
- Tenant-owned queries server-scoped and tested, if the product is multi-tenant
  (`AGENTS.md` #7).
- Minimal diff, matching surrounding conventions, no drive-by refactors (`AGENTS.md` #9).
- Idempotent workflows, audited transitions (`AGENTS.md` #8).

### Smell baseline

Always applied, always a judgement call - label it as a possibility ("possible Feature Envy"),
never as a violation. Each reads *what it is* -> *how to fix it*.

| Smell | What it is | Fix |
|-------|-----------|-----|
| Mysterious Name | A name that does not reveal what it does or holds | Rename it. If no honest name comes, the design is murky |
| Duplicated Code | The same logic shape in more than one hunk or file | Extract the shape, call it from both |
| Feature Envy | A method reaching into another object's data more than its own | Move the method onto the data it envies |
| Data Clumps | The same few fields keep travelling together | Bundle them into one type and pass that |
| Primitive Obsession | A string or primitive standing in for a domain concept | Give the concept its own small type - and a `CONTEXT.md` entry |
| Repeated Switches | The same branch on the same type recurring across the change | Polymorphism, or one map both sites share |
| Shotgun Surgery | One logical change forcing scattered edits across many files | Gather what changes together into one module |
| Divergent Change | One module edited for several unrelated reasons | Split so each changes for one reason |
| Speculative Generality | Abstraction or hooks for needs the task does not have | Delete it. Inline back until a real need shows |
| Message Chains | Long `a.b().c().d()` the caller should not depend on | Hide the walk behind one method on the first object |
| Middle Man | A module that mostly delegates onward | Cut it, call the real target |
| Refused Bequest | A subclass ignoring or overriding most of what it inherits | Drop the inheritance, use composition |

Shallowness is worth naming when you see it: an interface nearly as complex as the
implementation behind it. Apply the deletion test - if deleting the module would make
complexity vanish rather than reappear across callers, say so.

## Output

Two headings. Under each, findings worst-first:

```text
## Spec
  <criterion quoted> - missing / partial / wrong / not asked for
  <what is actually there>
  <suggested fix>

## Standards
  <severity> <file:symbol> - <the standard cited, or the smell named>
  <suggested fix>
```

Close with one line per axis: how many findings, and the worst one in each. **Do not pick a
single winner across the axes.**

No findings on an axis? Say so, and list the residual risk or test gap that remains anyway.

## Never

The builder does not approve its own work (`AGENTS.md`). Run this as a separate pass with the
diff in front of you, not as a self-assessment written from memory of what you intended.
