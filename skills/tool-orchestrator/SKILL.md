---
name: tool-orchestrator
description: Selects supporting capabilities for the current loop phase in Loop Engineer's own terms - memory synthesis, reusable skills, spec-driven task discipline, role-based review, sandboxed execution, RAG. Use when choosing tools, workflows, evals, memory, sandboxing, or production agent patterns.
---

# Tool Orchestrator

## Purpose

Select supporting capabilities for the current loop phase without hard-coding one vendor or agent runtime. Describe what the loop needs functionally; implement it however fits the product's stack. Named external tools/repos for each capability live in `tools/registry.md` - link there, don't re-list names here.

## Capability Map

| Capability | Use In Loop |
|------------|-------------|
| Cross-session memory synthesis | Retrieval, synthesis, gap analysis, citation memory across many sessions - beyond `memories/MEMORY.md`/`state.db` |
| Reusable agent skills | Shared skill patterns, review closeout, handoff - see `skills/agent-builder/SKILL.md` for the product's own skills |
| Spec-driven task discipline | Phased development from idea to build tasks - see `plan/features/`, `skills/plan-loop/phases/task-compiler.md` |
| Skill packaging conventions | Progressive disclosure, portable instructions - the `SKILL.md` frontmatter format Loop Engineer already uses |
| Role-based review | Strategy, PM, design, engineering, QA, security, release perspectives - see `skills/plan-loop/phases/council.md` |
| Sandboxed execution | Long-running or higher-risk agent execution: network policy, resource limits, safer runtime |
| Retrieval-augmented generation | Ingestion, hybrid retrieval, reranking, eval, guardrails - only when retrieval is actually needed |

## Selection Rules

- Use cross-session memory synthesis when the problem is long-horizon context, citations, interviews, or gap analysis.
- Use reusable-skill patterns when the problem is repeatable workflows or review closeout.
- Use spec-driven task discipline when moving from idea to build tasks.
- Use role-based review when separating strategy, PM, engineering, QA, security, and release responsibilities.
- Use sandboxed execution for long-running or higher-risk agent execution.
- Use RAG patterns only when retrieval is needed; do not add RAG to MVP if deterministic parsers solve the job.

## Output

- Capability selected
- Why it helps this phase
- What not to use yet
- Any setup or security caveat

## See also

`tools/registry.md` - the named external tool/repo for each capability above.
