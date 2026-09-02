# /config-gc

Garbage-collect stale configuration. Walk a workspace, identify env vars, feature
flags, and config entries that are no longer referenced, and emit a deletion
report. Use when a config file has grown unboundedly, when onboarding flagged
dead config, or as a periodic audit before a release.

## How To Interpret

If the user says `/config-gc`, `clean up config`, `find dead env vars`, `what's
in .env that nothing reads`, or asks to audit config, execute this file
directly.

## Required Reads

1. `AGENTS.md`
2. `skills/config-gc/SKILL.md`
3. the workspace's config files (`.env`, `pyproject.toml`, `package.json`,
   `tsconfig.json`, `Cargo.toml`, etc.)
4. the workspace's source tree (for reference scan)

## Loop

```text
INVENTORY keys -> REFERENCE SCAN -> DOC SCAN -> LAST-TOUCHED via git log -> EMIT REPORT
```

## Output

`plan/CONFIG_GC.md` with:

- Summary (live / dead / shadowed)
- Dead keys with last-touched date
- Live keys with the file:line that references them
- Shadows (same key, different value, in different configs)

The report is a **proposal**, not a deletion. The user approves; deletion
is a separate `TASKS.yml` entry.

## Continuation

The chain emits the report; the user picks the dead keys to remove; the
deletion is a `/develop-product` task. After deletion, the test suite
runs to confirm nothing broke.