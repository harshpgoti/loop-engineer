# /format

Format the project. Stack-agnostic via `<workspace>/.loop/dev_config.json`. Use
after writing code, before a commit, or as a CI gate (with `--check`).

## How To Interpret

If the user says `/format`, `format the code`, `run the formatter`, or asks for
formatting, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `commands/format.md` (this file)
3. `<workspace>/.loop/dev_config.json` (the format config; reads `format.command`)

## Loop

```text
READ .loop/dev_config.json -> RUN the configured format command -> EMIT pass/fail
```

## Script

```bash
python scripts/dev.py format --workspace <ws>            # write
python scripts/dev.py format --workspace <ws> --check  # check only
```

## Output

1. The configured format command's stdout + exit code
2. A clear "no config" message if `<workspace>/.loop/dev_config.json` does
   not declare a `format.command`

## Continuation

A failed check (`--check`) is a Stop Condition. A successful write
returns 0. A workspace without the config file is guided to add one.
