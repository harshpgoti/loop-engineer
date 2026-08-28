# /plan-loop

Run Step 1: initialize product planning, validation, grilling, evidence, PRD, architecture, and development instructions.

## How To Interpret

If the user says `/plan-loop`, `/plan-loop <idea>`, `/startup-discovery-loop`, `plan`, or describes a product idea, execute this file directly. Do not ask for `AGENT_BOOT_SEQUENCE.md`.

**User types only the idea.** Loop Engineer auto-detects scale, decomposes modules, and routes ultraplan - no manual scale/decompose commands.

## Public invocation

```text
/plan-loop <user's full product idea>
```

The coding agent invokes the internal session runtime, then reads
**`plan/PLAN_BOOTSTRAP.md`** before other plan reads. Users do not run the runtime
command separately.

Advanced (agent-only, not for users): `loop plan-loop scale`, `loop plan-loop decompose`, `loop plan-loop ultraplan next`.

## Scope resolution (unified workspaces)

When this workspace plans sub-products as scopes (`plan/products/` exists), decide **which
sub-product** this run is about before reading a plan or writing a file. You run this,
not the user:

```bash
loop scope resolve --text "<exactly what the user typed>" --session "<session id>" --remember
```

- Exit `0` - print the returned `banner`, then read and write only inside `plan_dir` and
  `code_dir`.
- Exit `2` - **ask the user which sub-product**, listing the returned candidates plus
  "shared platform work". Do not proceed on a guess, and never treat an unnamed scope as
  platform work.

A change this run needs in a *different* sub-product: locate it (`loop scope impact
<contract-id>`), ask the user with the specific change named, and apply it there on their
yes. See `skills/scope/SKILL.md`.

A workspace with no scopes skips this entirely and behaves exactly as before.

## Required Reads

Plus `skills/scope/SKILL.md` whenever `plan/products/` exists.

Read command/skill files from the tool app (`~/.loop-engineer/app/` or your clone). Read and write product-state files in the **active workspace** (local `.loop-engineer/` auto-detected from cwd, else `~/.loop-engineer/data/`). See `docs/DATA_LAYOUT.md`.

1. `AGENTS.md`
2. `memories/SOUL.md`
3. `memories/USER.md`
4. `memories/MEMORY.md`
5. `CONTEXT.md`
6. `DOUBTS.md`
7. `skills/plan-loop/SKILL.md`
8. `skills/plan-loop/phases/ultraplan.md`
9. `skills/session-lifecycle/SKILL.md`
9. `skills/feature-workflow/SKILL.md`
10. `skills/plan-loop/phases/spec-clarify.md`
11. `skills/plan-loop/phases/spec-checklist.md`
12. `skills/plan-loop/phases/council.md`
13. `skills/plan-loop/phases/grill.md`
14. `skills/plan-loop/phases/task-compiler.md`
15. `skills/deployment-plan/SKILL.md`
16. `skills/compact-loop/SKILL.md`
17. `skills/memory-review/SKILL.md`
18. `plan/main_plan.md`
19. `plan/` and `plan/step_*.md`
20. `.loop/active-feature.json` (when present)
21. `plan/SESSION_MANIFEST.md`
22. `plan/SESSION_RECALL.md`
23. `CURRENT_STATE.md`
24. `TASKS.yml`
25. `GATES.yml`
26. `HANDOFF.md`

Read **on demand**, not every session - both are append-only records that grow without
bound, and the manifest's `PHASE:` block names the skills the current phase needs:

- `DECISIONS.md` - when checking or recording a decision. Rationale for settled ones is
  in `plan/archive/DECISIONS_DETAIL.md`.
- `EVIDENCE_LOG.md` - when sourcing or checking a claim. Every `E-*` id still resolves
  there; settled sourcing is in `plan/archive/EVIDENCE_SETTLED.md`
  (`loop archive --search "<term>"`).

Product-state files (`plan/main_plan.md`, `plan/`, `memories/MEMORY.md`, `TASKS.yml`, etc.) must come from the product workspace, not from the reusable `loop-engineer/` repo.

## Loop

```text
SESSION-START â†’ RECALL â†’ PLAN â†’ GRILL â†’ EVIDENCE â†’ PRD â†’ ARCHITECTURE â†’ FEATURE SPEC â†’ TASKS â†’ SESSION-END
```

## Cycle checklist (all plan features)

| Step | Feature | Command / script |
|------|---------|------------------|
| Start | Session lifecycle | `loop session-start --command /plan-loop --text "<idea>"` |
| Hierarchy | Assimilate parent context | Automatic sync; accepted findings are folded into this workspace's plan/spec/tasks |
| Bootstrap | **Auto plan from idea** | `plan/PLAN_BOOTSTRAP.md` (scale + map + ultraplan route) |
| Bootstrap | Recall + manifest | `plan/SESSION_MANIFEST.md`, `SESSION_RECALL.md` |
| Plan | Product grill + council | `product-grill`, `product-council` |
| Plan | Step plan | `plan/step_XX_*.md` (index; ultraplan for platform) |
| Plan | Feature spec | `loop feature new` â†’ `/spec-clarify` â†’ `/spec-checklist` â†’ `feature-plan.md` |
| Plan | Tasks | `task-compiler` â†’ `tasks.md` + `TASKS.yml` |
| Plan | Deployment | `deployment_plan.py --source plan` |
| Plan | Validate | `validate_outputs.py` |
| End | Memory + compact | `memory review`, `/compact-loop` if long |
| End | Session lifecycle | `loop session-end --command /plan-loop` |

Session start/end automatically sync the tree; closeout also converges an active feature.
Never ask the user to run `/feature-converge` between planning steps.

## Always-on lifecycle (first and last step)

```bash
loop session-start --command /plan-loop --tool "<tool>"
```

Read `plan/SESSION_MANIFEST.md` before other required reads.

At closeout (after memory/handoff updates):

```bash
loop session-end --command /plan-loop --summary "<progress>"
```

```text
RECALL â†’ DETECT INIT â†’ ASK/INFER (PRODUCT + DEPLOYMENT) â†’ GRILL â†’ COUNCIL â†’ RESEARCH â†’ PLAN â†’ COMPILE TASKS â†’ DEPLOYMENT PLAN DRAFT â†’ VALIDATE â†’ MEMORY â†’ MEMORY REVIEW â†’ COMPACT IF NEEDED
```

## Steps

0. **Session start + auto-bootstrap** (pass the user's idea as `--text` only when
   `plan/main_plan.md` is missing or `UNINITIALIZED`; on an initialized plan the text
   is routing context and must not rewrite `IDEA.md` or `PRODUCT_MAP.md`):
   ```bash
   loop session-start --command /plan-loop --tool "<tool>" --text "<user product idea>"
   ```
   Read `plan/PLAN_BOOTSTRAP.md` then `plan/SESSION_MANIFEST.md`. Do **not** ask the user to run scale/decompose/ultraplan manually.
1. **Detect initialization.** If `plan/main_plan.md` says `Status: **UNINITIALIZED**`, initialize the user's product plan.
2. **Ask for required product inputs:** product name, target user, problem, first product step, constraints, sensitive data, preferred stack.
3. **Ask for deployment inputs during planning:** cloud provider, single vs multi-cloud, primary region(s), compute model, database hosting, LLM provider/model, embedding model, agent runtime, CI/CD platform, secrets management. Use `templates/plan_deployment_questions.md` as the checklist.
4. **Reuse prior answers** from `DECISIONS.md`, resolved `DOUBTS.md`, or existing `plan/main_plan.md` â†’ **Deployment & Infrastructure**. Inform the user when reusing; do not ask again unless they want to change something.
5. **If the user is unavailable**, record missing inputs in `DOUBTS.md` and do not invent product-specific facts.
6. **Restate current product state** from `memories/MEMORY.md` and `plan/main_plan.md`, not from chat memory.
6a. **Settle cross-sub-product contracts.** Run the cross-scope check; an unprovided or still-draft contract another scope is building against is a planning question, not a build-time surprise. See `skills/scope/SKILL.md`.
7. **Review open doubts** with `loop doubts ask` - blocking doubts only, each with its recorded `Default if unavailable` as the recommended answer. Record answers with `loop doubts resolve <id> "<answer>"` or `loop doubts defer <id> "<reason>"`; never hand-edit the status. If the user is unavailable, defer with a risk note and continue only safe planning work.
8. **Grill the plan** using:
   - first customer ICP
   - buyer and budget
   - real data access
   - compliance path
   - wedge sharpness
   - evidence quality
   - cloud/deployment fit
   - tech stack finalization (runtime, frameworks, datastore, migrations, auth, background work, test runners) - no layer left to a build-time default
   - LLM vendor lock-in and cost
9. **Run `skills/plan-loop/phases/council.md`** before major product or architecture decisions.
10. **Fact-check claims** before decisions. Add sources to `EVIDENCE_LOG.md`.
11. **Update `plan/main_plan.md`** with product-level strategy and the **Deployment & Infrastructure** table. Use `templates/main_plan.template.md` on first initialization.
12. **Follow `plan/PLAN_BOOTSTRAP.md`** for scale branch (already auto-detected):
    - **`convenient`:** one step file + feature spec (steps 15-17).
    - **`platform`:** ultraplan the step named in bootstrap (one step per session), then
      run that step through feature spec, clarification, checklist, doubts, and task compilation.

## Plan scale branch (automatic - do not ask user to run manual commands)

### A) `convenient` - single wedge product

Continue with standard step + deep **feature spec** (steps 15-17 below).

### B) `platform` - multiple sub-products / agents

Already bootstrapped: `PRODUCT_MAP.md`, step stubs, and canonical owner folders. **Your job:**
fully plan the step listed in `PLAN_BOOTSTRAP.md` through compiled tasks - one step per session.

13. **Use the initializer when enough product inputs are known** (convenient scale only, or first platform step):
   ```bash
   python scripts/init_product.py --name "<product>" --first-step "<step>" --target-user "<user>" --problem "<problem>" --cloud-provider "<cloud>" --cloud-strategy "<single|multi>" --llm-provider "<provider>" --llm-models "<models>"
   ```
14. **Create or update planning docs** from templates when useful:
   - `templates/prd.template.md`
   - `templates/adr.template.md`
   - `templates/risks.template.md`
   - `templates/metrics.template.md`
15. **Create or update `plan/step_XX_<name>.md`** - for platform scale, the root step file is an **index** only. Deep content lives in `plan/products/<slug>/` for a sub-product and `plan/steps/NN-slug/` for root-owned work. For convenient scale, use `templates/step_plan.template.md` with full PRD, flows, and acceptance criteria.
16. **Create or update active feature spec** (built-in spec-driven workflow):
   ```bash
   loop feature new "<module title>" --step plan/step_XX_<name>.md
   ```
   Fill `plan/features/NNN-slug/spec.md` from the step plan - link, do not duplicate entire step file.
   Run `/spec-clarify` then `/spec-checklist` before locking `feature-plan.md`.
17. **Run `skills/plan-loop/phases/task-compiler.md`** to convert plan into tasks, gates, acceptance criteria, test plan, and sync active feature `tasks.md` with `TASKS.yml`.
18. **Record deployment decisions** in `DECISIONS.md` and unresolved items in `DOUBTS.md`.
19. **Draft `DEPLOYMENT_PLAN.md`** from captured planning decisions:
   ```bash
   python scripts/deployment_plan.py --source plan
   ```
20. **Validate outputs** when product files are initialized:
   ```bash
   python scripts/validate_outputs.py
   ```
21. **Update `DECISIONS.md`** for any strategy or architecture decision.
22. **Update `memories/MEMORY.md`, `DOUBTS.md`, `CURRENT_STATE.md`, `HANDOFF.md`, and `.ai/SESSION_LOG.md`.**
23. **Run `/memory-review` at closeout** (default `--stage` for production workspaces):
   ```bash
   python scripts/memory_curator.py --stage
   loop memory review
   ```
24. **Run `/compact-loop` when planning is long, many files changed, the user may switch tools, or the context is getting heavy.** At minimum, ensure `COMPACT.md` is current before ending a large `/plan-loop` session.
25. **Session end** (mandatory - runs memory-review staging):
    ```bash
    loop session-end --command /plan-loop --summary "<progress>"
    ```

## Output

Return:

1. Plan summary
2. Product grill questions answered/open
3. Evidence added
4. Plan files created/updated
5. Product council verdict
6. Task compiler summary
7. Active feature spec status (`plan/features/`, `.loop/active-feature.json`)
8. Plan scale (`plan/PLAN_SCALE.md`) and ultraplan status if platform
9. Deployment decisions captured/reused and `DEPLOYMENT_PLAN.md` status
10. Gate status
11. Compact status (`COMPACT.md` updated or why not needed)
12. Memory review status (`plan/MEMORY_REVIEW.md`, pending writes if staged)
13. Next command: `/plan-loop`, `/ultraplan-loop`, `/develop-product`, or `/loop-engine`

## Continuation

Terminus: **tasks compiled + go/no-go for build.** Run the phase pipeline end to
end in this session - grill â†’ council â†’ (ultraplan) â†’ spec-clarify â†’ spec-checklist
â†’ resolve-doubts â†’ task-compiler - recomputing the phase after each and loading the
next. Never end a turn telling the user to run the next phase; see
`docs/CONTINUATION.md`.

## Stop Conditions

Stop and ask the user when:

- The product direction changes.
- Sensitive or regulated data is requested before the relevant gate passes.
- A build task would create irreversible architecture.
- Customer evidence is too weak to justify product development.
