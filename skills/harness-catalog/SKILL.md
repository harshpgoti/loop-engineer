---
name: harness-catalog
description: Consolidate the per-coding-agent harness JSON files (Claude, Cursor, Codex, etc.) into a single discoverable view. Surface the trust level, invocation path, and skill/command paths for each harness. Use when adopting a new coding agent, when a harness breaks, or as a periodic maintainer signal.
---

# Harness Catalog

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for keeping the harness layer of
the chain discoverable. The chain has 15 harness JSON files in
`harnesses/`, each declaring a coding agent's trust level and
invocation path. Over time, the harnesses drift (a new agent
version, a renamed skill path); the catalog surfaces the drift.

## When to use

- Adopting a new coding agent: read the catalog to see what the
  chain already supports.
- A harness breaks: the catalog tells you which fields the chain
  expects and what to verify.
- A maintainer signal: the catalog is the inventory of the chain's
  per-agent surface.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A single harness's contents | read `harnesses/<name>.json` |
| A coding-agent-specific behavior | the harness's own docs |
| A chain self-check | `self_audit` |

## Workflow

### 1. Read the catalog

```bash
python scripts/harness_catalog.py --root <le-app>
```

The script walks `harnesses/*.json` (excluding `worker_versions.json`)
and emits a Markdown table with one row per harness: name, trust
level, invocation path, skill paths, command paths.

### 2. Validate

A harness is "valid" if:

- `name` matches the filename stem.
- `trust` is one of `project-trust` / `user-trust` / `untrusted` (the
  three known levels).
- `invocation` is a non-empty string (e.g. `/command`).
- `skill_paths.user` and `skill_paths.project` are paths that exist
  on disk.
- `commands_paths.user` and `commands_paths.project` (when present)
  are paths that exist on disk.

A harness that fails any check is flagged with a remediation
hint.

### 3. Diff over time

The catalog output is a single Markdown page. Save the page under
`docs/HARNESS_CATALOG.md` at every release. Diff consecutive pages to
see what changed.

## Output

A single Markdown page:

```markdown
# Harness Catalog

| Harness | Trust | Invocation | Skill paths | Command paths | Status |
|---------|-------|------------|--------------|----------------|--------|
| claude | project-trust | /command | user + project | user + project | OK |
| cursor | project-trust | /command | user + project | user + project | OK |
| ... |
```

## Anti-Patterns

- **A catalog that hides the trust level.** The trust level is the
  most important field; it must be visible in every row.
- **A catalog that never updates.** A catalog from 6 months ago is
  misleading; the chain ships new harnesses regularly.
- **A catalog that flags every minor issue.** A report with 20
  findings is one that gets ignored. The catalog surfaces structural
  issues (missing file, broken trust level), not cosmetic ones.

## Related Skills

- `self_audit` - the chain's self-check; the catalog is a separate
  per-harness view.
- `chain-catalog` - the chain's full surface; this skill is the
  per-harness subset.
- `safeguard` - the prompt-level defence; the harness's
  `PreToolUse` hook can apply the baseline.