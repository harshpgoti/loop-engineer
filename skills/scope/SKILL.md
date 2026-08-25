---
name: scope
description: Sub-products planned and built inside one workspace as scopes under plan/products/, how a command decides which sub-product it is about, how one sub-product asks another for a change, and how to fold a federated sub-product workspace into the main one. Use when the user types /scope, names a sub-product in a command, asks to switch sub-products, or wants a sub-product's own .loop-engineer merged into the main product.
---

# Scopes

## Purpose

A platform is one product with several sub-products. The federated layout gave each
sub-product a workspace of its own, and everything that kept the two ends agreeing was a
bridge across that boundary - roughly 2,980 lines of it. Worse, the direction that
matters most had no channel at all: one sub-product needing something from another could
only be expressed as a *finding* that two plans disagreed.

A **scope** is that sub-product living inside the main product's single workspace:

```text
.loop-engineer/plan/products/auth/     plan, tasks, gates, doubts, features, steps
services/auth/                         its code
```

One workspace, so a portal task can be `blocked_by` an auth task, a contract has a real
provider and real consumers, and nothing needs syncing.

## Read First

- `commands/scope.md`
- `plan/SESSION_MANIFEST.md` - the `## Scope` block says which sub-product this session is about
- `plan/products/<slug>/scope.json`
- `plan/contracts/` when the work crosses sub-products
- `docs/SCOPES.md` for the full model

## Which sub-product is this command about?

The user runs **every** command from the main product folder and names the sub-product in
the text:

```text
/plan-loop start working on auth product
/develop-product continue the portal checkout flow
```

So resolution happens inside the command. **You** run this - the user never types it,
and you never re-parse their text yourself:

```bash
loop scope resolve --text "<what the user typed>" --session "<session id>" --remember
```

| Exit | Meaning | What to do |
|---|---|---|
| `0` | resolved scope or explicitly selected shared platform | Print the `banner`, then work in `plan_dir` and `code_dir` |
| `2` | not resolved, or needs confirming | **Ask the user.** Do not proceed |

Order: explicit `--scope`, then the command text, then a `.loop-scope` pointer, then the
remembered scope. Three rules make it safe:

- **Ambiguous never resolves.** Two scopes matched is a question with both named.
- **Remembered is re-confirmed after a break** - a different session, or more than 12
  hours. Within one session it continues silently.
- **Nothing resolved asks**, listing the sub-products *and* shared platform work. Never
  treat "no scope named" as "shared work": that turns a forgotten word into edits to CI,
  schema, or the design system.
- **Shared platform phrases resolve.** `shared platform`, `platform work`, `root platform`,
  `root plan`, and `root tasks` are affirmative root selections, not missing scope names.

## Announce it

Before writing anything, say which scope is active and where its plan and code are:

```text
Scope: auth (plan/products/auth, code services/auth)
```

A remembered scope silently carrying into the wrong command is the one way this model
loses work.

## Code layout is the user's decision

`scope.json.code_dir` is **not** set by this skill. It is asked once, during that scope's
own `/plan-loop`, and recorded:

| `code_layout` | Meaning |
|---|---|
| `own-dir` | The scope owns a folder (`services/auth`). Strongest write isolation |
| `shared` | Several scopes build into one app tree. Write-scoping is weaker - say so |
| `external` | The code lives in another repo; the plan still lives here |

## When work in one scope needs a change in another

This is the case the federated design could not handle. Do not switch scope, and do not
queue a note. In the same run:

1. **Locate** the impact site deterministically - `loop scope impact <contract-id>` names
   the provider scope, its plan folder, the contract file, and every live consumer.
2. **Ask the user**, naming exactly what would change:

   > `portal` needs `tenant_id` on the session payload, provided by `auth`
   > (`plan/contracts/auth.session-v1.yml`). This requires a new contract version
   > `auth.session-v2`, one new task in `plan/products/auth/TASKS.yml`, and
   > `AUTH-TASK-011` reopened. Apply this?

3. **Apply on confirmation** - write the contract, tasks and plan in the other scope now.
4. **A no is also an answer.** Record the doubt against the asking scope with what it
   blocks, and leave its task blocked rather than building against a contract that will
   not exist.

The old rule was "authored state never crosses a workspace boundary". Here the protection
is the question, not the boundary.

## Contracts

`plan/contracts/<id>.yml` - one provider, many consumers, checked by `loop scope check`:

| Finding | Means |
|---|---|
| `contract-unprovided` | A scope consumes something no scope provides |
| `contract-unimplemented` | A consumer task is in progress against a still-draft contract |
| `contract-breaking` | A frozen surface was edited without a new version id |
| `consumer-unnotified` | A consumer is still on a superseded version |

`status: declined` on a consumer is an **answer, not a gap** - deciding not to integrate
is a real decision, and saying so stops the checker guessing.

Run `loop scope lock` when a contract reaches `agreed`: it records the surface, which is
the only history `contract-breaking` needs.

## Dependency order

`loop scope list` orders sub-products so that what others depend on comes first, derived
from `PRODUCT_MAP`'s `Depends on`, `scope.json` `depends_on`, and provider/consumer links.
Recommend the next sub-product to plan or build from that order, so nobody starts on a
scope that will immediately block on a contract nobody has written.

A **cycle stops the run** and is printed. Two sub-products depending on each other is a
planning problem; breaking an arbitrary edge would hide it.

## Absorbing a federated sub-product

A sub-product that still has its own `.loop-engineer/`. The user asks for this in words -
"merge the auth sub-product into main", `/scope absorb ./auth-service` - and **you** run
the runtime below; do not hand them a command list:

```bash
loop scope discover                      # what could be absorbed, in dependency order
loop scope absorb ./auth-service --dry-run
loop scope absorb ./auth-service
```

What happens: the plan becomes `plan/products/<slug>/`; task, gate and doubt ids are
prefixed with the scope and every reference rewritten with them; decisions merge into the
shared `DECISIONS.md` tagged by scope; memory becomes `memories/scopes/<slug>.md`;
sessions fold into `state.db` carrying their scope; `PARENT_CONTEXT.md`, the watermark and
the finding log are dropped as generated.

Four refusals, all of them before the first write:

- the folder holds no workspace, or no map row binds it (pass `--map-id`)
- staged writes are still pending there
- `plan/products/<slug>/` already exists (pass `--merge`)
- **both plans decided the same topic differently** - the one thing that is never
  auto-merged. Resolve it in `DECISIONS.md`, or pass `--accept-conflicts` to keep both
  sides side by side

A dangling `blocked_by` is recorded as a doubt in the scope, never dropped.

Afterwards the child workspace is **renamed** to `.loop-engineer.absorbed-<date>/`. That
rename is load-bearing: leave the original path intact and every future session run in
that folder silently resolves to the dead workspace instead of the main one. It is also
the backup of what was absorbed - nothing reads it, so delete it once you have verified the absorb.

## Sub-products in another repo

A sub-product big enough for its own repository still has no workspace of its own. Set
`code_layout: "external"` and point `code_dir` at that checkout - the plan stays here, in
`plan/products/<slug>/`, like every other scope. Splitting the code is a size decision;
splitting the plan would cost cross-scope dependencies, which is the thing this design
exists to keep.

## Rules

- **The `loop` lines in this file are yours to run, never to print.** Report findings,
  not commands. If you catch yourself writing "run `loop scope check`", run it instead
  and report the result. Users only ever see slash commands.
- Resolve the scope, announce it, then act. Exit `2` means ask.
- Write inside the active scope. Crossing into another one requires the user's yes.
- Platform-level work (CI, schema, design system, shared infra) is a **listed choice**,
  never the fallback.
- Run the cross-scope check before handing off, and report what it found - an
  unprovided contract or a dangling blocker is a build that will fail later.
