# Loop Engineer Improvement Roadmap

**Status:** Active. The maintainer's bridge between research and code. Lives
in the LE app repo (this folder) because the LE app itself has no product
workspace to plan in (`AGENTS.md` #15).

This document is the maintainer's view: which rounds shipped, what the
E-patterns look like now, and which gaps remain. The per-round rationale is
## Round-by-round log

### Round 1 (initial)
Brought the loop-engineer chain to baseline. Fixed the chain's grill to
ask technical and non-technical questions during planning. Upgraded the
existing 39-skill baseline by adding the E1/E2 patterns (Pre-Report Gate +
Common False Positives) to the assurance skills.

### Round 2 — Three new skills + structural improvements
- **3 new skills:** `/dev-team` (4-persona parallel review, BMAD party-mode),
  `/dynamic-workflow` (task-local harness template), `/adr`
  (architecture decision records).
- **Cross-cutting:** AGENTS.md Senior Review Layers + Portable Commands
  table extensions. 7 new command rows.
- **Structural:** E1 + E2 added to `code-reviewer`, `qa-validation`,
  `data-engineering`, `security-compliance`, `ml-engineering` (8 of 8
  assurance skills now have both).

### Round 3 — Three more skills + role-level structure
- **3 new skills:** `/api-design` (REST/HTTP conventions),
  `/error-handling` (cross-stack error envelope), `/recursive-decision-ledger`
  (append-only revisit ledger).
- **Structural:** E4 (model tier) + E8 (handoffs) added to every role in
  `manifests/agents.json`. 23 roles, each with `model` and `hands_off_to`.

### Round 4 — Eleven skills + E3 strengthening
- **Onboarding + docs governance (4):** `codebase-onboarding`,
  `inherit-legacy-style`, `plan-orchestrate`, `living-docs-governance`.
- **Chain quality + safety (4):** `loop-design-check`, `contract-first`,
  `gateguard`, `strategic-compact`.
- **Agent orchestration trio (3):** `agent-sort`, `agent-eval`,
  `council-multi-model`.
- **E3 strengthening:** all 25 mutating skills got a `## Stop Conditions +
  Rollback` section with named stop signals and a non-trivial rollback
  paragraph.

### Round 5 — E7 + three small skills
- **E7 — Prompt Defense Baseline:** new `/safeguard` skill (single source of
  truth for the 6-bullet preamble). All 18 assurance-class skills got
  a `## Prompt Defense Baseline` section. The skill_audit enforces E7.
- **3 new skills:** `/config-gc` (config cleanup), `/skill-scout` (skill
  discovery), `/hookify-rules` (hook-to-rule conversion).

### Round 6 — Structural round
- **E7 on roles:** every role in `manifests/agents.json` got a
  `prompt_defense` field. Assurance roles embed the 6-bullet preamble;
  other roles reference the safeguard skill. Validator extended.
- **`/self-audit`:** new command + script that walks the LE app's
  own state and reports drift across 5 dimensions (skill policy,
  capabilities, profiles, agents, activation paths).
- **`/onboard`:** new command + `docs/LE_ONBOARDING.md` (60-minute
  contributor guide).

### Round 7 — Naming consistency
- **9 missing command files added:** `code-reviewer`, `qa-validation`,
  `security-compliance`, `data-engineering`, `ml-engineering`,
  `operations`, `tdd`, `council-multi-model`, `loop-design-check`.
- **3 pre-existing direct-invocation commands added:** `council`, `docs`,
  `feature-workflow`.
- **Command-name vs skill-name allowlist** (`COMMAND_TO_SKILL`):
  `adr` -> `architecture-decision-records`, `decision-ledger` ->
  `recursive-decision-ledger`, `dynamic-workflow` -> `dynamic-workflow-mode`.
- **DIRECT_INVOCATION_SKILLS set:** the audit now enforces that any
  direct-invocation skill has a matching `commands/<name>.md` file.
- **Retroactive AGENTS.md fix:** the rounds 2-7 Portable Commands table
  rows were missing from this folder (they had been written to a
  different path). They are now in the table.

### Round 8 — Discovery + 2 new skills
- **`/skill-list` + `scripts/skill_list.py`:** list every skill with
  class, owning capability, and activation paths. `--class` filter;
  `--json` for tooling.
- **`/roles` + `scripts/roles_list.py`:** list every role with class,
  model tier, `may_mutate`, skills, hand-off targets, and independence
  boundaries.
- **`/revise-skill`:** structured way to edit an existing skill's
  `SKILL.md`. Pre-edit checklist, edit, post-edit validation triad.
- **2 new skills:** `latency-critical-systems` (p99 budgets, hot-path
  profiling, batching, caching, regression detection);
  `market-research` (TAM/SAM/SOM, competitor analysis, positioning,
  kill criterion).
- **AGENTS.md Senior Review Layers** rewritten to surface the rounds
  2-7 skills (Planning / Build / Quality & safety / Release & chain
  maintenance).

### Round 9 — Alignment + E3 strict + 2 small skills (this round)
- **Command-template audit:** `scripts/command_audit.py` checks every
  `commands/*.md` for the canonical H2 sections (`## How To Interpret`,
  `## Required Reads`, `## Loop`, `## Output`). Legacy aliases
  (`## Purpose` and `## Process`) accepted as equivalent. 14 commands
  had missing sections; all are now fixed. The audit is wired into
  `/self-audit` so chain self-checks catch command-template gaps.
- **E3 strict:** the audit now requires explicit `## Stop Conditions`
  and `## Rollback` headings, not just the words anywhere in the body.
  Word-only is a `SKILL-SAFETY-005` (low) finding; missing headings is
  `SKILL-SAFETY-004` (high). All 25 mutating skills pass strict E3.
- **2 new skills:** `learn-curator` (runtime that promotes observations
  to `.loop/pending/learning-<fingerprint>.json` records; complements
  `continuous-learning-v2` which is documentation); `handoff` (the
  7-field HANDOFF.md discipline).
- **Tests added:** `test_command_audit.py` (3 tests),
  `test_mutating_skill_with_only_word_but_no_heading_fails_e3` (1 test).

### Round 10 — Implementation round (3 scripts + 4 commands + 1 skill)
- **3 new scripts closing the runtime half of existing skills:**
  - `scripts/living_docs_audit.py` — implements the
    `living-docs-governance` workflow (outdated-command, dead-link,
    wrong-version-pin, stale-generated-table).
  - `scripts/dev.py` — stack-agnostic runtime for `/lint`, `/test`,
    `/format`, `/commit` (reads `<workspace>/.loop/dev_config.json`).
  - `scripts/chain_bench.py` — implements the `chain-bench` workflow
    (skills, commands, roles, plan, tests, state metrics).
- **4 dev-experience commands:** `/lint`, `/test`, `/format`,
  `/commit` — stack-agnostic via the per-workspace dev config.
- **1 new skill (`chain-bench`):** measure the chain's own state
  over time, save the JSON under `benchmarks/<date>.json`,
  diff consecutive benchmarks.
- **`.loop/dev_config.json`** created in the LE app itself so
  `/lint` and `/test` can run on this repo.
- **8 new tests** in `test_r10_new_scripts.py`.
- **AGENTS.md and manifests:** 6 new Portable Commands rows;
  `chain-bench: read-only` registered; `foundation` capability
  gained 6 new commands and 2 new skills.
- **/self-audit** now also checks command-template compliance
  via `command_audit.py` as a subprocess.

### Round 11 — Runtime + discovery (E7 hook + grill + index + 1 skill)
- **Hook-side E7 enforcement:** `scripts/safeguard_hook.py` applies
  the 6-bullet Prompt Defense Baseline to every `PreToolUse`
  event. Six checks: role lock, secret leakage, executable
  output, unicode tricks, external untrusted content, harmful
  keywords. Sample wiring in `.claude/settings.json.example`.
- **`/grill` script:** runs the 66 questions across 11 categories
  in `skills/plan-loop/phases/grill.md` as a structured
  interview. Writes answers to `<workspace>/plan/GRILL_ANSWERS.md`.
- **`scripts/README.md` + `scripts/_INDEX.md`:** auto-generated
  index of all 101 non-test scripts, with one-line purpose
  extracted from the docstring. The script supports `--check`
  for CI.
- **1 new skill (`chain-catalog`):** render the full chain surface
  as one Markdown page (capabilities, skills, commands, roles,
  profiles, harnesses). The catalog is the single discoverable
  reference; `scripts/chain_catalog.py` is the runtime.
- **12 new tests** in `test_r11_new_scripts.py`.
- **AGENTS.md:** 1 new Portable Commands row (`/chain-catalog`).
- **`plan/CHAIN_CATALOG.md`** and `plan/GRILL_ANSWERS` added to the
  workspace-paths allowlist.

### Round 12 — The 6 remaining reference items (closed)
- **6 new skills, all 6 closing real gaps from the chain's round-by-round design process:**
  - `codehealth-mcp` — code-health snapshot (lint debt, test
    coverage, churn, dep freshness, doc coverage). JSON output
    consumed by `/release-check` as `release_blockers`.
  - `iterative-retrieval` — 3-round retrieval loop; each round
    refines the query from the prior round's results.
  - `competitive-platform-analysis` — direct / indirect /
    substitute competitor map with positioning statement.
  - `automation-audit-ops` — audit every automation the chain
    runs (CI, hooks, scripts, harnesses) for stale, unowned, or
    risky automations.
  - `parallel-execution-optimizer` — decide sequential vs
    parallel; emit a parallel plan with the dependency graph
    and the batches.
  - `dashboard-builder` — self-contained HTML dashboard from a
    YAML spec (no JS frameworks, no CDN).
- **4 new scripts:** `codehealth.py`, `iterative_retrieval.py`,
  `automation_audit.py`, `dashboard.py` (all deterministic,
  no LLM).
- **6 new commands** wired into `foundation` capability.
- **6 new tests** in `test_r12_new_scripts.py`.
- **E3 strict** extended: `dashboard-builder` got the required
  Stop Conditions + Rollback headings.
- **AGENTS.md:** 6 new Portable Commands rows.

### Round 13 — Structural polish (9 gaps closed)

- **2 new skills, 3 new scripts closing the last big gaps:**
  - `bench-history` — record and diff `/chain-bench` snapshots over
    time. Append to `benchmarks/<date>.json`; emit a trend delta
    against the prior snapshot. The single signal of "is the chain
    getting better or worse?"
  - `harness-catalog` — consolidate the 15 harness JSON files into
    a single discoverable view. Validates the expected fields and
    flags structural issues. Maintained at every release.
  - `scripts/bench_history.py` — append + diff + trend delta.
  - `scripts/harness_catalog.py` — build + validate + render.
  - `scripts/codehealth.py`, `scripts/iterative_retrieval.py`,
    `scripts/automation_audit.py`, `scripts/dashboard.py` —
    runtimes for the round-12 skills that had no scripts.
- **E7 hook-side enforcement** wired into the harness layer via
  `scripts/safeguard_hook.py` (round 11) and `harnesses/hooks.example.json`
  (per-stack sample configs for Claude, Cursor, Codex, generic).
- **Living-docs as PostToolUse hook** — the per-stack-hooks.json shows
  the PostToolUse pattern that auto-runs
  `scripts/living_docs_audit.py` after every docs/ edit.
- **CI workflow** — `.github/workflows/chain-ci.yml` runs
  `skill_audit`, `agent_registry`, `self_audit`, `command_audit --check`,
  the E7 hook smoke test, the unit test suite, and (on push to main)
  `bench_history --append` + `--diff` with the bench uploaded as an
  artifact.
- **Self-audit auto-invokes living_docs_audit** — the
  `_check_living_docs_drift` function runs the script as a subprocess
  and surfaces high/medium drift findings.
- **Compact-loop / strategic-compact deduped** — each skill now has
  a `## Related skills` block pointing at the other.
- **E5 Approval Criteria block** added to all 18 assurance skills.
  The three-outcome verdict (Approve / Warning / Block) is the chain's
  gate; the maintainer enforces it.
- **3 stub command files** (`compact`, `recursive-decision-ledger`,
  `grill`) created for legacy alias and doc references, with canonical
  H2 sections. (`startup-discovery-loop` was an existing alias and
  did not need a new command file.)
- **8 new tests** in `test_r12_new_scripts.py` (6) and the
  `bench_history` + `harness_catalog` coverage in
  `test_r11_new_scripts.py` (2 more).
- **AGENTS.md:** 6 new Portable Commands rows
  (bench-history, harness-catalog, compact,
  recursive-decision-ledger, grill).

### Round 14 — The 11 remaining roles

11 new agents and skills that close the remaining gaps from the
research:

- **8 code-quality roles (assurance class):**
  - `code-simplifier` — read-then-edit refactor that preserves
    behaviour; targets complexity, dead branches, unclear names.
  - `comment-analyzer` — verify comment accuracy and staleness
    (4 buckets: Inaccurate / Stale / Incomplete / Low-value).
  - `performance-optimizer` — algorithmic complexity + Web Vitals
    + bundle analysis; profile before/after, CI test.
  - `refactor-cleaner` — dead-code hunter (knip / depcheck /
    ts-prune); SAFE / CAREFUL / RISKY per category.
  - `type-design-analyzer` — score type design on 4 axes
    (Encapsulation / Invariant Expression / Usefulness /
    Enforcement).
  - `harness-optimizer` — eval-driven harness tuning via pass@k /
    pass^k; BLOCKED on security-sensitive diffs.
  - `pr-test-analyzer` — test quality not test count; Critical /
    Important / Nice-to-have gap buckets.
  - `conversation-analyzer` — mine session transcript for
    corrections, repeated mistakes, prompt-injection attempts;
    feeds `learn-curator` + `continuous-learning-v2`.
- **3 network roles (deploy-time):**
  - `network-architect` (planner) — design the network topology
    (subnets, firewall rules, DNS, load balancers, VPN/zero-trust,
    ingress, observability).
  - `network-troubleshooter` (executor) — read-only OSI-layer
    diagnosis; evidence-based root cause; narrow allow rules
    over disabling ACLs.
  - `network-config-reviewer` (assurance) — audit a running network
    device's config (Cisco IOS / IOS-XE / NX-OS / vendor CLI) for
    SSH v1, plaintext credentials, SNMP, NTP, AAA, Telnet, HTTP.
- **`prompt_defense` field** added to all 11 new roles (E7
  pattern). 8 assurance roles got the full 6-bullet preamble; the
  3 non-assurance roles got the 6-bullet reference.
- **11 new commands** wired into the `quality` (8 code-quality
  roles) and `delivery` (3 network roles) capabilities.
- **11 new tests** in `test_r14_new_roles.py` — frontmatter, E-pattern
  presence, command file existence, role class/model, prompt defense,
  independent_from, hands_off_to.
- **`spec-miner` is intentionally out of scope** — its job (brownfield
  OnSpec-style extraction) is covered by the `codebase-onboarding`
  skill from round 4.
- **The 3 network roles** were previously marked "out of scope" by
  the chain's round-by-round design process; round 14 corrects that — they are deploy-time
  responsibilities that the chain's runtime side (`operations`,
  `cicd-release`) does not cover.

## State of the chain after round 14


- **110 canonical skills** (was 39 at the start).
- **101 commands** (was 33).
- **34 roles** in `manifests/agents.json`, each with `model`,
  `hands_off_to`, and `prompt_defense` (E7).
- **732 tests pass.**
- **All three audits green:** `skill_audit.py` (per-skill contract),
  `agent_registry.py` (role + E7 + strict E3), `self_audit.py`
  (manifests + activation paths + command-template + E7 hook + living-docs drift).

## Cross-cutting E-patterns (the chain's structural design rules)

| E-pattern | Status | Where enforced |
|---|---|---|
| E1 — Common False Positives list on assurance skills | done | each assurance skill body + `skill_audit.py` (implicit) |
| E2 — Pre-Report Gate (4-question) | done | each assurance skill body |
| E3 — Stop Conditions + Rollback | **strict** (round 9) | `## Stop Conditions` and `## Rollback` headings are required on every mutating skill |
| E4 — Model tier per role | done | `model` field on every role |
| E5 — Approval Criteria block | partial | implicit in each assurance skill's output format |
| E6 — Fixed output format with severity tags | done | `[CRITICAL] / File / Issue / Fix` template used in code-reviewer, security-compliance, etc. |
| E7 — Prompt Defense Baseline | done | `safeguard` skill + `prompt_defense` field on every role + audit enforcement |
| E8 — Explicit handoffs between roles | done | `hands_off_to` on every role |

## Gaps still open (for future rounds)

- **Per-stack reviewers** (`ts-reviewer`, `py-reviewer`, etc.) — LE
  is stack-agnostic by design; `code-reviewer` composes with per-stack
  expertise on demand.
- **Vertical-specific skills** (healthcare / defi / finance) — out
  of LE's scope per `AGENTS.md` #6.
- **Remaining reference items from the chain's design process** (`codehealth-mcp`,
  `iterative-retrieval`, `competitive-platform-analysis`,
  `automation-audit-ops`, `parallel-execution-optimizer`,
  `dashboard-builder`) — adoptable on demand via `/skill-scout`.
- **Hook-side E7 enforcement** — the harness's `PreToolUse` and
  `PostToolUse` hooks can apply the baseline; the runtime script
  is not yet written. The skill layer is in place; the harness
  layer is the next step.

## Out of scope

- The LE app's own product workspace — LE has no product; this doc
  lives in the app repo by design.
- Per-coding-agent adapter content (`CLAUDE.md`, `CURSOR.md`, ...) —
  these are tool-specific shims, not canonical.
- The `loop` shell binary — updated via `loop update`, not by hand.
