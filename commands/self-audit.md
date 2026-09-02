# /self-audit

Walk the Loop Engineer chain's own state: skill-policy vs capabilities consistency,
command/skill reachability, harness compatibility, install-profile budget, role
manifest consistency. Use before a release of the LE app, as a periodic
maintenance check, or when adding a new skill/command/role.

## How To Interpret

If the user says `/self-audit`, `audit the chain`, `check the LE app`, `is the
chain consistent`, or asks whether the four manifests agree with the on-disk
inventory, execute this file directly.

## Required Reads

1. `AGENTS.md`
2. `manifests/skill_policy.json`
3. `manifests/capabilities.json`
4. `manifests/agents.json`
5. `manifests/install_profiles.json`
6. the on-disk `skills/`, `commands/`, `harnesses/` directories

## Loop

```text
LOAD manifests -> WALK inventory -> CHECK drift across 4 dimensions -> EMIT report
```

## Script

```bash
python scripts/self_audit.py
```

Optionally emit JSON for tooling:

```bash
python scripts/self_audit.py --json
```

## Output

A Markdown report. Drift is reported as a list of bullet points under
`## Findings`. Zero findings is success; non-zero means at least one of the
manifests and the on-disk inventory disagree.

Drift categories checked:

1. **Skill policy** - every on-disk `skills/<name>/SKILL.md` has a class
   assignment in `manifests/skill_policy.json`; every assignment refers
   to a real skill.
2. **Capabilities** - every command and skill listed in a capability
   exists on disk; no command or skill has multiple owners; no on-disk
   command or skill is unowned.
3. **Profiles** - every install profile fits its `context_budget` after
   the capability closure.
4. **Agents** - every role's `skills` exist; every role's
   `independent_from` and `hands_off_to` reference real role ids.
5. **Activation paths** - every skill and command has at least one
   activation source (AGENTS.md, a command, another skill, or a phase
   file). Surfaced as counts; the full audit is `scripts/skill_audit.py`.

## Continuation

Zero findings → the chain is consistent; ship the next release.
Non-zero findings → the chain has drift; address each finding before
shipping. Drift that is intentional (a skill is being staged) is recorded
as a doubt in `DOUBTS.md` (per the product convention; this script runs
in the LE app, not the product, so doubts are recorded in
`docs/LE_DRIFTS.md` instead).
