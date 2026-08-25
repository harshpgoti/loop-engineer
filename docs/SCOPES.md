# Scopes - Sub-Products Inside One Workspace

User-facing operations happen through `/scope`, `/plan-loop`, `/develop-product`, or natural
language. Shell examples below are internal runtime references for agents and maintainers,
not steps users must chain manually.

A platform is one product with several sub-products. There are two ways to hold that:

| Mode | Sub-product is | Kept in agreement by |
|------|----------------|----------------------|
| **unified** (this document) | A **scope**: `plan/products/<slug>/` in the main workspace, with its code wherever the user decided | Nothing - it is one workspace |
| **federated** ([`PRODUCT_HIERARCHY.md`](PRODUCT_HIERARCHY.md)) | A folder with its own `.loop-engineer/` | A bridge: `PARENT_CONTEXT.md`, watermarks, findings |

Unified is the default for new sub-products. Federated remains supported and is the right
answer for a sub-product in **another repo** - see [External](#external-sub-products).

## Layout

```text
main-product/
├── .loop-engineer/
│   ├── plan/
│   │   ├── main_plan.md              # the platform plan
│   │   ├── PRODUCT_MAP.md            # one row per sub-product; `Scope` column binds it
│   │   ├── contracts/                # cross-scope interfaces
│   │   │   └── auth.session-v1.yml
│   │   └── products/
│   │       ├── auth/
│   │       │   ├── scope.json        # identity, map_id, code_dir, provides/consumes
│   │       │   ├── prd.md architecture.md data-model.md ...
│   │       │   ├── steps/  features/
│   │       │   ├── TASKS.yml  GATES.yml  DOUBTS.md
│   │       └── portal/
│   ├── TASKS.yml GATES.yml DOUBTS.md DECISIONS.md    # platform level
│   ├── memories/  (+ memories/scopes/<slug>.md)
│   └── state.db   (sessions carry a `scope` column)
├── services/auth/     └── .loop-scope      # optional pointer, so `cd` also works
└── apps/portal/       └── .loop-scope
```

The scope folder **is** the ultraplan pack from [`ULTRAPLAN.md`](ULTRAPLAN.md), moved under
`plan/products/` and given the build state it never had. This is not a second hierarchy
beside ultraplan - it is the same one, finished.

## The folder name is not the binding key

In the federated model, `workspace_tree.map_id_for()` binds a sub-product by slug-equality
of folder name to map-row title, which is why retitling a row silently unbinds it and
leaves the row "unbuilt while looking built".

Scopes bind explicitly instead:

- `scope.json` carries `"map_id": "01"`, written once at creation and never inferred.
- `PRODUCT_MAP.md` carries a `Scope` column naming the folder.
- Retitling a row changes nothing. `loop scope rename` moves the folder and every
  reference together.
- Slug-matching survives only as a **reported** fallback for unbound legacy folders.

## Which sub-product a command is about

Every command is run from the **main folder**, with the sub-product named in the text:

```text
/plan-loop start working on auth product
/develop-product continue the portal checkout flow
```

One implementation resolves it - `loop scope resolve --text "..." --session <id>` - and
every skill calls it rather than parsing the text itself.

1. explicit `--scope`
2. named in the command text: exact slug or map id as a whole word, then a full name or
   alias as a phrase, then a unique slug prefix. Rules first, no model call
3. a `.loop-scope` pointer in cwd or a parent
4. the remembered scope (`.loop/active-scope.json`)

Exit code is the instruction: `0` go, `2` **ask the user first**.

| Guard | Why |
|---|---|
| Ambiguous never resolves | Picking the first of two matches is the mis-binding that the federated binder's substring fallback was removed for |
| The scope is always announced | `Scope: auth (plan/products/auth, code services/auth)` in the banner and the manifest |
| Nothing resolved asks | Treating "no scope named" as "shared platform work" turns a forgotten word into edits to CI, schema, or the design system |

### Remembered, but re-confirmed after a break

`.loop/active-scope.json` stores the scope, when it was set, and by which session. It
continues **silently** within one session, and **asks** when stale - a different session
id, or older than 12 hours:

```text
Last scope was `auth`, set 3 days ago. Continue there, or switch?
```

Deterministic, not a judgement call. One session's work flows without friction; coming
back tomorrow always gets a checkpoint.

## What is shared, what is per scope

Shared means anything two sub-products must not disagree about.

| State | Where | Why |
|---|---|---|
| `main_plan.md`, `PRODUCT_MAP.md` | root | the platform contract |
| `DECISIONS.md` | root, tagged `scope:` | one file per topic, so `decision-conflict` cannot exist |
| `DEPLOYMENT_PLAN.md` | root | same reason |
| `contracts/` | root | one provider, many consumers |
| `EVIDENCE_LOG.md` | root | evidence is about the world, not one sub-product |
| `memories/`, `state.db` | root, per-scope file / `scope` column | one index, filtered on read |
| `CONTEXT.md` glossary | root | one product, one vocabulary |
| PRD, architecture, steps, features | scope | authored and genuinely local |
| `TASKS.yml`, `GATES.yml`, `DOUBTS.md` | scope **and** root | unioned by the loader |

Tasks and gates load as a union with the scope attached. A scope always sees platform
tasks too - platform work gates scope work, and hiding it would report a false "ready".

```yaml
# plan/products/portal/TASKS.yml
- id: PORTAL-TASK-002
  blocked_by: [AUTH-TASK-003]        # cross-scope, resolved by the loader
  needs_contract: auth.session-v1
```

A `blocked_by` naming nothing is **reported, never dropped** - that is exactly what a
half-finished absorb would leave behind.

## Contracts

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
    rationale: "signed JWT instead (D-014)"
```

`loop scope check` runs four deterministic checks:

| Kind | Level | Fires when |
|---|---|---|
| `contract-unprovided` | error | A scope consumes an id no scope provides, or the provider is not a scope here |
| `contract-unimplemented` | error | A consumer task is in progress while the contract is still `draft` |
| `contract-breaking` | error | A frozen (`agreed`/`implemented`) surface changed without a new version id |
| `consumer-unnotified` | warn | A consumer still points at a superseded version |

`declined` is an answer, not a gap. `loop scope lock` records agreed surfaces - the only
history `contract-breaking` needs, since without it the edited surface simply *is* the
surface.

Everything else the federated drift table reported is now impossible by construction:
`parent-added/changed/removed`, `decision-conflict`, `deployment-conflict`,
`unmapped-sub`, `missing-link`, `uninitialized-sub`, `stale-sub`.

## When one scope needs a change in another

Locate, ask, apply - in the same run:

```bash
loop scope impact auth.session-v1     # provider, its plan folder, the file, live consumers
```

The command names the impact site, asks the user with the specific change spelled out,
and on a yes writes it in the other scope. A no records the doubt and leaves the
dependent task blocked. The protection is the question, not a boundary.

## Dependency order

`loop scope list` sorts sub-products so that what others depend on comes first, from
`PRODUCT_MAP`'s `Depends on`, `scope.json` `depends_on`, and provider/consumer links. Use
it to recommend what to plan and build next. A **cycle stops the run** and is printed
rather than broken at an arbitrary edge.

## Absorbing a federated sub-product

```bash
loop scope discover                        # candidates, in dependency order
loop scope absorb ./auth-service --dry-run
loop scope absorb ./auth-service
loop scope absorb --all                    # stops at the first refusal
loop scope eject auth-service              # the reversal
```

| Child state | Becomes |
|---|---|
| `plan/main_plan.md` | scope `prd.md`, under `## From sub-product plan` |
| `plan/steps/`, `plan/features/`, other authored plan files | the same, inside the scope |
| `TASKS.yml` | scope `TASKS.yml`, ids prefixed `SLUG-`, every reference rewritten |
| `GATES.yml` | `G-X` -> `G-SLUG-X`, task gate refs rewritten with them |
| `DOUBTS.md` | `DQ-n` -> `DQ-SLUG-n` |
| `DECISIONS.md` | merged into root, tagged `scope:` |
| `EVIDENCE_LOG.md` | appended to root, tagged |
| `memories/MEMORY.md` | `memories/scopes/<slug>.md` |
| `state.db` sessions | root `state.db`, `scope` column set |
| `INTEGRATIONS.yml` | draft contracts in `plan/contracts/` |
| `PARENT_CONTEXT.md`, `SUBPRODUCTS.md`, `.loop/parent-sync.json`, `.loop/finding-log.json` | dropped - generated or boundary-only |

Refusals, all **before the first write**: no workspace in the folder, no map row (pass
`--map-id`), staged writes still pending, the scope folder already exists (`--merge`), or
a **decision conflict**. That last one is the only thing never auto-merged - guessing
which side wins would discard a real decision.

Id renaming is idempotent: `AUTH-TASK-001` never becomes `AUTH-AUTH-TASK-001`.

Afterwards the child workspace is **renamed** to `.loop-engineer.absorbed-<date>/`.
The rename is load-bearing - `workspace_resolver` looks for markers at
`<folder>/.loop-engineer`, and leaving that path intact would silently route every future
session in the folder back to the dead workspace. It is also what `eject` restores from,
so it is not litter.

## The federated bridge, and when it runs

`PARENT_CONTEXT.md`, the parent watermark, derived findings and `plan/SUBPRODUCTS.md`
exist to keep two *workspaces* agreeing. They run exactly when a second workspace is
still involved:

| Situation | Bridge |
|---|---|
| This workspace is a sub-product with a parent | runs |
| A child folder still holds its own `.loop-engineer/` - external, or not yet absorbed | runs, for that child |
| Every sub-product is a scope here | **skipped**, and a stale `SUBPRODUCTS.md` is removed |

`loop workspace sync` in a unified workspace says so rather than telling you to create
sub-product workspaces - advice that would rebuild the boundary you removed. Ejecting a
scope brings the bridge straight back for that folder.

Two things this had to fix, both found by absorbing a real three-sub-product platform:

- **The absorbed child is unlinked from the main workspace.** Otherwise the entry stays,
  the folder is found without its data dir, and `missing-link` is reported as an error
  every session, telling you to restore folders you deliberately absorbed.
- **A map row bound to a scope counts as built.** `unbuilt-row` means "the plan says this
  is a sub-product and nothing is building it". An absorbed row is being built here, so
  reporting it unbuilt would never stop.

## Eject is a real reversal

Absorb copies the sub-product's decisions, evidence, memory and sessions into the shared
files. Eject removes those copies again - the child's own were never touched.

Skipping that step is not cosmetic: both sides then hold the same decisions, and the
drift check correctly reports every shared topic as a `decision-conflict`. On the real
platform that was ten shared topics and three error-level findings, none of them a real
disagreement.

## External sub-products

A sub-product in another repo stays federated: it keeps its own workspace and the
existing bridge (`PARENT_CONTEXT.md`, the parent watermark, `loop findings`). Nothing in
[`PRODUCT_HIERARCHY.md`](PRODUCT_HIERARCHY.md) changes for it - that machinery now serves
this one case instead of every case.

## Backward compatibility

A workspace with no `plan/products/` is `federated` and behaves exactly as before: no
`## Scope` block in the manifest, no scope resolution, unchanged read order. Mode is
inferred from the presence of scopes, or pinned in `.loop/workspace.json`:

```json
{"mode": "unified"}
```

## Internal runtime reference

```bash
loop scope list | show <slug> | new <slug> | rename <old> <new>
loop scope resolve --text "<user text>" --session <id> [--remember]   # 0 = go, 2 = ask
loop scope use <slug> | clear
loop scope check | impact <contract-id> | lock
loop scope discover | absorb <folder> [--map-id NN] [--dry-run] [--all] | eject <slug>
```
