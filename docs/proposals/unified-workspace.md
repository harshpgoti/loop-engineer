# Proposal: One Workspace, Many Product Scopes

**Status:** **implemented** (P0-P3). The shipped behaviour is documented in
[`../SCOPES.md`](../SCOPES.md); this file is kept as the design record and the rationale
behind each decision.

| Phase | State |
|---|---|
| P0 scope model, resolution, union loaders | done - `scripts/scope_paths.py`, `scripts/scope_state.py` |
| P1 absorb / eject / discover | done - `scripts/scope_absorb.py` |
| P2 contracts and the deterministic checks | done - `scripts/contracts.py` |
| P3 command surface, manifest, doctor | done - `commands/scope.md`, `skills/scope/SKILL.md`, `loop scope`, `## Scope` in the manifest |
| P4 narrow the federated bridge to external scopes only | done - gated on a real three-sub-product platform absorbed and ejected cleanly first. The bridge now runs only where a second workspace exists; `bridge_state()` in `scripts/scope_paths.py` is the seam |
**Would supersede if accepted:** the delegating half of `docs/PRODUCT_HIERARCHY.md`.

**Decisions taken (2026-08-24):** scope folders are named `plan/products/<slug>/` with no
numeric prefix; gates stay per scope; external repos stay federated; the code directory
per scope is the **user's choice, settled during that scope's planning**; and every
command is run **from the main folder** - the user names the scope in the command text
(`/plan-loop start working on auth product`), never by `cd`.

## 1. The problem, stated from the code

Today a sub-product is a **folder with its own `.loop-engineer/`**. Resolution is
nearest-wins (`workspace_resolver.find_local_workspace`), so standing in `auth-svc/`
you are in a different workspace with a different `plan/`, `TASKS.yml`, `GATES.yml`,
`DECISIONS.md`, `DOUBTS.md`, `memories/` and `state.db` from the main product.

Everything that makes the two agree is therefore a **boundary bridge**:

| Module | Lines | Exists only because of the boundary |
|---|---|---|
| `hierarchy_drift.py` | 786 | compare two plans that cannot see each other |
| `workspace_tree.py` | 493 | discover / link / stamp the other side |
| `parent_inbox.py` | 310 | recompute the parent's findings from the child's side |
| `subproducts_report.py` | 307 | roll children up into a generated file |
| `parent_watermark.py` | 285 | remember which parent state this child has seen |
| `hierarchy_sync.py` | 266 | write policy across the boundary |
| `parent_context.py` | 224 | copy inherited constraints into the child |
| `tree_sync.py` | 174 | run the above from either end |
| `finding_log.py` | 139 | remember answers to cross-boundary disagreements |
| **total** | **~2,980** | plus ~1,600 lines of tests |

Three costs fall out, and they are exactly the three named in the request:

1. **Main to sub** is a *copy* (`plan/PARENT_CONTEXT.md`), which is why the watermark,
   the drift levels, and the `parent-added` / `parent-changed` / `parent-removed`
   family all had to exist.
2. **Sub to main** is a *derived report* (`plan/SUBPRODUCTS.md`) - the main product can
   summarise a child but cannot depend on it. There is no cross-workspace `blocked_by`.
3. **Sub to sub** has no channel at all. `auth` being consumed by `portal` is expressed
   as a `contract-gap` **finding** - a complaint that two plans disagree - because a
   real declaration cannot cross two boundaries. `docs/PRODUCT_HIERARCHY.md` already
   records that the first version of that check was reading back its own output.

This proposal removes the boundary for sub-products that live in the same tree, and
keeps it only for the case that genuinely needs it: another repo, another team.

## 2. Target layout

```text
main-product/
├── .loop-engineer/                  # THE workspace - the only one
│   ├── plan/
│   │   ├── main_plan.md             # master plan (platform level)
│   │   ├── PRODUCT_MAP.md           # one row per scope - unchanged as the registry
│   │   ├── contracts/               # NEW - cross-scope interfaces (sub <-> sub)
│   │   │   └── auth.session-v1.yml
│   │   └── products/                # NEW - one folder per product scope
│   │       ├── auth/
│   │       │   ├── scope.json       # identity + code_dir + contracts (the binding key)
│   │       │   ├── overview.md prd.md architecture.md data-model.md
│   │       │   ├── integrations.md risks.md acceptance.md   # today's ultraplan pack
│   │       │   ├── steps/           # this scope's own step plans
│   │       │   ├── features/        # this scope's feature specs (001-, 002-)
│   │       │   ├── TASKS.yml        # this scope's tickets
│   │       │   ├── GATES.yml
│   │       │   └── DOUBTS.md
│   │       └── portal/ ...
│   ├── TASKS.yml GATES.yml DOUBTS.md DECISIONS.md   # platform-level, shared
│   ├── memories/  state.db  .loop/
├── services/auth/                   # the scope's CODE - no .loop-engineer here
│   └── .loop-scope                  # optional convenience pointer: auth
└── apps/portal/
    └── .loop-scope
```

The scope folder **is** today's `plan/steps/NN-slug/` ultraplan pack, moved under
`plan/products/` and given the build-state files it never had. That is deliberate:
this does not add a second hierarchy beside ultraplan, it finishes the one that
already exists. `docs/ULTRAPLAN.md` already says every map row gets a pack *inside the
main workspace*; today only rows typed `sub-product` are then torn out into a folder
of their own. This proposal deletes the tearing-out step.

**The folder name is deliberately not the binding key.** Today it is - `map_id_for()`
binds a sub-product by slug-equality of folder name to row title, which is exactly why
`docs/PRODUCT_HIERARCHY.md` has to warn that retitling a row silently unbinds it and
leaves the row "unbuilt while looking built". Plain `plan/products/auth/` only stays safe
if that rule is dropped, so it is:

- `scope.json` carries `"map_id": "01"` - **that** is the binding, written once at
  creation and never inferred.
- `PRODUCT_MAP.md` gains a `Scope` column naming the folder, the same explicit binding
  the `Workspace` column provides today.
- Retitling a row changes nothing. Renaming the folder becomes `loop scope rename`,
  which rewrites both ends together.
- `map_id_for()`'s slug-matching survives only as a *fallback for unbound legacy
  folders*, and reports what it guessed instead of binding silently.

This is a strict improvement over the numeric-prefix option: a prefix protects the
binding against retitling, but explicit IDs protect it against retitling *and* re-slugging
*and* folder moves.

## 3. The one new concept: a scope

```json
// plan/products/auth/scope.json
{
  "slug": "auth",
  "map_id": "01",
  "name": "Auth and Identity",
  "aliases": ["auth product", "identity", "login"],
  "code_dir": "services/auth",
  "code_layout": "own-dir",
  "type": "sub-product",
  "status": "building",
  "provides": ["auth.session-v1", "auth.tenant-claims-v1"],
  "consumes": ["billing.plan-v1"]
}
```

`code_dir` is **not** decided by this design. It is asked once, during that scope's own
planning run, and recorded here - `own-dir` (`services/auth`), `shared` (a monolith every
scope builds into), or `external` (section 6). `/develop-product` reads it; nothing else
in the system assumes a layout.

A scope is *addressable*, *activatable*, and *buildable*:

- **Addressable** - `01`, `auth`, or `services/auth` all resolve to the same scope.
- **Activatable** - `.loop/active-scope.json`, exactly like the existing
  `.loop/active-feature.json` (`feature_paths.read_active_feature`). One resolver,
  one file, same pattern - nothing new to learn.
- **Buildable** - `/develop-product ... auth ...` builds into that scope's `code_dir`.
  A command that names no scope and has none remembered asks which one (section 3.3).

### 3.1 Everything is run from the main folder

This is the decided invocation model, and it is the part that most affects the build.
The user never `cd`s into a sub-product. They type, from the main product folder:

```text
/plan-loop start working on auth product
/develop-product continue the portal checkout flow
/status
```

So **scope selection is a resolution step inside every command**, not a flag. Order:

1. **Explicit flag** - `--scope auth`, for scripts and for the agent's own internal calls.
2. **Named in the command text** - deterministic match of the text against every scope's
   `slug`, `name`, `aliases`, and its `PRODUCT_MAP` row title. Rules first, no LLM
   (`AGENTS.md` #4): exact slug, then whole-word name/alias, then unique prefix.
   `loop scope match "<text>"` is the single implementation; the skills call it, they
   do not each re-parse.
3. **Sticky active scope** - `.loop/active-scope.json`, set by the last command that
   resolved one, so a follow-up `/status` or `/develop-product` with no scope named
   continues where the user was.
4. **Nothing** - platform scope: the master plan, the map, the shared files.

Three rules keep this from guessing wrong, which is the whole risk of text matching:

- **Ambiguous never resolves.** Two scopes matched, or a partial match with no unique
  prefix, stops and asks with the candidates listed. It never picks the first one -
  that is the mis-binding failure `map_id_for()`'s substring fallback was removed for.
- **The resolved scope is always announced**, in the session banner and in
  `SESSION_MANIFEST.md`: `Scope: auth (plan/products/auth, code services/auth)`. A
  sticky scope silently carrying over into the wrong command is the one way this model
  loses work, so it is never silent.
- **A name that matches no scope is a question, not a new scope.** `/plan-loop start
  working on payments` where no `payments` scope exists asks whether to create it (and
  which `PRODUCT_MAP` row it is), rather than planning into the platform scope by
  accident.

`.loop-scope` pointer files stay in the design as a pure convenience - if someone does
`cd services/auth`, it resolves - but they are no longer the primary path, and nothing
depends on them existing.

### 3.2 The active scope is remembered, but re-confirmed after a break

Step 3 above is sticky, with one guard. `.loop/active-scope.json` records the scope
**and** the session that set it:

```json
{"slug": "auth", "set_at": "2026-08-24T11:20:03Z", "set_by_session": 412}
```

A later command with no scope named continues on `auth` **silently** while it is still
the same working session. It **asks first** when the stickiness is stale:

```text
/develop-product
  > Last scope was `auth`, set 3 days ago (session 412).
  > Continue on auth, or switch?
```

Stale is decided deterministically, never by feel - re-confirm when **either** the
current session id differs from `set_by_session` **or** `set_at` is more than 12 hours
old. One session's worth of work continues without friction; coming back tomorrow always
gets a checkpoint. That is the failure this guards: a remembered scope quietly absorbing
work the user believed was going somewhere else.

Switching is always explicit and always announced, in the banner and in
`SESSION_MANIFEST.md`.

### 3.3 When no scope is named and none is remembered

The command **stops and asks**. It never assumes:

```text
/develop-product
  > Which do you want to build?
    1. auth     (services/auth)      G-AUTH-02, 3 tasks ready
    2. portal   (apps/portal)        blocked on auth.session-v1
    3. shared platform work          CI, DB schema, design system - root TASKS.yml
```

Platform-level work is a real option in that list, not the default. Treating "no scope
named" as "shared work" would turn a forgotten word into edits to CI, schema, or the
design system - the blast radius that matters most in a single workspace, and the one
thing the federated design got for free from folder separation.

The list is ordered by the dependency sort in section 9.1, so the scope that unblocks
others is offered first.

## 4. What is shared and what is per scope

The split is not arbitrary. **Shared = anything two scopes must not disagree about.**

| State | Where | Why |
|---|---|---|
| `main_plan.md`, `PRODUCT_MAP.md` | root | the platform contract |
| `DECISIONS.md` | root, entries tagged `scope:` | **this alone kills `decision-conflict`.** Two scopes cannot resolve the same topic differently if there is one file; a real divergence becomes a superseding entry, not a finding |
| `DEPLOYMENT_PLAN.md` | root, with a per-scope overrides section | kills `deployment-conflict` the same way |
| `contracts/` | root | sub-to-sub, see section 5 |
| `EVIDENCE_LOG.md` | root | evidence is about the world, not about one scope |
| `memories/`, `state.db` | root, rows gain a `scope` column | one recall index, filtered per scope at read time |
| `CONTEXT.md` glossary | root | one product, one vocabulary - `glossary.py` already assumes this |
| PRD / architecture / steps / features | scope | authored, and genuinely local |
| `TASKS.yml`, `GATES.yml` | scope + root | see below |
| `DOUBTS.md` | scope + root | a doubt belongs to whoever must answer it |

**Tasks and gates** load as a union: the root file holds platform tasks, each scope file
holds its own, with IDs namespaced (`AUTH-TASK-003`, `G-AUTH-01`). A loader used by
`task_context.py`, `build_phase.py` and `status.py` returns the union with a `scope`
field attached, filtered to the active scope by default. Two things become possible that
are impossible today:

```yaml
# plan/products/portal/TASKS.yml
- id: PORTAL-TASK-002
  blocked_by: [AUTH-TASK-003]        # cross-scope dependency, resolved by the loader
  needs_contract: auth.session-v1    # and by contract, not just by ticket
```

That is the direct answer to "sub to sub is the hardest part": it stops being a *sync
problem* and becomes an *index lookup* in one file tree.

## 5. Cross-scope interfaces (`plan/contracts/`)

Today `INTEGRATIONS.yml` plus `contract-gap` compares two declarations across a boundary
and reports disagreement. In one workspace the same information becomes a registry with
one provider and many consumers:

```yaml
# plan/contracts/auth.session-v1.yml
id: auth.session-v1
provider: auth
status: draft            # draft -> agreed -> implemented -> deprecated
surface: "POST /session/verify -> {tenant_id, subject, scopes[]}"
consumers:
  - scope: portal
    status: agreed
  - scope: billing
    status: declined
    rationale: "server-to-server via signed JWT instead (D-014)"
supersedes: auth.session-v0
```

Deterministic checks - rules first, no LLM (`AGENTS.md` non-negotiable #4):

| Check | Fires when |
|---|---|
| `contract-unprovided` | a scope `consumes` an id no scope `provides` |
| `contract-unimplemented` | a consumer task is `in_progress` while the contract is still `draft` |
| `contract-breaking` | provider edits an `agreed` / `implemented` surface without a new version id |
| `consumer-unnotified` | provider bumped the version and a consumer still points at the old one |

These are the **only** drift checks that survive as real checks. Everything else in
`hierarchy_drift.py`'s table becomes impossible by construction:

| Finding today | Fate |
|---|---|
| `parent-added` / `parent-changed` / `parent-removed` | **gone** - nothing to propagate; the scope reads the same file |
| `decision-conflict`, `deployment-conflict` | **gone** - one file per topic |
| `unmapped-sub`, `missing-link`, `uninitialized-sub`, `stale-sub` | **gone** - a scope is in the map or it does not exist |
| `dependency-gap`, `contract-gap` | **replaced** by the registry above |
| `unbuilt-row` | **kept** - a map row with no scope folder is still the next thing to start |

`PARENT_CONTEXT.md`, the watermark, the finding log and `parent_inbox` all lose their
reason to exist for in-tree scopes. That is roughly 2,400 of the ~2,980 lines.

### 5.1 When work in one scope needs a change in another

Building `portal` reveals that `auth` must expose a field it does not expose. In the
federated design this could only become a *finding* - a note that two plans disagree,
raised later, in a different session, in a different folder. In one workspace the
session can simply fix it, so the rule is about **consent, not capability**:

1. **Locate.** The command determines exactly where the change is required - which
   scope, which file, which task or contract. Deterministically, from the contract
   registry and the task index, not by guessing.
2. **Ask.** It raises it to the user as a question, naming the impact site and what the
   change would be:

   > `portal` needs `tenant_id` on the session payload. That is provided by `auth`
   > (`plan/contracts/auth.session-v1.yml`, provider scope `auth`).
   > This requires: a new contract version `auth.session-v2`, one new task in
   > `plan/products/auth/TASKS.yml`, and `AUTH-TASK-011` to be reopened.
   > Apply this?

3. **Apply on confirmation.** With the user's yes, the session writes the change **in
   the other scope** - contract, tasks, plan - in the same run. No queue, no note to
   drain later, no second session in another folder.
4. **Decline is also an answer.** A no records the doubt against `portal` with what it
   blocks, and `portal`'s task stays blocked rather than being built against a contract
   that will not exist.

The write policy this replaces (`docs/PRODUCT_HIERARCHY.md`: "authored product state is
never written across a workspace boundary") existed because a main-level run could
silently rewrite a plan in a folder the user was not working in. Here the protection is
the **question**, not the boundary: nothing crosses without an explicit yes, and because
it is one workspace the yes can be acted on immediately instead of being turned into a
finding somebody has to come back for.

## 6. External sub-products stay supported

The billing-in-another-repo case in `docs/PRODUCT_HIERARCHY.md` is real and does not go
away. It becomes the **exception** rather than the default:

- a scope may set `"external": {"workspace": "../billing"}` instead of `code_dir`
- for those, the existing bridge (`parent_context`, watermark, findings) is retained
  **unchanged** and runs only for external scopes
- `/subproduct-new` gains `--external` for the deliberate case

So this is a *narrowing*, not a removal: same machinery, one caller instead of every caller.

## 7. Context discipline - the main risk of this design

Ten scopes in one workspace means the naive `SESSION_MANIFEST.md` is ten times bigger,
and every command reads it. Unmanaged, this trades a sync problem for a context problem.
Three rules:

1. **Manifest is scope-filtered.** `session_lifecycle` emits root plan + active scope +
   contracts the active scope provides or consumes + *names only* of siblings.
2. **Recall is scope-filtered.** `session_recall` / `session_search` filter `state.db`
   on the new `scope` column, falling back to platform sessions.
3. **Memory is layered.** `memories/MEMORY.md` (platform, existing char limits) plus
   `memories/scopes/<slug>.md` (per scope, same limits). `memory_curator` curates the
   active scope's file and the platform file, never all of them.

Net context per session should be *smaller* than today, because a sub-product session
currently also carries a generated `PARENT_CONTEXT.md` copy of the parent's constraints.

## 8. Command surface

| Command | Change |
|---|---|
| `/plan-loop <text naming a scope>` | plans that scope, and asks how its code is laid out the first time; no scope named or sticky = platform plan plus map |
| `/develop-product <text naming a scope>` | **builds a sub-product from the main folder** - the core ask. Writes into that scope's `code_dir` |
| `/subproduct-new <rows>` | creates `plan/products/<slug>/`, asks how that scope's code is laid out, writes `scope.json`; no `mkdir`, no `loop setup`, no `cd` - and it can now chain straight into `/loop-engine`, because there is no second session state to bootstrap |
| `/product-tree` | reads one workspace; shows scopes, contracts, cross-scope blocks |
| `/product-tree-sync` | **retired for in-tree scopes** (nothing to sync); kept for external |
| `/feature-new` | features nest under the active scope |
| `/status`, `/prod-gap`, `/release-check` | scope-aware; aggregate across scopes by default, per scope when one is named or sticky |
| `/scope` (new) | `loop scope list / show / match / rename / absorb / eject` |

## 9. Migrating an existing sub-product workspace into the main one

Command: **`loop scope absorb <folder> [--map-id NN] [--dry-run]`**, surfaced as
`/subproduct-absorb`, and offered automatically by `/doctor` when it finds a child
`.loop-engineer/` inside a workspace already in unified mode.

**Preconditions - refuse, do not guess:**

- the child workspace resolves and is `role: sub` or `standalone`
- a `PRODUCT_MAP` row binds it, or `--map-id` is given
- the child has no staged `pending/` writes and no open findings
- `plan/products/<slug>/` does not already exist, or `--merge` was passed

**Algorithm** - all writes staged into a temp tree, committed atomically at the end:

| Child state | Becomes | Conflict rule |
|---|---|---|
| `plan/main_plan.md` | scope `prd.md`, appended under `## From sub-product plan` | never overwrite an authored pack file |
| `plan/steps/*`, `plan/features/*` | same paths under the scope | feature IDs renumbered unique **within the scope only** |
| `TASKS.yml` | scope `TASKS.yml`, IDs prefixed `SLUG-` | `blocked_by` rewritten through the same ID map; an unresolvable ref becomes a doubt, never a silent drop |
| `GATES.yml` | scope `GATES.yml`, `G-X` -> `G-SLUG-X` | gate refs inside tasks rewritten identically |
| `DOUBTS.md` | scope `DOUBTS.md`, `DQ-n` -> `DQ-SLUG-n` | superseded doubts stay superseded |
| `DECISIONS.md` | **merged into root**, each entry tagged `scope: slug` | same topic decided on both sides -> **stop and ask**; this is the one thing that must never be auto-merged |
| `EVIDENCE_LOG.md` | appended to root, entries tagged | dedupe on source URL plus claim |
| `memories/MEMORY.md` | `memories/scopes/<slug>.md` | curator runs afterwards to respect char limits |
| `state.db` sessions | inserted into root `state.db` with `scope = slug` | ids remapped, FTS index rebuilt |
| `PARENT_CONTEXT.md`, `SUBPRODUCTS.md`, `.loop/parent-sync.json`, `.loop/finding-log.json` | **dropped** | generated or boundary-only - nothing authored is lost |
| `.loop/active-feature.json` | scope-local active feature | |
| `INTEGRATIONS.yml` | seeds `plan/contracts/*` entries at `status: draft` | provider inferred from `counterparty`; unresolved ones surface as `contract-unprovided`, which is the correct loud failure |

**Afterwards:**

- the child `.loop-engineer/` is **renamed** to `.loop-engineer.absorbed-<date>/`, not
  deleted. Renaming is load-bearing: `_has_markers_at` no longer matches, so nearest-wins
  resolution stops finding it. Leaving it in place would silently route every future
  session in that folder back to the dead workspace - the single worst failure mode of
  this migration.
- a `.loop-scope` pointer file is written in the folder
- `scope.json` records `code_dir` and `absorbed_from`
- the map row's `Workspace` column is updated to the scope path
- a full report prints every rewritten ID, every dropped file, and every conflict raised
  as a doubt

**Reversal:** `loop scope eject <slug>` does the inverse - scope folder back out to a
child workspace - which is what the `.absorbed-<date>` copy is retained for.
Reversibility is what makes this safe to adopt incrementally.

**Bulk:** `loop scope absorb --all` walks `scan_children` and absorbs each, stopping at
the first conflict rather than half-migrating a tree.

### 9.1 Dependency order, for absorbing and for building

Absorbing `portal` before `auth` leaves `blocked_by: [AUTH-TASK-003]` pointing at
something not yet imported. Rather than tolerate dangling refs, **absorb runs in
dependency order**: the scopes others depend on go first.

The order is computed, not asked for - a topological sort of `PRODUCT_MAP`'s
`Depends on` column, plus `provides` / `consumes` in each `scope.json`, plus any
`INTEGRATIONS.yml` being converted. `loop scope absorb --all` prints the order it
derived before it writes anything.

- **A cycle stops the run** and prints the cycle. Two sub-products that depend on each
  other are a planning problem, and silently breaking the loop at an arbitrary edge
  would hide it.
- **A ref to a scope not in this batch** is still recorded as pending and healed when
  that scope lands, so a partial absorb is safe.

The same ordering is worth reusing beyond migration: `/product-tree` and
`/subproduct-new` should recommend the **next scope to plan and build** by the same
sort, so a dependency sub-product is planned and built before the scopes waiting on it,
instead of the user picking a scope that will immediately block on a contract nobody has
written yet.

## 10. Rollout

| Phase | Content | Gated by |
|---|---|---|
| **P0** | scope model: `scope_paths.py`, `scope.json`, `loop scope match`, active-scope resolver, union loaders for TASKS / GATES / DOUBTS. Existing workspaces behave as one implicit platform scope - **zero behaviour change** | nothing; inert until a scope exists |
| **P1** | `loop scope absorb` / `eject`, plus `/doctor` detection | `--dry-run` first |
| **P2** | `plan/contracts/` and the four deterministic checks; retire `dependency-gap` / `contract-gap` | `mode: unified` in `.loop/workspace.json` |
| **P3** | command surface: `/develop-product <scope>`, `/subproduct-new` writes scopes, scope-filtered manifest / recall / memory | same flag |
| **P4** | narrow the bridge stack to external scopes only; rewrite `test_workspace_hierarchy.py` (996 lines), `test_tree_sync.py`, `test_parent_propagation.py`, `test_subproduct_new.py` | after one real product has been absorbed and ejected cleanly |

Both modes coexist through P0-P3, chosen per workspace by
`.loop/workspace.json: {"mode": "unified" | "federated"}`. No existing workspace changes
behaviour until it is absorbed.

## 11. Decisions

**Settled (2026-08-24):**

| Question | Answer | Consequence in this design |
|---|---|---|
| Scope folder naming | `plan/products/<slug>/`, no numeric prefix | folder name stops being the binding key; `scope.json.map_id` plus a `Scope` column bind instead (section 2) |
| Code layout | user's choice, asked during that scope's planning | `scope.json.code_layout` = `own-dir` / `shared` / `external`; nothing else assumes a layout |
| Gates | per scope | scope `GATES.yml` plus root platform gates, unioned by the loader |
| External repos | stay federated | the bridge stack survives, narrowed to external scopes only |
| Invocation | every command from the main folder, scope named in the text | scope resolution moves inside every command (section 3.1) |

**Also settled (2026-08-24, second round):**

| Question | Answer | Where |
|---|---|---|
| Does the active scope stick between commands? | yes, but re-confirmed after a break - different session or older than 12h | 3.2 |
| No scope named and none remembered? | stop and ask, with shared platform work as one listed option, never the default | 3.3 |
| Work in one scope needs a change in another? | locate the impact site, ask the user, apply across scopes on confirmation | 5.1 |
| Absorb order when scopes depend on each other? | dependency order, computed; cycles stop the run. Same sort recommends what to plan and build next | 9.1 |

**Nothing is open.** The design is decided end to end; what remains is the P0-P4 build in
section 10.
