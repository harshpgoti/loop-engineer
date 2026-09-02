---
name: chain-meta
description: Read-only surface for the Loop Engineer chain's own state — roles, skill list, and self-audit. Composes `/roles`, `/skill-list`, and `/self-audit` so meta-inquiries about the chain have one routing layer (`scripts/roles_list.py`, `scripts/skill_list.py`, `scripts/self_audit.py`).
class: read-only
capability: chain-meta
activation:
  - /roles
  - /skill-list
  - /self-audit
owner: chain-meta
---

Inherits `docs/SKILL_CONTRACT.md`. Risk and approval: this skill is
read-only; it never mutates the chain. Use it as a preflight check before
release, before any chain edit, or as periodic maintenance. Mutation belongs
in `/revise-skill` or `/upgrade-loop-engineer`.

# Purpose

`chain-meta` is the read-only introspection layer for the Loop Engineer chain
itself. The three commands it composes answer "who is in the chain", "what
skills does the chain have", and "is the chain consistent". All three read
manifests (`manifests/agents.json`, `manifests/skill_policy.json`,
`manifests/capabilities.json`, `manifests/install_profiles.json`) and emit a
report; none of them mutate the chain.

# Read First

- `AGENTS.md`
- `manifests/agents.json`
- `manifests/skill_policy.json`
- `manifests/capabilities.json`
- `manifests/install_profiles.json`

# Workflow

1. **Pick the right meta-script.** `roles_list.py` for the role matrix,
   `skill_list.py` for the skill surface, `self_audit.py` for cross-manifest
   drift.
2. **Load the relevant manifest(s).** Every meta-script validates JSON on load.
3. **Filter (optional).** `--class assurance`, `--json`, etc. are honoured per
   the command's documented flags.
4. **Emit.** Markdown for humans, JSON for tooling. The chain never mutates from
   these commands — they are observability surfaces.

# Output

- `/roles`: a Markdown or JSON table of roles with class, model tier, skills,
  hand-off targets, and independence boundaries.
- `/skill-list`: a Markdown or JSON table of skills with class, owning
  capability, and activation sources.
- `/self-audit`: a Markdown report of drift across the four manifests vs the
  on-disk inventory; zero findings means the chain is consistent.

# Anti-Patterns

- **Mutating from a meta-command.** None of `/roles`, `/skill-list`, or
  `/self-audit` writes to disk; mutation belongs in `/revise-skill` or
  `/upgrade-loop-engineer`.
- **Drift that is intentional.** Record it as a doubt in `DOUBTS.md` (per the
  product convention); record it in the chain's release notes when running
  against the LE app's own state.
- **Splitting `chain-meta` into three skills.** Each member is a one-screen
  report; the value is in the unified introspection surface.

# Related Skills

- `agent-builder` (when a meta-report triggers a role or capability change)
- `revise-skill` (when a meta-report triggers a skill change)
- `doctor` (runtime health check, different scope)