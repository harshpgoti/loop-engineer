# Loop Engineer - Data Layout

Loop Engineer separates **updatable app code** from **durable memory/data** -
`app/` never mixes with data, in both global and local modes.

Works the same on Windows, macOS, and Linux.

## Global layout: `~/.loop-engineer/`

```text
~/.loop-engineer/
├── app/                     # updatable tool runtime (git clone)
├── bin/loop                 # internal bridge used by coding-agent skills
└── data/                    # ALL global memory/data - nothing else lives loose here
    ├── registry/
    │   └── workspaces.json  # registered local product folders
    ├── memories/            # global MEMORY.md, USER.md, SOUL.md
    ├── state.db             # global session search (SQLite FTS5)
    ├── skills/              # global procedural skills
    ├── secrets.env          # user secrets, if any (chmod 600)
    ├── plan/                # product plan: main_plan.md + step plans
    ├── DOUBTS.md
    └── ...
```

## Local layout: `<product-folder>/.loop-engineer/`

A local product folder gets the exact same split, just rooted one level
deeper - `app/` doesn't apply locally (the tool runtime stays global), but
**all** memory/data is nested under a single hidden `.loop-engineer/` folder
so it never mixes with your actual product code:

```text
my-product/
├── src/                     # your product code - untouched by Loop Engineer
├── package.json
└── .loop-engineer/          # ALL local memory/data, hidden away
    ├── memories/
    │   ├── MEMORY.md
    │   ├── USER.md
    │   └── SOUL.md
    ├── state.db
    ├── skills/
    ├── plan/                # main_plan.md + step plans
    ├── docs/
    ├── .ai/
    ├── DOUBTS.md, TASKS.yml, GATES.yml, DECISIONS.md, ...
    └── .loop-workspace-version
```

## Two memory modes

| Mode | Data root | When used |
|------|-----------|-----------|
| **Global** (default) | `~/.loop-engineer/data/` | Installer default; no local loop data in cwd |
| **Local** | `<product-folder>/.loop-engineer/` | `/setup-loop-engine` from that product folder |

### Auto-detection

When you run `/plan-loop`, `/loop-engine`, or another Loop skill:

1. Loop checks the **current folder** (and parents) for a `.loop-engineer/` subfolder with local loop data (`memories/`, `.loop-workspace-version`, etc.)
2. **If found** → uses `<that-folder>/.loop-engineer/` as the data root
3. **If not** → uses global data in `~/.loop-engineer/data/`

Example: set up `H:/POC/QEAutoAI` once with local mode, close the terminal, come back later - `/plan-loop` automatically uses `H:/POC/QEAutoAI/.loop-engineer/` again, from anywhere inside that product folder (including subdirectories).

## Nested products (main product + sub-products)

Local workspaces nest. A main product folder can contain sub-product folders that each
have their own `.loop-engineer/`, and resolution still picks the **nearest** one - working
inside `auth-svc/` uses `auth-svc/.loop-engineer/`, never the parent's.

```text
main-product/
├── .loop-engineer/          role: main   (plan/SUBPRODUCTS.md rolls the children up)
├── auth-svc/
│   └── .loop-engineer/      role: sub    (plan/PARENT_CONTEXT.md holds what it inherits)
└── portal/
    └── .loop-engineer/      role: sub
```

The link between them lives in `<workspace>/.loop/workspace.json` and is refreshed at
every `loop session-start`. No file means `standalone`, the unchanged single-product
behavior. See [`docs/PRODUCT_HIERARCHY.md`](PRODUCT_HIERARCHY.md).

## Central tool + local product (multiple products)

```text
~/projects/
├── QEAutoAI/
│   └── .loop-engineer/      # local memories/, plan/main_plan.md, state.db
├── OtherProduct/
│   └── .loop-engineer/      # separate local memory
~/.loop-engineer/app/        # shared tool runtime
```

Open the coding agent in `~/projects/QEAutoAI` and run `/setup-loop-engine`.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `LOOP_ENGINEER_HOME` | Override home (default `~/.loop-engineer`) - `app/`, `bin/`, and `data/` all live under this |
| `LOOP_HOME` | Alias for `LOOP_ENGINEER_HOME` |

## Updates

Use `/upgrade-loop-engineer` to update deliberately and `/doctor` to check the runtime
and active workspace. The coding agent invokes the internal runtime operations.

Data (global `data/` or local `.loop-engineer/`) is never touched by a runtime update.

## Migrating from the old flat layout

If you have an existing install predating the `app/data` and `.loop-engineer/`
split (files sitting loose directly in `~/.loop-engineer/` or your product
folder root), run `/migrate-import` and ask it to migrate the legacy layout. It previews
the move before applying it.

Dry-run by default. Only moves an explicit allowlist of Loop-Engineer-owned
paths - never touches your actual product code. For local mode, `docs/` and
`skills/` are flagged rather than auto-moved (a real product may have its own),
except the three known Loop-Engineer-generated files under `docs/`.

## Session bootstrap read order

1. `plan/SESSION_MANIFEST.md` (after `loop session-start`)
2. `memories/SOUL.md`
3. `memories/USER.md`
4. `memories/MEMORY.md`
5. `CONTEXT.md`
6. `plan/main_plan.md`, `HANDOFF.md`, active feature `spec.md` / `tasks.md` (when set)
7. `plan/SUBPRODUCTS.md` (main product) or `plan/PARENT_CONTEXT.md` (sub-product)
8. `plan/SESSION_RECALL.md`, `plan/AUTO_SKILLS.md`, `plan/AUTO_AGENT_SKILLS.md`

All paths above are relative to the resolved data root (`~/.loop-engineer/data/`
or `<product-folder>/.loop-engineer/`).

Feature specs: `plan/features/` - see `docs/FEATURE_WORKFLOW.md`

Always-on lifecycle: `docs/SESSION_LIFECYCLE.md`

The active skill refreshes the manifest automatically through session lifecycle.
