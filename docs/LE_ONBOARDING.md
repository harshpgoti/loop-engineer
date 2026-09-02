# Loop Engineer — Contributor Onboarding

A new contributor's first 60 minutes. Read this before you touch anything.

Loop Engineer (LE) is a chain-of-skills runtime that helps any user plan,
validate, build, test, secure, document, and deploy a software product. The
chain runs as a chain: a single command (`/plan-loop`, `/develop-product`,
`/loop-engine`) cascades through phases until it reaches a terminus or a
named Stop Condition. You are reading this because you are about to add to
that chain.

## The One Rule

> **Read `AGENTS.md` first.** Read it **every** session. It is the chain's
> universal operating rules. Its 16 non-negotiables apply to every command,
> every skill, and every contribution.

After `AGENTS.md`, read `docs/SKILL_CONTRACT.md`. Every canonical skill
inherits this contract; deterministic validators (`scripts/skill_audit.py`)
enforce the link. New skills that do not reference it will fail the audit.

## The Map (60-Second Tour)

```
loop-engineer/
  AGENTS.md                  # 16 non-negotiables. Read first.
  CLAUDE.md / CURSOR.md /    # Per-coding-agent adapters. Do not put
    CODEX.md / ...            # canonical logic here.
  commands/                  # Public slash commands (one per skill).
  skills/                    # Reusable instruction packages.
    <name>/SKILL.md
    <name>/phases/...        # Per-phase files for skills with phases.
  scripts/                   # Deterministic runtime (~140 Python files).
  manifests/                 # The 4 manifests. Source of truth.
    skill_policy.json
    capabilities.json
    agents.json
    install_profiles.json
  harnesses/                 # Per-coding-agent adapters (Claude, Cursor, ...).
  templates/                 # Scaffolds for product-state files.
  evals/                     # Plan-quality + dev-quality scoring.
  docs/                      # Design + architecture + lifecycle docs.
  tools/registry.md          # External capability references.
```

## What Not To Touch

- **`AGENTS.md` non-negotiables** (1–16) — these are the chain's
  contract. Changing them is a deliberate, reviewed decision; do not
  edit casually.
- **The 4 manifests' structure** — `skill_policy.json` adds new
  assignments as `name: class`; `capabilities.json` declares
  capabilities with `requires`/`context_cost`; `agents.json` declares
  roles with `class`/`may_mutate`/`independent_from`; `install_profiles.json`
  declares profiles with `capabilities`/`context_budget`. Renaming
  these fields breaks the chain.
- **Per-coding-agent adapter files** (`CLAUDE.md`, `CURSOR.md`, `CODEX.md`,
  `OPENCODE.md`, `GROK.md`, `PI.md`, `CLINE.md`) — these are thin
  tool-specific shims, not the canonical logic.
- **Anything in the `loop` shell binary** — that is the runtime bridge
  and is updated via `loop update`, not by hand.

## How to Add a Skill (the most common contribution)

A new skill is the chain's primary extension surface. The pattern:

1. **Scout first.** Run `/skill-scout` to confirm the need is not
   already covered by an existing skill (local pack, then GitHub, then
   web).
2. **Pick the class.** `read-only` (no mutation), `stateful` (writes
   product state), `mutating` (changes code/config; requires rollback
   and approval), `assurance` (evidence-backed findings; never self-approves).
3. **Write `skills/<name>/SKILL.md`.** First line: frontmatter with
   `name:` and `description:` (one-line activator). Second: heading
   `# <Title>`. Third: `Inherits \`docs/SKILL_CONTRACT.md\`.`
4. **Use the canonical sections.** `# Purpose`, `# Read First`, `# Workflow`,
   `# Output`. Add E-pattern sections as needed (Pre-Report Gate, Common
   False Positives, Stop Conditions, Rollback, Prompt Defense Baseline).
5. **Write `commands/<name>.md`.** Mirror the skill's structure.
6. **Register in `manifests/skill_policy.json`** under `assignments` as
   `"<name>": "<class>"`.
7. **Add to a capability** in `manifests/capabilities.json`. Find the
   closest existing capability; add the skill name to its `skills`
   list and the command name to its `commands` list. Do not create a new
   capability unless the new skill belongs to none of the existing
   ten.
8. **Add a row to the Portable Commands table** in `AGENTS.md`.
9. **Run `python scripts/skill_audit.py`** — it must report `Skill audit OK`.
10. **Run `python scripts/self_audit.py`** — it must report zero findings.
11. **Run `python -m unittest discover -s scripts -p "test_*.py"`** —
    add a test for the new skill's behaviour.

A skill that is added without these eleven steps is a skill that is
broken in some way the chain will discover later.

## How to Add a Role (less common)

A new role is the chain's responsibility matrix. Adding a role is a
bigger decision than adding a skill; a role appears in `manifests/agents.json`
and is referenced from other roles' `independent_from` and `hands_off_to`.

1. **Define the responsibility** — what does this role do that no
   existing role does? If a skill covers it, add the skill to an
   existing role's `skills` list instead.
2. **Pick the class** — `planner`, `executor`, `assurance`, `controller`.
3. **Set `may_mutate`** — `true` for planner/executor/controller that
   write, `false` for assurance.
4. **Set `independent_from`** — assurance roles must list every
   executor/builder they should not approve. This is the
   `autoreview` enforcement.
5. **Set `model`** — `opus` for heavy reasoning, `sonnet` for default,
   `haiku` for cheapest. Default per class is in the manifest's
   `schema_notes`.
6. **Set `hands_off_to`** — the role ids this role escalates to.
7. **Set `prompt_defense`** — the E7 Prompt Defense Baseline. Assurance
   roles embed the 6-bullet preamble; other roles reference
   `skills/safeguard/SKILL.md`.
8. **Run `python scripts/agent_registry.py`** — it must report
   `Agent registry OK`.
9. **Add the role's skills/commands to the relevant capabilities** in
   `manifests/capabilities.json` if not already present.
10. **Run `python scripts/self_audit.py`** — zero findings.

## How to Add a Capability (rare)

Capabilities are the chain's planning units. Most new skills fit an
existing capability. A new capability is justified when:

- the new skill belongs to none of the existing ten;
- the new capability's `context_cost` justifies its own profile
  bucket;
- the new capability's `requires` dependency chain is well-defined.

A capability addition updates `manifests/capabilities.json` and possibly
`manifests/install_profiles.json`. Run `python scripts/capabilities.py`
to validate.

## The 16 Non-Negotiables (Recap)

From `AGENTS.md`:

1. **Memory first** - read `DOUBTS.md`, `plan/main_plan.md`, `TASKS.yml`,
   `GATES.yml`, `HANDOFF.md` first.
2. **First-run initialization** - if `plan/main_plan.md` is
   `UNINITIALIZED`, `/plan-loop` initializes it.
3. **Evidence gate** - product/architecture decisions need an
   `EVIDENCE_LOG.md` entry.
4. **Rules first, AI second** - deterministic parsers, validators, and
   rules before LLM calls.
5. **Human approval** - high-risk external actions need explicit
   approval.
6. **Sensitive data safety** - no secrets, regulated data, or customer
   PII in logs, fixtures, screenshots, or prompts.
7. **Tenant isolation** - multi-tenant queries are server-scoped and
   tested.
8. **Idempotent workflows** - safe retries; audit important transitions.
9. **Minimal diffs** - match existing conventions; no drive-by refactors.
10. **Tests required** - no task marked done without relevant tests.
11. **Handoff required** - update `memories/MEMORY.md`, `DOUBTS.md`,
    `HANDOFF.md` before ending session.
12. **Always-on lifecycle** - `loop session-start` / `loop session-end`.
13. **Run to terminus, not to chunk** - cascade through phases; never
    end a turn telling the user to run the next command.
14. **Skills are the public interface** - the `loop` shell is internal.
15. **Scope before writing** - resolve the sub-product before reading
    or writing.
16. **One workspace** - sub-products are scopes; no second workspace.

If a contribution violates one of these, the contribution is wrong,
not the rule.

## The Five-Phase Contribution Loop

When you add a new skill, command, role, or capability:

```text
RESEARCH  -> Scout for existing coverage (/skill-scout)
DESIGN    -> Pick the class, scope, and reach
WRITE     -> The skill, command, manifest entries
VALIDATE  -> skill_audit, agent_registry, self_audit
TEST      -> Unit + integration test
COMMIT    -> Minimal diff; cite the rationale
```

The loop is the same whether the contribution is a 5-line fix or a
500-line skill.

## Common First-Contribution Tasks

- **Add a Pre-Report Gate** to an assurance skill that lacks one.
  Pattern is in `skills/code-reviewer/SKILL.md`.
- **Add Common False Positives** to an assurance skill that lacks them.
  Pattern is in `skills/security-compliance/SKILL.md`.
- **Add Stop Conditions + Rollback** to a mutating skill that lacks them.
  Pattern is in `skills/develop-product/SKILL.md`.
- **Add the Prompt Defense Baseline** to a skill that lacks it. Pattern
  is in `skills/safeguard/SKILL.md`.
- **Add a missing test** for an existing skill's behaviour.
- **Replace a verbose description with a one-line activator** that the
  router can match.

If a contribution does not fit any of these, ask in `HANDOFF.md` first
before writing.

## Where to Get Help

- **`/doctor`** - run the runtime doctor; the chain's runtime health.
- **`/self-audit`** - run the chain's self-audit; the manifests vs the
  on-disk inventory.

- **`docs/LE_ROADMAP.md`** - the per-round improvement roadmap.
- **`docs/SKILL_CONTRACT.md`** - the canonical contract every skill
  inherits.
- **`AGENTS.md` Senior Review Layers** - which skill to read before
  which kind of work.

## What to Do on Your First Day

1. Read `AGENTS.md` end-to-end.
2. Read `docs/SKILL_CONTRACT.md` end-to-end.
3. Skim `docs/LE_ROADMAP.md` to see what has been done.
4. Run `python scripts/doctor.py` (or `/doctor` from a coding agent) and
   confirm the chain is healthy.
5. Run `python scripts/self_audit.py` and confirm zero findings.
6. Run `python -m unittest discover -s scripts -p "test_*.py"` and
   confirm all tests pass.
7. Open `commands/plan-loop.md` and read the whole file. Then
   `commands/develop-product.md`. Then `commands/loop-engine.md`. You
   now understand the chain.
8. Open `manifests/agents.json` and read the 23 roles. You now
   understand the responsibility matrix.
9. Pick a small contribution from "Common First-Contribution Tasks"
   above. Ship it. Get a review. Repeat.
