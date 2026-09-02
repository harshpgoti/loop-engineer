# /error-handling

Apply cross-stack error-handling conventions. Use when designing, reviewing, or
debugging how the server shapes internal exceptions into the public response envelope.

## How To Interpret

If the user says `/error-handling`, `error handling`, `exception handling`, `error
envelope`, `typed errors`, or asks how a failure path should look from the user's side,
execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/error-handling/SKILL.md`
3. `skills/api-design/SKILL.md` (the envelope shape)
4. `skills/security-compliance/SKILL.md` (what must not be in the body)
5. `plan/main_plan.md` and `codebase-design` (the codebase's existing error types)

## Loop

```text
READ EXISTING ERROR TYPES -> MAP TO ENVELOPE -> FLAG LEAKS -> WRITE ERROR CONTRACT
```

## Output (locked)

```text
## Error Handling: <surface>

### Internal exception layer
- <typed error> -> maps to <status code>, <code>, <envelope fields>

### External response layer
- The envelope defined in /api-design; no stack traces, no internal class names, no
  file paths, no query strings with credentials.

### Leaks
- <location>: <sensitive field exposed to the user>

### Open questions
- <question for the user>
```

## Continuation

A new typed error is a contract change. Mirror it into the API spec, the error envelope
table, and the `qa-validation` golden cases (one per status code, one per `code`).

## Output

1. The error contract output
2. Internal-exception to external-envelope mapping
3. Leaks flagged (with severity)
4. Open questions
5. Next action (apply, fix, or ask)