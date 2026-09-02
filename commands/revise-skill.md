# /revise-skill

Revise an existing skill's `SKILL.md` safely. The skill audit enforces
`docs/SKILL_CONTRACT.md` and the policy class rules; this command makes the
edit-followed-by-validate cycle explicit. Use when the user wants to refine
an existing skill without going through `/skill-scout` to find one and the
audit pattern to verify the result.

## How To Interpret

If the user says `/revise-skill`, `edit the X skill`, `refine the X skill`,
`update X's SKILL.md`, or asks to revise an existing skill, execute this
file directly.

## Required Reads

1. `AGENTS.md`
2. `docs/SKILL_CONTRACT.md` (the canonical contract every skill inherits)
3. `docs/LE_ONBOARDING.md` (the contributor guide)
4. the target `skills/<name>/SKILL.md`
5. the current `manifests/skill_policy.json` and `capabilities.json` entries
6. the activation sources for the skill (`python scripts/skill_list.py`)

## Loop

```text
IDENTIFY target skill -> READ existing SKILL.md + the contract -> STATE the revision in one sentence -> EDIT -> RUN audit (skill_audit, agent_registry, self_audit) -> RUN tests -> COMMIT minimal diff
```

## Pre-Edit Checklist

Before editing, confirm:

- The change is within the skill's class (`read-only` / `stateful` /
  `mutating` / `assurance`).
- The change does not violate the SKILL_CONTRACT.
- The change is a minimal diff, not a drive-by refactor.
- The change is recorded in the skill's `### Change log` block at the
  bottom of the file (date, change, reason).

If any of these is unclear, ask the user before editing.

## Edit

Open the skill's `SKILL.md` in the editor of choice. Use the existing
section structure: `# Purpose`, `# Read First`, `# Workflow`, `# Output`,
`# Anti-Patterns`, `# Related Skills`. Add the new section in the
right place; do not reorder existing sections unless the change requires
it.

If the change is non-trivial (new class, new activation path, new command),
update the manifests **in the same commit**:

- `manifests/skill_policy.json` — if the class is changing.
- `manifests/capabilities.json` — if the owning capability is changing.
- `commands/<name>.md` — if a public command is being added or removed.
- `AGENTS.md` — if the new command goes in the Portable Commands table.
- The new role's `manifests/agents.json` entry — if a new role claims
  this skill.

## Post-Edit Validation

Run the three audits in order:

```bash
python scripts/skill_audit.py      # SKILL-CONTRACT + ownership checks
python scripts/agent_registry.py   # role + independence + E7 checks
python scripts/self_audit.py       # manifest vs on-disk consistency
```

Then run the test suite:

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

If any audit or test fails, the change is incomplete. Address the
failure before committing.

## Commit

Single commit, single skill, minimal diff. The commit message names the
skill and the rationale:

```
revise(<skill>): <one-line summary>

<reason for the change, citing the trigger: user request / audit finding
/ sibling skill change / external reference>
```

## Anti-Patterns

- **A revision that quietly changes the skill's class.** Class change
  is a manifest change; the revision must update the policy and the
  audit must re-validate.
- **A revision that adds E1 / E2 / E3 / E7 sections only to match the
  other skills without checking that the section's content applies.**
  Style uniformity is the goal; content correctness is the goal too.
- **A revision that touches other skills' files.** Each revision is one
  skill; cross-skill changes are a different commit.
- **A revision that bypasses the audit.** "It's a small change" is the
  most common reason revisions break the chain. The audit is small and
  fast; run it.

## Related Skills

- `skill-scout` - the pre-creation scout; this command is for editing
  existing skills, not creating new ones.
- `safeguard` - the prompt-level defence; revisions to user-input-
  processing skills should re-apply the baseline.
- `codebase-design` - the seam vocabulary; revisions that touch
  interfaces should re-cite it.

## Output

1. The revised `SKILL.md` (single file)
2. The audit triad result (`skill_audit`, `agent_registry`, `self_audit`)
3. The test suite result
4. The commit message (single skill, minimal diff)

## Continuation

After `/revise-skill`, the chain continues with the next action. The revised skill is loaded by the next command that references it.
