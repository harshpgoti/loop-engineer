# Agent-development capability catalog

Read only the capability rows selected in `plan/AUTO_AGENT_SKILLS.md`. The stage order is the
default execution order, not permission to perform external or destructive actions.

| Capability | Stage | Use when | Required outcome |
|---|---|---|---|
| `agentic-engineering` | plan | any agent product | eval-first work units with one risk and one done condition |
| `agent-sort` | plan | the loaded surface is too broad | evidence-backed always-loaded versus on-demand set |
| `council` | plan | several defensible choices exist | raw positions, strongest dissent, verdict, evidence log |
| `council-multi-model` | plan | high-consequence decision needs external critique | minimal review packet, explicit transfer consent, labeled critique |
| `recursive-decision-ledger` | plan | repeated rollouts or high-dimensional search | visible candidates, coherence marks, promotion reason |
| `token-budget-advisor` | plan | the user supplied a token budget | task allocation that preserves verification and closeout |
| `agent-harness-construction` | harness | tools or observations are being designed | bounded action space, schemas, validated observations, error contract |
| `agentic-os` | harness | persistent commands, roles, schedules, or state | small kernel, role registry, routing table, state ownership |
| `dynamic-workflow-mode` | harness | next step depends on runtime output | task-local state machine and eval gates |
| `autonomous-agent-harness` | harness | scheduled/computer-use/task-queue operation | consent boundaries, persistent queue, completion verification |
| `agent-payment-x402` | harness | an agent must make a payment | human-set per-task budget, pinned dependency, non-custodial boundary |
| `team-builder` | orchestrate | a task genuinely benefits from parallel roles | minimum team, explicit ownership, no duplicate assignment |
| `dev-team` | orchestrate | PM/architecture/build/QA perspectives are requested | bounded independent positions plus synthesis |
| `team-agent-orchestration` | orchestrate | an agent squad executes work | work items, ownership, Kanban state, control-pane handoffs |
| `ralphinho-rfc-pipeline` | orchestrate | an RFC decomposes into dependent work | DAG, unit specs, isolated branches, ordered merge queue |
| `continuous-agent-loop` | orchestrate | work repeats until a measurable condition | bounded loop, eval gate, recovery path, completion predicate |
| `autonomous-loops` | compatibility | old plans use the former name | route to `continuous-agent-loop` without loading duplicate guidance |
| `gan-style-harness` | evaluate | generator/evaluator iteration is justified | independent rubric, threshold, maximum iterations, escalation |
| `eval-harness` | evaluate | any behavior-changing agent work | predeclared capability/regression cases and deterministic graders first |
| `agent-eval` | evaluate | comparing agent configurations or harnesses | isolated tasks; pass rate, consistency, time, and cost |
| `agent-self-evaluation` | evaluate | substantial output needs a self-check | evidence-backed five-axis scorecard followed by one improvement pass |
| `santa-method` | evaluate | two independent passes are required | two isolated reviews; both pass or bounded correction loop |
| `agent-architecture-audit` | audit | pre-release or failing layer is unknown | evidence across model, wrapper, prompts, tools, memory, transport, UI |
| `agent-introspection-debugging` | recover | an agent run fails | captured failure, hypothesis, contained recovery, introspection report |
| `enterprise-agent-ops` | operate | long-lived production workload | observability, least privilege, lifecycle, SLOs, incident and rollback plan |
| `unified-memory` | memory | state must survive tools or sessions | scoped durable record, provenance, retention, correction precedence |
| `continuous-learning-v2` | learn | repeated sessions reveal reusable behavior | atomic project-scoped learning with evidence and confidence |
| `continuous-learning` | compatibility | old plans use the former name | route to `continuous-learning-v2`; do not maintain a second learner |
| `context-budget` | compact | context growth needs an audit | inventory, duplicate detection, prioritized reductions |
| `strategic-compact` | compact | a phase boundary approaches the context limit | durable summary preserving decisions, evidence, state, and next action |

## Evaluation rules

Prefer deterministic graders, then model graders for semantics, then human review for judgment
that cannot be made reliable mechanically. Track both `pass@k` (can it succeed at least once?)
and `pass^k` (does it succeed consistently?) when reliability matters. Never tune only against
the golden set; keep held-out regression cases.

## Recovery rules

Capture the input, state, tool transcript, output, failing assertion, and environment before
changing anything. Map the failure to the earliest responsible layer. Retry only when the
failure is transient and the retry budget permits it; otherwise change the hypothesis or stop.
