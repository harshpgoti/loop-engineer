# /scope

Work with the sub-products planned and built inside this one workspace: list them, switch between them, check how they depend on each other, and fold a sub-product that still has its own `.loop-engineer/` into this workspace.

## How To Interpret

If the user says `/scope`, `scopes`, `list sub products`, `switch to <sub-product>`, `work on <sub-product>`, `merge the sub product into the main workspace`, `absorb <folder>`, `move the sub product plan into main`, or asks which sub-product is active, execute this file directly.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read and write product-state files in the **active workspace** (local `.loop-engineer/` auto-detected from cwd).

1. `AGENTS.md`
2. `skills/scope/SKILL.md`
3. `plan/SESSION_MANIFEST.md` (the `## Scope` block)
4. `plan/PRODUCT_MAP.md`
5. `plan/products/<slug>/scope.json` for the scope in question
6. `plan/contracts/` when the question is about one sub-product needing something from another

## Loop

```text
SESSION-START -> RESOLVE SCOPE -> ACT (list | switch | check | absorb) -> REPORT -> NEXT COMMAND
```

## What the user types

They type `/scope`, or say it in words. Everything after the command name is theirs to
phrase - resolve it, do not make them learn a syntax:

```text
/scope                                    -> list sub-products, say which is active
/scope work on the payer forms product    -> switch to it
/scope work on shared platform            -> select root plan/tasks explicitly
/scope absorb the auth-service folder     -> fold its workspace into this one
/scope what breaks if auth changes?       -> contract impact
"merge my sub-products into the main workspace"
"which sub-product am I on?"
```

## Scripts

Internal runtime the **agent** runs (`docs/INTERNAL_RUNTIME.md`). Never print these as
steps for the user, and never ask them to run one:

```bash
loop scope list                       # every sub-product, in dependency order
loop scope show auth                  # one scope: plan dir, code dir, contracts, tasks
loop scope use auth                   # remember it for later commands
loop scope clear                      # forget it, so the next command asks
loop scope new auth --name "Auth and Identity" --code-dir services/auth --map-id 01
loop scope rename auth identity       # folder and every reference, together
loop scope check                      # contract, dependency, gate and cycle findings
loop scope impact auth.session-v1     # who a change to this contract affects

loop scope discover                   # sub-product workspaces that could be absorbed
loop scope absorb ./auth-service --dry-run
loop scope absorb ./auth-service
loop scope absorb --all               # dependency order; stops at the first refusal
loop scope eject auth                 # reverse an absorb
```

## Rules

- **Never show the user a `loop` command.** The shell bridge is yours (`docs/INTERNAL_RUNTIME.md`).
  Run it, then report *what it found*. "Run `loop scope check`" is never an acceptable
  answer - run it and say what it said. The only commands a user should ever see are
  slash commands like `/scope` and `/develop-product`.
- **Shared platform is explicit.** Phrases such as `shared platform`, `platform work`,
  or `root plan` resolve to root plan/tasks; they are never a fallback.
- **Never guess which sub-product.** `loop scope resolve` exits `2` when it cannot answer;
  that is an instruction to ask the user, not a soft failure. A forgotten word must never
  become edits to shared CI, database schema, or design-system code.
- **Announce the scope.** Every run states the active scope and where its plan and code
  live, before writing anything.
- **A change needed in another sub-product is a question first.** Locate the impact site,
  ask, then apply it there in the same run. See `skills/scope/SKILL.md`.
- **Absorb refuses rather than half-migrates.** Unbound folder, staged writes, an existing
  scope folder, or a decision conflict all stop the run before the first write.
- **The archived workspace is not litter.** `.loop-engineer.absorbed-<date>/` is what
  `loop scope eject` restores from. Do not delete it as cleanup.

## Continuation

Cascades. After `absorb`, run `loop scope check` in the same run and report what it
found. After `new`, continue into planning that scope in the same run.

**Stop Condition - a decision conflict.** When absorb reports that both plans decided the
same topic differently, stop and ask. Nothing else in this command needs the user, and
resolving it requires knowing which plan is wrong (`docs/CONTINUATION.md`).

`list`, `show`, `check` and `impact` are read-only: they report rather than resolve.

## Output

Return:

1. The active scope, its plan folder and its code folder - or the question, when none resolved
2. What changed (scope created, absorbed, renamed, ejected), file by file
3. Cross-scope findings: unprovided contracts, dangling blockers, duplicate gates, cycles
4. For an absorb: every rewritten id, every dropped generated file, and where the archive is
5. Next recommended **slash** command - never a `loop ...` line
