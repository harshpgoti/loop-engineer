# /lint

Run the project's linter. Stack-agnostic via `<workspace>/.loop/dev_config.json`.
Use before committing or as a CI gate.

## How To Interpret

If the user says `/lint`, `run the linter`, `check the code style`, or asks for a
lint pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `commands/lint.md` (this file)
3. `<workspace>/.loop/dev_config.json` (the lint config; reads `lint.command`)

## Loop

```text
READ .loop/dev_config.json -> RUN the configured lint command -> EMIT pass/fail
```

## Script

```bash
python scripts/dev.py lint --workspace <ws>            # check
python scripts/dev.py lint --workspace <ws> --fix     # auto-fix (if configured)
```

## Output

1. The configured lint command's stdout + exit code
2. A clear "no config" message if `<workspace>/.loop/dev_config.json` does
   not declare a `lint.command`

## Continuation

A failing lint is a Stop Condition; the chain halts until the user
fixes or accepts. A passing lint returns 0. A workspace without the
config file is guided to add one.
