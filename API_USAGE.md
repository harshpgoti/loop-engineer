# Direct LLM API Usage

Use this when calling an LLM directly through an API without an IDE agent.

## Always-on lifecycle (between API turns)

Before each product loop turn:

```bash
loop session-start --tool api --command "<action>"
```

Inject `plan/SESSION_MANIFEST.md` into context. After the turn:

```bash
loop session-end --tool api --summary "<one-line>"
```

See `docs/SESSION_LIFECYCLE.md`.

## Source Files

Use command files as system/developer instructions, paired with the matching skill
file as additional context: `commands/<name>.md` + `skills/<name>/SKILL.md`. See the
full, current list in **`AGENTS.md`'s Portable Commands table** (or
`LOOP_COMMANDS.md`) — not duplicated here, since a second copy drifts stale every
time a command is added.

## Minimum User Context

Send these files in the user message or retrieval context:

- `memories/MEMORY.md`
- `DOUBTS.md`
- `plan/main_plan.md`
- `TASKS.yml`
- `GATES.yml`
- `HANDOFF.md`

## Prompt Template

```text
Command: /plan

Context files:
[paste or retrieve MEMORY.md]
[paste or retrieve DOUBTS.md]
[paste or retrieve plan/main_plan.md]
[paste or retrieve TASKS.yml]
[paste or retrieve GATES.yml]
[paste or retrieve HANDOFF.md]

Execute only the command. Return file updates as patches.
```

## Safety

- No real sensitive or regulated data in prompts unless the relevant gate passes.
- Prefer synthetic data.
- Ask or log doubts before irreversible decisions.
