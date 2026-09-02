---
name: config-gc
description: Garbage-collect stale configuration. Walk a workspace, identify configs that are no longer referenced (env vars, feature flags, build settings, dependency entries), and emit a deletion report. Use when a config file has grown unboundedly, when onboarding flagged dead config, or as a periodic audit before a release.
---

# Config GC

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic walker that finds configuration that is no longer
referenced. A config is "live" if some code or doc reads it; "dead" if
nothing does. The skill is **read-only by default**; deletion is a
separate, approved step.

## When to use

- A config file (`.env`, `pyproject.toml`, `package.json`, `tsconfig.json`,
  `Cargo.toml`) has grown; many entries look unused.
- Onboarding flagged dead config.
- A periodic audit before a release finds the config surface is bigger
  than the code surface.
- A feature flag rollout is complete and the flag's "off" branch can
  be removed.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| Removing a single env var | edit the file |
| A secret rotation | the secret store, not config-gc |
| Renaming a config key | a planned migration, not GC |

## The Walk

For each config surface, four passes:

| Pass | What it does |
|---|---|
| Inventory | list every key, value, and source location |
| Reference scan | grep the entire codebase (excluding the config file itself) for each key |
| Doc scan | grep docs, READMEs, runbooks, ADRs for each key |
| Last-touched | git log -L on the key, when present |

A key is **live** if any of the four passes finds a reference outside
the config file. A key is **dead** if all four are empty.

## Output

```markdown
# Config GC Report: <workspace>

## Summary
- keys scanned: <n>
- live: <n> | dead: <n> | shadowed: <n> (same name, different value, in another config)

## Dead keys (recommended removal)
- <config-file>:<key>: <value> (last touched <date>)
  reference scan: no
  doc scan: no
  shadowed: no

## Live keys (kept)
- <config-file>:<key>: <value> (live because <file:line reference>)

## Shadows
- <config-file-A>:<key>=X and <config-file-B>:<key>=Y. Resolve to one.
```

The report is committed under `plan/CONFIG_GC.md` and (optionally) a
re-runnable scanner under the active workspace's `scripts/` directory is
generated for the user to invoke on demand.

## Deletion Discipline

Dead-key removal is a mutating action. The skill's output is a
**proposal**, not a deletion. The user approves the report; the
deletion is a separate task in `TASKS.yml`. The deletion:

- runs the test suite to confirm nothing broke;
- commits the change with a message naming the report;
- updates any docs that referenced the key (the doc scan should have
  been clean, but drift happens).

A dead key that breaks tests is **not** dead; the report is wrong, not
the code. The key is live; the skill that flagged it is the bug.

## Anti-Patterns

- **A "config GC" that auto-deletes.** Deletion is a mutating action;
  it requires approval. The skill proposes; the user approves; the
  user (or a separate workflow) executes.
- **A scan that ignores shadowed keys.** Two configs with the same
  name and different values is a bug-in-waiting. The report must call
  out the shadow; the user picks the winner.
- **A scan that conflates "dead" with "no recent reference."** A key
  with no recent reference is not dead; it may be deliberately stable
  (a default that has worked for years). Cite the last-touched date;
  let the user decide.
- **A scan that scans only code.** Docs are also references. A key
  that no code reads but a runbook documents is live.
- **A scan that scans only one config file.** Many projects have
  configs in 3-4 places (`.env`, `pyproject.toml`, `settings.py`,
  `docker-compose.yml`). Scan all of them or the report is incomplete.

## Related Skills

- `codebase-onboarding` - produces the initial config inventory.
- `living-docs-governance` - the doc drift sister.
- `setup-loop-engine` - the workflow that bootstraps the config tree.