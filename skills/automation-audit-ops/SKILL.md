---
name: automation-audit-ops
description: Run an audit of every automation the chain runs (CI workflows, scheduled jobs, hooks, scripts) to surface dead automations, missing alerts, or unowned configurations. Use during a chain release, after adding a new hook, or as a periodic maintenance signal.
---

# Automation Audit Ops

Inherits `docs/SKILL_CONTRACT.md`.

A small, deterministic discipline for auditing the automations the
chain runs. The chain has scripts, hooks, scheduled jobs, CI
workflows, and external integrations. Over time, automations go stale
(their owner leaves, the upstream API changes, the script breaks
silently). The audit surfaces dead, broken, or unowned automations.

## When to use

- During a chain release, as part of the release-readiness check.
- After adding a new hook or scheduled job, to make sure the change
  is consistent with the rest.
- As a periodic maintenance signal: monthly or quarterly.
- When a CI failure is mysterious: the audit surfaces the
  automations that might be related.

## When NOT to use

| Instead of this skill | Use |
|---|---|
| A code review | `code-reviewer` |
| A security review | `security-compliance` |
| A performance review | `latency-critical-systems` |
| A docs review | `living-docs-governance` |

## What the Audit Walks

| Source | What it checks |
|---|---|
| `.claude/settings.json*` and equivalents | registered hooks; matched scripts exist |
| `harnesses/*.json` | trust + invocation fields consistent with the LE app |
| `scripts/` | every script has a matching test; deprecated scripts removed |
| `manifests/install_profiles.json` | every capability in a profile has a positive context budget |
| `manifests/capabilities.json` | every command in a capability is reachable from at least one activation source |
| `manifests/agents.json` | every role has `model` and `hands_off_to`; assurance roles are independent from builders |
| `docs/UPGRADE.md` and similar | upgrade paths reference current code, not deprecated scripts |
| `templates/` | all templates are referenced by at least one command or skill |
| GitHub Actions / `.github/workflows/` | all referenced scripts exist; all secrets are declared |

## Workflow

### 1. Run the audit

```bash
python scripts/automation_audit.py --root <le-app> --out plan/AUTOMATION_AUDIT.md
```

The script walks the sources above and emits a Markdown report.

### 2. Triage the report

The report's structure is:

- **Healthy** — automations that pass every check.
- **Stale** — automations that reference a non-existent file or skill.
- **Unowned** — automations with no clear owner; the chain cannot
  reach the owner on a failure.
- **Risky** — automations that depend on a secret or external API
  that has rotated or expired.

The report is a list, not a verdict. The maintainer triages.

### 3. Take action

- **Stale** — remove the stale automation, or fix the reference.
- **Unowned** — assign an owner; the next round of the audit will
  expect a `owner: <name>` field.
- **Risky** — rotate the secret, update the API version, or add a
  fallback.

## Output

A single Markdown report with the four categories and a per-automation
list. The chain does not auto-fix; the audit is read-only.

## Anti-Patterns

- **An audit that becomes a chore.** The audit is a signal, not a
  habit. A monthly audit is fine; a daily audit is noise.
- **An audit that flags everything.** A report with 100 findings
  is a report that gets ignored. The audit is severe on the
  most-impactful items, light on the rest.
- **An audit that hides the owner.** "Stale" is a fact; "who owns
  it" is a fact. Both belong in the report.
- **An audit that runs without a fix path.** The report must
  name the fix for each finding, not just the finding.

## Related Skills

- `code-reviewer` - the per-PR review; the audit is the whole-project
  view.
- `release-check` - the consumer of the audit; treats
  stale or unowned automations as release blockers.
- `living-docs-governance` - the docs side of the audit; this skill
  is the automation side.