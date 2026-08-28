# /product-tree

Show the sub-products this workspace holds as scopes: their plan state, how they depend on each other, and where a contract or task reference is unsatisfied.

## How To Interpret

If the user says `/product-tree`, `product tree`, `show sub products`, `how do my products link`, `is my sub product plan aligned`, or asks why a sub-product's plan differs from the main plan, execute this file directly.

## Required Reads

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read product-state files in the **active unified workspace** (local `.loop-engineer/` auto-detected from cwd).

1. `AGENTS.md`
2. `skills/product-tree/SKILL.md`
3. `plan/SESSION_MANIFEST.md`
4. `plan/products/*/scope.json`
5. `plan/PRODUCT_MAP.md`
6. `plan/main_plan.md`
7. `DECISIONS.md`
8. `DOUBTS.md`

## Loop

```text
SESSION-START -> RESOLVE SCOPE -> LIST DEPENDENCIES -> CHECK CONTRACTS -> RECOMMEND NEXT COMMAND
```

## Scripts

```bash
loop scope list                     # sub-products, in dependency order
loop scope check                    # contracts, dangling refs, cycles
loop workspace tree                 # this workspace and the scopes it holds
```

## Rules

- **Read-only.** Reporting is this command's product; changes belong to `/scope` or `/revise-plan`.
- Sub-products are scopes discovered under `plan/products/` and bound by `scope.json.map_id`.
- A legacy product folder with its own `.loop-engineer/` is only an absorb candidate;
  do not report it as a second live plan workspace.

## Continuation

**Read-only - deliberately does not cascade.** Reporting the tree and naming the next
command *is* this command's product - it is read-only by design, so it reports rather
than resolves. When a contract or binding needs resolving, hand off to
`/scope` (to fix a contract or binding) or `/plan-loop` (to correct the master plan). See the
read-only exemption in `docs/CONTINUATION.md`.

## Output

Return:

1. Platform root and selected scope, if any
2. Scope table: map row, plan/code folder, status, gate, task, and open doubts
3. Dependency order and cycles
4. Contract findings and their affected providers/consumers
5. Next recommended command
