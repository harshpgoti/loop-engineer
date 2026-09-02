# /harness-catalog

Consolidate the per-coding-agent harness JSON files (Claude, Cursor, Codex, etc.)
into a single discoverable view. Surface the trust level, invocation path, and
skill/command paths for each harness. Use when adopting a new coding agent,
when a harness breaks, or as a periodic maintainer signal.

## How To Interpret

If the user says `/harness-catalog`, `harness inventory`, `what harnesses are
supported`, `harness health`, or asks for a per-harness overview, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `skills/harness-catalog/SKILL.md`
3. `scripts/harness_catalog.py`
4. `harnesses/*.json` (the source data)

## Loop

```text
WALK harnesses/*.json -> VALIDATE each (trust, invocation, paths) -> EMIT a single Markdown page
```

## Script

```bash
python scripts/harness_catalog.py --root <le-app>
python scripts/harness_catalog.py --root <le-app> --out docs/HARNESS_CATALOG.md
```

## Output

A single Markdown page with one row per harness. Structural issues
(missing trust level, broken paths) are surfaced as a "## Issues"
section at the bottom.

## Continuation

The catalog is the maintainer view; the maintainer triages the issues.
A clean catalog is committed at every release.