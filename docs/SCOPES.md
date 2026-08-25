# Scopes - Sub-Products Inside One Workspace

User-facing operations happen through `/scope`, `/plan-loop`, `/develop-product`, or natural
language. Shell examples below are internal runtime references for agents and maintainers,
not steps users must chain manually.

A platform is one product with several sub-products. **There is one workspace**, at the
main product folder, and it holds every sub-product's plan.

A sub-product's *code* can live anywhere - a folder in the product tree, or a repository
of its own. Being big enough to deserve its own repo is a reason to split the **code**,
never a reason to split the plan: the moment the plan splits, one sub-product can no
longer depend on another without a synchronisation mechanism between two workspaces, and
that mechanism is what this design removed.

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
| Shared platform is explicit | `shared platform`, `platform work`, or `root plan` resolves root plan/tasks without pretending a sub-product was selected |

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
session in the folder back to the dead workspace. The renamed copy is kept as a plain
backup of what was absorbed; nothing reads it, so it can be deleted once the absorb has
been verified.

## What the single workspace removed

The federated layout gave each sub-product a workspace of its own, and roughly 2,000
lines existed only to keep two workspaces agreeing. All of it is gone:

| Removed | Why it cannot apply |
|---|---|
| `parent_context.py`, `plan/PARENT_CONTEXT.md` | A scope reads the same files as the platform - nothing to copy across |
| `parent_watermark.py`, `.loop/parent-sync.json` | Nothing to have "last seen" |
| `parent_inbox.py`, `finding_log.py`, `loop findings` | A scope has no parent to disagree with |
| `subproducts_report.py`, `plan/SUBPRODUCTS.md` | The plans are already in one tree - `loop scope list` reads them directly |
| `hierarchy_sync.py`, `tree_sync.py`, `/product-tree-sync` | No boundary to sync |
| `subproduct_new.py`, `/subproduct-new` | Carving a workspace out re-creates the boundary; `/scope new` creates the plan folder instead |
| `hierarchy_drift.check_children` and 8 drift kinds | `parent-added/changed/removed`, `decision-conflict`, `deployment-conflict`, `unmapped-sub`, `missing-link`, `stale-sub` are all impossible when there is one plan |
| `loop scope eject` | There is no second layout to go back to |

What replaced them is smaller and answers the same questions from files this workspace
already holds: `plan/contracts/` with four deterministic checks, cross-scope `blocked_by`
resolved by the task loader, and `scope_readiness.py` for `/status`, `/prod-gap` and
`/release-check`.

`loop scope absorb` **stays**. It is the way a sub-product that still has its own
`.loop-engineer/` gets folded in - the migration path, one direction only.

## Sub-products in another repo

A sub-product large enough to warrant its own repository still has **no workspace of its
own**. Its plan lives here like every other scope; only its code is elsewhere:

```json
{
  "slug": "billing",
  "map_id": "03",
  "code_layout": "external",
  "code_dir": "D:/repos/billing"
}
```

| `code_layout` | Where the code is | Where the plan is |
|---|---|---|
| `own-dir` | a folder in the product tree (`services/auth`) | here |
| `shared` | one app tree several scopes build into | here |
| `external` | another repository entirely | here |

`code_dir` may be an absolute path or a path outside the product folder; `/develop-product`
and `/deploy` read it and work in that checkout. Nothing else changes: the same
`plan/products/billing/` holds its PRD, tasks, gates and doubts, and a task in another
scope can depend on one of its tasks directly.

## A workspace with no scopes

A product that never split has no `plan/products/`, and behaves exactly as a
single-product workspace always did: no `## Scope` block in the manifest, no scope
resolution, unchanged read order. Scopes appear the first time one is created or absorbed.

## Internal runtime reference

```bash
loop scope list | show <slug> | new <slug> | rename <old> <new>
loop scope resolve --text "<user text>" --session <id> [--remember]   # 0 = go, 2 = ask
loop scope use <slug> | clear
loop scope check | impact <contract-id> | lock
loop scope discover | absorb <folder> [--map-id NN] [--dry-run] [--all]
```
