# scripts/

107 top-level scripts. Each is a deterministic Python module called by the chain's commands and lifecycle hooks.

| Script | Purpose |
|---|---|
| `agent_registry.py` | Validate canonical agent roles and their skill/independence contracts |
| `agent_router.py` | Select governed agent roles from command, task, risk, and domain signals |
| `agent_scaffold.py` | Scaffold agent/ (skills, tools, evals, architecture doc) in the product workspace |
| `agent_skill_router.py` | Auto-detect AI-agent-development signals from task and plan context |
| `assurance_findings.py` | Structured assurance findings, baseline deltas, policy verdicts, and SARIF |
| `auto_update.py` | Silent, throttled auto-update of the installed app, run at session-start |
| `automation_audit.py` | Audit every automation the chain runs |
| `bench_history.py` | Append and diff chain benchmarks over time |
| `build_phase.py` | Deterministic build-phase router for /develop-product |
| `capabilities.py` | Inspect and validate Loop's capability registry and install profiles |
| `chain_bench.py` | Chain benchmark: measure the chain's own behaviour over time |
| `chain_catalog.py` | Chain catalog: a single command that emits the full chain surface as one |
| `cloud_inventory.py` | What this product has actually created in a cloud account, and why |
| `codehealth.py` | Code-health snapshot for the active workspace |
| `command_audit.py` | Audit the chain's command files for canonical-template compliance |
| `compact_context.py` | Create a durable COMPACT.md summary for long-running product loops |
| `contracts.py` | Cross-scope interfaces: one provider, many consumers, checked deterministically |
| `dashboard.py` | Build a self-contained HTML dashboard from a YAML spec |
| `dependency_ledger.py` | What a sub-product has *declared* about the modules it depends on |
| `deployment_plan.py` | Create or refresh DEPLOYMENT_PLAN.md from product decisions and open deployment questions |
| `deployment_topics.py` | Shared deployment topic definitions and helpers for planning and release workflows |
| `detect_workspace.py` | Detect candidate product workspaces |
| `dev.py` | Stack-agnostic developer-experience commands |
| `doctor.py` | Health-check the Loop Engineering OS runtime and active product workspace |
| `domain_skill_router.py` | Select domain skills from deterministic workspace and task signals |
| `doubts.py` | One parser for DOUBTS.md, so every command agrees what is open |
| `eval_suite.py` | The evals loop: recorded runs, regressions, and error analysis that decides what next |
| `event_store.py` | Append-only, idempotent Loop lifecycle event store with payload redaction |
| `evidence_review.py` | When a recorded claim stops being trustworthy, which is not when its file changes |
| `execution_backends.py` | Portable session backend adapters used by the Loop execution plane |
| `execution_cli.py` | Internal CLI for one durable, isolated local execution worker |
| `execution_runtime.py` | Durable, worktree-isolated execution runs for compiled Loop tasks |
| `execution_schemas.py` | Dependency-free deterministic validators for durable execution records |
| `execution_supervisor.py` | Persistent local supervisor lifecycle for durable queued worker dispatch |
| `feature_converge.py` | Compare active feature spec/plan/tasks against TASKS.yml and repo signals |
| `feature_paths.py` | Feature spec paths and active-feature resolution |
| `fog.py` | What the plan knows it does not know yet |
| `freshness.py` | Is a generated file still true of the files it was generated from? |
| `frontend_scope.py` | Resolve the active scope's frontend code roots in a unified workspace |
| `frontend_skill_router.py` | Auto-select built-in and external frontend skills from task and plan context |
| `glossary.py` | The product's own words, and where the plan stops using them |
| `graph_index.py` | One index of how a workspace's records reference each other |
| `graph_schema.py` | What must be true of the reference graph, checked deterministically |
| `grill.py` | The Grill: structured interview for /plan-loop |
| `harness_adapters.py` | Load the declarative coding-harness capability registry |
| `harness_catalog.py` | Harness catalog: consolidate per-coding-agent harness JSON files into one view |
| `hierarchy_drift.py` | Deterministic drift checks between a main product plan and its sub-products |
| `import_agent_development_skills.py` | Import and adapt the approved agent-development skill pack |
| `import_scanner.py` | Scan a folder of another tool's arbitrary data/memory files and route each |
| `init_product.py` | Initialize product-specific planning files from templates |
| `install_skills.py` | Install thin router skills into every coding agent, pointing at the installed app |
| `iterative_retrieval.py` | Three-round iterative retrieval against a corpus |
| `learning_candidates.py` | Govern repeated observations without silently rewriting skills or rules |
| `living_docs_audit.py` | Living-docs drift detection |
| `local_process_runner.py` | Own one worker child and expose durable file-based stop/exit control |
| `loop_cli.py` | Unified loop CLI for Loop Engineering OS |
| `loop_home.py` | Loop Engineer home directory and path resolution |
| `loop_update.py` | Update Loop Engineer app runtime without touching product memory |
| `memory_curator.py` | Curate bounded memory files and detect drift |
| `memory_paths.py` | Resolve product memory file paths with backward-compatible fallbacks |
| `migrate_import.py` | Import memory and skills from an external agent workspace into Loop Engineer |
| `migrate_legacy_layout.py` | One-time migration: move an existing flat Loop Engineer layout into the new |
| `migrate_workspace.py` | Apply safe product-workspace migrations as Loop Engineering OS evolves |
| `new_feature.py` | Create a numbered feature spec folder and set it as active |
| `pending_writes.py` | Queue for writes that need a human decision |
| `plan_extract.py` | Extract sub-product / agent modules from free-text product ideas |
| `plan_idea.py` | One-shot plan bootstrap from a user's product idea (auto scale + ultraplan route) |
| `plan_paths.py` | Paths and constants for plan scale and ultraplan harness |
| `plan_phase.py` | Deterministic planning-phase router for the plan-loop orchestrator |
| `plan_scale.py` | Detect whether a product idea is convenient (single wedge) or platform-scale |
| `prod_gap.py` | Create a structured product gap analysis draft in plan/PROD-GAP.md |
| `release_check.py` | Run a focused pre-production release readiness check |
| `research_search.py` | Search public research-paper sources: arXiv, Research Square, SSRN |
| `roles_list.py` | List the Loop Engineer chain's roles with class, model, skills, and handoffs |
| `runtime_update.py` | Recoverably update the globally installed Loop runtime checkout |
| `safeguard_hook.py` | E7 hook: apply the Prompt Defense Baseline to every tool call |
| `scope_absorb.py` | Fold a sub-product's own `.loop-engineer/` workspace into the main product as a scope |
| `scope_cli.py` | `loop scope ...` - the runtime every scope-aware command calls |
| `scope_layout.py` | One layout for every sub-product, checked rather than assumed |
| `scope_paths.py` | Product scopes: one workspace, many sub-products |
| `scope_readiness.py` | Whether this product's sub-products are ready, for /status, /prod-gap and /release-check |
| `scope_state.py` | Tasks, gates and doubts unioned across the platform and every scope |
| `self_audit.py` | Self-audit the Loop Engineer chain's own state |
| `session_lifecycle.py` | Always-on session lifecycle: start recall + end memory review (tool-agnostic) |
| `session_recall.py` | Recall relevant past sessions at loop start and write plan/SESSION_RECALL.md |
| `session_search.py` | Search past Loop Engineering OS sessions stored in workspace state.db |
| `session_store.py` | SQLite session store with FTS5 search for past session recall |
| `setup_loop_engine.py` | First-time setup for Loop Engineering OS |
| `setup_options.py` | Shared setup helpers for local vs global product memory layout |
| `skill_audit.py` | Audit every canonical skill against the shared operating contract |
| `skill_list.py` | List the Loop Engineer chain's skills with class, capability, and reachability |
| `skill_resolver.py` | Resolve canonical vs user skills with product-workspace priority |
| `source_tree_scan.py` | Shared source-tree checks for production readiness scripts |
| `state_archive.py` | Shrink finished work in place, without letting the plan forget it happened |
| `status.py` | Write a quick STATUS.md snapshot for the active product workspace |
| `supervisor_process.py` | Background loop for the persistent local execution supervisor |
| `sync_loop_state.py` | Reconcile product-loop state files and report drift |
| `task_context.py` | The slice of build state one task actually needs |
| `team_init.py` | Team mode: commit a path-free bootstrap so teammates get Loop automatically |
| `ultraplan_harness.py` | Platform-scale ultraplan harness: decompose, init deep step packs, track status |
| `upgrade_loop_engineer.py` | Safely copy Loop Engineering OS tool files into a product workspace |
| `validate_outputs.py` | Validate product-loop outputs after /plan-loop or /develop-product |
| `validate_template.py` | Validate the Loop Engineering OS template before publishing |
| `workspace_registry.py` | Register and switch product workspaces |
| `workspace_resolver.py` | Resolve product workspace: local folder vs global ~/.loop-engineer data |
| `workspace_tree.py` | Product hierarchy: a main product workspace and its sub-product workspaces |
| `workspace_utils.py` | Shared workspace helpers for Loop Engineering OS scripts |

## Conventions

- Every script reads its inputs from `sys.argv` and `--workspace` (where applicable).
- Every script writes to the workspace, never to the LE app repo (except diagnostics and benchmarks).
- Every script imports the canonical `app_root = Path(__file__).resolve().parents[1]` and uses it for `manifests/`, `skills/`, `commands/`, `harnesses/`.
- Every script has a test in `test_<name>.py` if its logic is non-trivial.

## Conventions for new scripts

When you add a new script:
1. Add a one-line docstring at the top of the file: `\"\"\"Run X for Y.\"\"\"`.
2. Add it to the right capability in `manifests/capabilities.json` (if it backs a public command).
3. Run `python scripts/_index.py` (this file) to regenerate this index.
4. Add a `test_<name>.py` covering the happy path and one error path.
5. Run `python -m unittest discover -s scripts -p "test_*.py"`.

