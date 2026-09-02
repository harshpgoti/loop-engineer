# /code-reviewer

Run the two-axis code review (Spec vs Standards) on the current diff. Use after
/develop-product changes and before marking a task complete. The skill is wired
into the chain by default; this command is for direct invocation.

## How To Interpret

If the user says `/code-reviewer`, `review the code`, `two-axis review`, or
asks for a Spec-vs-Standards review, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/code-reviewer/SKILL.md`
3. the current diff
4. `plan/BUILD_CONTEXT.md` (the active task's acceptance)
5. `CONTEXT.md`, `DECISIONS.md` (the repo's vocabulary)

## Loop

```text
READ the diff + the task's acceptance -> READ CONTEXT.md + DECISIONS.md -> EMIT Spec findings + Standards findings (kept separate)
```

## Output

`plan/CODE_REVIEW.md` with two sections: `## Spec` and `## Standards`,
each with findings worst-first, and one closing line per axis. The
reviewer never picks a single winner across the axes.

## Continuation

A passing review is one axis with no findings; a clean run is a valid
result (do not manufacture findings). A failing review is a Stop
Condition; the chain halts until the user resolves.

## Related Skills

- `codebase-design` - the seam vocabulary the reviewer uses.
- `tdd` - the test bar the reviewer enforces.
- `safeguard` - the prompt-level defence the reviewer applies to diff content.