# Loop Supervisor Architecture Plan

**Status:** Phases 0-5 and the beneficial local Phase 6 scale slice implemented  
**Research baseline:** initial external review at `bca584a840011079a121fe965a222eb5a3578408`, refreshed at `1fd7ea289b7a4c23a1fd9474680ed2facd6b7dd1`  
**Purpose:** add a harness-independent execution plane beneath Loop's existing
planning, evidence, scope, task, gate, and memory control plane.

## Outcome

Keep Loop as the product-development authority. Add a deterministic supervisor
that can turn compiled Loop tasks into bounded worker runs, isolate those runs,
observe them without spending model turns, and accept, merge, or tear them down
only after Loop's existing gates pass.

```text
user
  |
  v
Loop supervisor
  |-- plan / evidence / scopes / doubts / tasks / gates
  |-- task intake and dependency scheduling
  |-- worker brief + lease
  |-- review and human authority
  |
  +--> delivery run   --> isolated worktree --> diff/tests/review --> PR or local merge
  +--> research run   --> isolated worktree --> cited report ------> plan/evidence
  +--> validation run --> read-only diff     --> verdict ----------> gate transition
```

The supervisor is an execution role, not another source of product truth. Product
truth remains in `.loop-engineer/`; worker state is derived from a compiled task
and reconciled back into that workspace.

## Evidence reviewed

Primary source files inspected at the pinned commit:

- `README.md` and `docs/architecture.md`: agent-distro model, task shapes,
  event-driven supervision, worktree isolation, delivery modes, restart recovery.
- `AGENTS.md`: the reference implementation's user-authority model, project read-only boundary, dispatch and memory
  ownership rules.
- `.agents/skills/harness-adapters/SKILL.md`: empirically verified differences
  across Claude, Codex, OpenCode, Pi, Grok, Kimi, Cursor, and Muse.
- `bin/fm-brief.sh`: immutable task identity, delivery contract, worker status
  protocol, and separate implementation/investigation definitions of done.
- `bin/fm-spawn.sh`: task locks, clean/fresh worktree gate, harness/backend
  selection, environment sanitization, launch verification, and relaunch rules.
- `bin/fm-watch.sh`, `bin/fm-crew-state.sh`: durable wake queue and semantic
  liveness classification.
- `bin/fm-send.sh`, `bin/fm-control.sh`: durable steering and recovery rather
  than fragile terminal typing alone.
- `bin/fm-pr-check.sh`, `bin/fm-pr-merge.sh`, `bin/fm-merge-local.sh`: current-head
  verification and explicit merge authority.
- `bin/fm-teardown.sh`: fail-closed proof that work is landed before cleanup.

These are architectural observations, not a dependency decision. Loop will not
vendor the reference implementation or require its shell scripts.

## Current Loop strengths to preserve

| Existing Loop capability | Keep as authority |
|---|---|
| `plan/products/<slug>/` scopes and contracts | Product decomposition and ownership |
| `TASKS.yml` and task compiler | Work definition and dependency graph |
| `GATES.yml`, doubts, evidence, compliance | Readiness and human approval |
| `state.db`, session lifecycle, handoff, memory | Cross-session durability |
| `/develop-product` continuation contract | End-to-end task convergence |
| separate code-reviewer role | Builder cannot approve its own work |
| centralized skills and harness adapters | Portable public interface |

Loop should not introduce a second backlog, second gate model, or second memory
database. Worker records must reference the existing scope and task IDs.

## Gaps

| Gap | Consequence today | Required seam |
|---|---|---|
| No durable worker identity | Agent runs cannot be safely resumed or reconciled | Worker registry |
| No compiled worker brief | Context and authority can drift between agents | Brief compiler |
| No mandatory worktree isolation | Parallel edits can collide | Workspace provider |
| No worker lease/lock | Duplicate workers may execute one task | Lease manager |
| No structured event protocol | Status depends on chat or harness UI | Append-only event log |
| No semantic liveness model | A quiet pane can look complete or wedged | Worker state fold |
| No harness launch contract | Model/effort/trust behavior is scattered | Harness adapter |
| No runtime backend interface | tmux/terminal assumptions leak upward | Session backend |
| No fail-closed teardown proof | Unlanded work can be orphaned | Teardown verifier |
| No explicit research lifecycle | Research and implementation share unsafe semantics | Run-kind contract |

## Target state layout

```text
<workspace>/.loop-engineer/
  workers/
    registry.json
    <worker-id>/
      meta.json
      brief.md
      events.jsonl
      inbox/
      handled/
      report.md            # research run only
      review.json          # validation run only
  locks/
    task-<task-id>.lock
  plan/
  TASKS.yml
  GATES.yml
  state.db
```

`meta.json` should include schema version, worker ID, task ID, scope, kind,
harness, backend, repository, worktree, base commit, branch, lease generation,
created time, and delivery mode. Never store credentials or prompt transcripts.

`events.jsonl` is append-only. Minimum event vocabulary:

```text
created, launched, working, waiting_external, blocked, checkpoint,
tests_passed, review_ready, pr_ready, report_ready, failed, stopped, torn_down
```

Every row carries worker ID, lease generation, monotonically increasing sequence,
timestamp, event type, and a bounded public-safe summary. The generation prevents
events from an old worker incarnation being accepted after relaunch.

## Deep modules and interfaces

### 1. Worker registry

Small interface: `create`, `get`, `append_event`, `fold_state`, `close`.
It owns schemas, atomic writes, sequence validation, lease generation, and
recovery. SQLite may index records later, but JSON/JSONL is the first durable
format because it is inspectable and easy to repair.

### 2. Brief compiler

Compiles one existing `TASKS.yml` entry plus scope plan, acceptance criteria,
gate state, authority, and relevant decisions into an immutable brief. Spawn
refuses if the brief's task, scope, kind, or delivery mode disagrees with the
requested launch.

### 3. Workspace provider

Interface: `allocate(task)`, `verify(worker)`, `release(worker)`.
The first adapter uses native `git worktree`; Treehouse or Orca can be optional
future adapters. Allocation refuses dirty/unfetchable bases and verifies the
worker is not in the primary checkout.

### 4. Harness adapter

Interface: `preflight`, `launch_spec`, `send`, `interrupt`, `stop`, `probe`.
Use the existing declarative harness registry for discovery, invocation, trust,
hooks, model/effort support, and environment markers. Keep live-version evidence
separate from generic workflow logic.

### 5. Session backend

Interface: `create_endpoint`, `send`, `capture`, `process_state`, `destroy`.
Start with a portable subprocess backend. Add tmux only after lifecycle contracts
pass. GUI backends, SSH second-level supervisors, and terminal-composer scraping
are deferred.

### 6. Supervisor

Consumes compiled tasks, leases eligible work, spawns workers, folds events,
raises actionable decisions, dispatches independent review, and advances Loop
gates. It never edits product code and never grants its own merge approval.

### 7. Teardown verifier

For delivery runs, teardown requires a clean worktree and proof that every worker
commit is reachable from an accepted local target or verified remote PR head.
For research runs, it requires a durable report and decision inventory. Ambiguity
refuses cleanup.

## Run kinds and authority

### Delivery run

- May edit only its isolated worktree.
- Must satisfy the compiled acceptance criteria.
- Produces a branch plus test evidence.
- Requires a separate reviewer verdict.
- Merge follows the task's explicit delivery mode and human gate.

### Research run

- Investigation only; never pushes or merges.
- Writes a cited report and decision inventory.
- Findings reconcile into `EVIDENCE_LOG.md`, doubts, decisions, or tasks through
  the supervisor—not directly into product truth.

### Validation run

- Read-only over the candidate diff and test output.
- Reports Spec and Standards independently using Loop's existing reviewer skill.
- Cannot modify the candidate branch or approve its own implementation.

## Phased delivery plan

### Implementation verification

| Phase | Implemented evidence |
|---|---|
| 0 | JSON schemas, dependency-free validators, golden failure fixtures, ADR 0001 |
| 1 | Registry, immutable brief hash, native worktree provider, subprocess backend, lifecycle CLI |
| 2 | Cited research report/reconciliation and detached read-only validation runs bound to base/head |
| 3 | Ordered inbox acknowledgement, idempotent events/actions, semantic liveness, generation relaunch |
| 4 | Harness interface, pinned executable preflight, generated matrix, local and optional tmux backends |
| 5 | Local-only/direct-PR/gated-pipeline modes, GitHub exact-head/check verification, approval-gated merge, journaled task/gate reconciliation |
| 6 | Persistent local supervisor and quota/dependency-aware priority dispatch implemented; remote workers, GUI scraping, and public relay remain evidence-gated |

### Phase 0 — contracts and fixtures

1. Specify worker, brief, event, adapter, lease, and teardown schemas.
2. Add golden fixtures for delivery, research, validation, relaunch, stale generation,
   dirty worktree, and unlanded commit cases.
3. Add an architecture decision recording product truth versus execution state.

**Gate:** schemas validate deterministically; no process or worktree creation yet.

### Phase 1 — single-worker local execution

1. Implement worker registry and brief compiler.
2. Implement native Git worktree provider.
3. Implement subprocess backend and one Codex/Claude-neutral pointer launch.
4. Add `loop worker spawn|status|events|stop|teardown` internal commands.
5. Run one delivery task at a time; no automatic merge.

**Gate:** crash/restart preserves identity; duplicate task spawn is refused;
primary checkout cannot be used as a worker worktree.

### Phase 2 — research and independent validation

1. Add research-report contract and evidence reconciliation.
2. Add validation-run kind with read-only candidate access.
3. Require a validation verdict before a delivery task can become merge-ready.
4. Bind verdict to exact base/head commits so later changes invalidate it.

**Gate:** builder cannot approve itself; stale reviews are rejected.

### Phase 3 — event-driven supervision

1. Add worker inbox and append-only event protocol.
2. Implement the semantic state fold and durable actionable queue.
3. Add bounded heartbeat/wedge detection without terminal-screen heuristics.
4. Add generation-bound relaunch and idempotent acknowledgement.

**Gate:** no event is silently lost across supervisor restart; duplicate events
are harmless; old-incarnation events cannot mutate current state.

### Phase 4 — harness and backend expansion

1. Verify Claude, Codex, Pi, Grok, OpenCode, Cursor, and Kimi adapters against
   pinned CLI versions.
2. Add project hooks/extensions only where they improve lifecycle reliability.
3. Add tmux backend after subprocess semantics are stable.
4. Publish a generated compatibility matrix and drift tests.

**Gate:** every advertised adapter passes discovery, launch, delivery, stop,
relaunch, and teardown contracts on its supported platforms.

### Phase 5 — controlled shipping

1. Add explicit `local-only`, `direct-PR`, and gated-pipeline delivery modes.
2. Verify remote PR state and exact head before merge-ready or teardown.
3. Connect Loop human-approval gates to merge commands.
4. Reconcile completed tasks, gates, memory, and handoff atomically.

**Gate:** no merge from stale metadata; no teardown of dirty or unlanded work;
high-risk actions always stop at the existing human gate.

### Phase 6 — optional scale

Consider persistent domain supervisors, remote workers, GUI backends, quota-aware
dispatch, and public relay only after the local execution plane has production
evidence. These are not MVP dependencies.

Implemented where it improves the current chain: the local supervisor persists outside a
chat turn, reconciles on every tick, dispatches only explicitly queued tasks, applies bounded
per-kind quotas, respects task dependencies and priority, detects heartbeat wedges, and has
durable start/status/stop state. It never generates work. Remote credentials, GUI screen
heuristics, and public relay remain deferred until production evidence justifies their larger
security and lifecycle surface.

## What to adopt, adapt, and defer

| Decision | Disposition | Reason |
|---|---|---|
| One user-facing supervisor | Adopt | Reduces coordination burden |
| Delivery/research separation | Adopt | Different authority and deliverables |
| Worktree isolation | Adopt | Prevents concurrent checkout mutation |
| Durable status and inbox | Adopt | Restart-proof and harness-independent |
| Fail-closed teardown | Adopt | Protects unlanded work |
| Explicit delivery mode | Adopt | Prevents workers guessing merge authority |
| Bash screen scraping | Do not adopt | Fragile and poor Windows fit |
| Treehouse requirement | Adapt later | Native Git worktrees are sufficient first |
| tmux as hard default | Do not adopt | Loop must remain Windows/agent portable |
| A separate execution backlog | Do not adopt | `TASKS.yml` is already authoritative |
| Persistent delegated runtimes and remote homes | Defer | Large lifecycle/security surface |
| Social relay | Defer | Outside Loop's core product-development mission |

## Safety and privacy requirements

- Worker briefs contain only task-bounded context; no secrets, regulated data,
  private customer records, or full session transcripts.
- Harness environment sanitization removes foreign identity markers and passes
  credentials only through existing secure provider mechanisms.
- Worker permissions never exceed the task, repository, network, and approval
  policy recorded at intake.
- All external mutations—push, PR creation, merge, deployment, publication, or
  spend—reuse Loop's human-approval gates.
- Locks use owner identity, generation, and bounded stale recovery; age alone
  never proves a lock abandoned.

## Test strategy

Test through the public runtime seams, not internal helpers:

- Registry: crash during append, duplicate sequence, stale generation, recovery.
- Brief: task/scope/mode mismatch refuses before launch.
- Worktree: dirty base, stale base, primary-checkout alias, concurrent allocation.
- Supervisor: duplicate spawn, worker crash, supervisor restart, lost wake retry.
- Review: builder/reviewer identity collision and head-change invalidation.
- Teardown: dirty, uncommitted, committed-unlanded, merged, and research-report cases.
- Harness contracts: discovery, launch, readiness, delivery, interrupt, stop.
- Windows/Linux matrix: path quoting, junction/symlink fallback, process cleanup.

No phase advances on documentation-only assertions. Each harness capability must
have a dated executable verification or be marked unsupported.

## Migration and compatibility

- Existing `/plan-loop`, `/develop-product`, and single-agent operation remain
  unchanged until Phase 1 is explicitly enabled.
- The worker system is opt-in behind a workspace setting during Phases 1–4.
- Existing `TASKS.yml` IDs become worker task references; no task migration.
- Existing `state.db` receives summaries/indexes, while raw worker events stay in
  bounded per-worker files initially.
- Central skill distribution and harness adapter cleanup proceed independently;
  the supervisor consumes the same adapter registry when ready.

## Recommended first implementation slice

Build only Phase 0 and the narrowest Phase 1 vertical slice:

```text
one compiled TASKS.yml item
  -> immutable brief
  -> native Git worktree
  -> one local subprocess worker
  -> append-only events
  -> separate review record
  -> fail-closed teardown
```

Do not begin with tmux, multiple harnesses, automatic PR creation, remote workers,
or background watchers. Those are adapters around the lifecycle; the lifecycle
must first prove restart safety and authority correctness on one portable path.

### Implemented internal interface

The execution plane is exposed through the internal runtime bridge:

```text
loop worker spawn <task-id> --repository <repo> --command-json '<argv>' [--scope <slug>] [--kind delivery|research]
loop worker status [<run-id>]
loop worker events|stop|relaunch|teardown <run-id>
loop worker send|ack <run-id> ...
loop worker actions|ack-action ...
loop worker heartbeat|liveness <run-id> ...
loop worker validation-start|validation-submit <run-id> ...
loop worker research-record|research-reconcile <run-id> ...
loop worker github-evidence|merge-ready|merge-local|merge-github <run-id> ...
loop worker reconcile-product <run-id> --tasks <path> --gates <path>
loop worker compatibility --output <path>
loop worker enqueue|queue|dispatch ...
loop worker supervisor-start|supervisor-status|supervisor-stop|supervisor-tick
```

This remains an internal deterministic bridge. Skills and natural-language workflows are
the public interface; automatic dispatch remains opt-in and no worker grants itself merge
authority.

## Resolved implementation decisions

1. Worker orchestration is opt-in through explicit supervisor invocation.
2. The portable subprocess backend is normative; tmux is optional and advertised only when
   executable preflight succeeds. Harness launch specs stay behind one adapter interface.
3. Active worker events are retained fully. The persistent supervisor is local and restart-safe;
   closed-run compaction and remote supervisors remain evidence-gated scale work.
