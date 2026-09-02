# /commit

Stage all changes and commit with a structured message that follows the
conventional-commits template. Stack-agnostic via `<workspace>/.loop/dev_config.json`.
Use after `/lint`, `/test`, and `/format` have passed.

## How To Interpret

If the user says `/commit`, `commit this`, `make a commit`, or asks to commit the
current work, execute this file directly. The user must supply a structured
message; the command does not auto-author one.

## Required Reads

1. `AGENTS.md`
2. `commands/commit.md` (this file)
3. `<workspace>/.loop/dev_config.json` (the commit config)

## Loop

```text
READ .loop/dev_config.json -> VALIDATE the message against the template -> STAGE all changes -> COMMIT
```

## Script

```bash
python scripts/dev.py commit --workspace <ws> --message "feat(loop): add /lint command"
```

## Output

1. Validation result (type, scope, subject length)
2. The git commit result (commit hash + summary)
3. A clear "no config" message if `<workspace>/.loop/dev_config.json` does
   not declare a commit config

## Continuation

After a successful commit, the chain continues with the next action
(from `HANDOFF.md`). A validation failure is a Stop Condition; the user
authors a corrected message and re-runs.

## Commit Message Template

```
<type>(<scope>): <subject>

<body>

<footer>
```

Allowed types (configurable): `feat`, `fix`, `docs`, `refactor`, `test`,
`chore`. Subject max length: 72 chars.
