# /test

Run the project's test suite. Stack-agnostic via `<workspace>/.loop/dev_config.json`.
Use before release, after a feature, or as a CI gate.

## How To Interpret

If the user says `/test`, `run the tests`, `is the build green`, or asks for a
test pass, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `commands/test.md` (this file)
3. `<workspace>/.loop/dev_config.json` (the test config; reads `test.command`)

## Loop

```text
READ .loop/dev_config.json -> RUN the configured test command -> EMIT pass/fail
```

## Script

```bash
python scripts/dev.py test --workspace <ws>            # standard
python scripts/dev.py test --workspace <ws> --coverage  # coverage variant
```

## Output

1. The configured test command's stdout + exit code
2. A clear "no config" message if `<workspace>/.loop/dev_config.json` does
   not declare a `test.command`

## Continuation

A failing test is a Stop Condition. A passing test returns 0. A
workspace without the config file is guided to add one.
