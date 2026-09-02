"""Auto-detect AI-agent-development signals from task and plan context.

Mirrors scripts/frontend_skill_router.py's pattern (gather context -> score
signals -> write plan/AUTO_AGENT_SKILLS.md) but for products that are, or
include, an AI agent - not for Loop Engineer's own operational skills.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from skill_resolver import resolve_skill
from workspace_utils import ROOT, resolve_workspace

AGENT_SIGNALS = (
    "ai agent", "an agent", "autonomous agent", "agentic", "llm agent", "coding agent",
    "background agent", "workflow automation", "dynamic workflow", "automate the workflow",
    "chatbot", "copilot", "ai assistant", "voice agent", "support agent", "sales agent",
    "research agent", "cron agent", "agent loop", "tool-calling agent", "tool use agent",
    "multi-agent", "multi agent", "agent swarm", "orchestrator agent", "sub-agent",
)

SHAPE_PATTERNS: dict[str, tuple[str, ...]] = {
    "multi_agent": ("multi-agent", "multi agent", "agent swarm", "orchestrator agent", "sub-agent", "sub agent"),
    "tool_use": ("tool use", "tool-use", "tool calling", "function calling", "tool-calling"),
    "rag": ("rag", "retrieval augmented", "retrieval-augmented", "vector search", "vector store", "embeddings search"),
    "scheduled": ("cron", "scheduled job", "background job", "recurring", "on a schedule", "nightly job"),
    "dynamic_workflow": ("dynamic workflow", "conditional workflow", "branching workflow", "workflow engine", "state machine agent"),
    "chat_interface": ("chatbot", "chat interface", "conversational agent", "assistant ui"),
}

ALWAYS_READ = (
    "skills/agent-builder/SKILL.md",
    "skills/agent-development/SKILL.md",
    "skills/research-search/SKILL.md",
)

# Ordered by the agent-development lifecycle.  The router emits only capabilities
# whose signals match; compatibility names are reported separately so old plans
# keep working without loading obsolete guidance.
CAPABILITY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("agentic-engineering", AGENT_SIGNALS),
    ("agent-harness-construction", ("tool-calling", "tool calling", "function calling", "agent tool", "action space", "observation format")),
    ("agentic-os", ("persistent agent", "agent operating system", "scheduled agent", "long-running agent")),
    ("dynamic-workflow-mode", ("dynamic workflow", "branching workflow", "adaptive", "state machine")),
    ("continuous-agent-loop", ("autonomous agent", "continuous agent", "recurring agent", "scheduled agent", "agent loop")),
    ("team-agent-orchestration", ("multi-agent", "multi agent", "agent team", "agent squad", "kanban")),
    ("team-builder", ("compose agents", "pick agents", "agent team", "agent squad")),
    ("dev-team", ("dev team", "development team simulation", "role-based team", "pm architect developer qa")),
    ("ralphinho-rfc-pipeline", ("rfc", "dag", "merge queue", "worktree")),
    ("gan-style-harness", ("generator evaluator", "generator-evaluator", "iterate until", "quality threshold")),
    ("eval-harness", ("eval", "golden case", "pass@k", "pass^k", "regression")),
    ("agent-eval", ("compare agents", "agent benchmark", "coding agents", "head-to-head")),
    ("agent-self-evaluation", ("self evaluate", "self-evaluate", "scorecard")),
    ("santa-method", ("two reviewers", "dual review", "adversarial review", "check twice")),
    ("agent-architecture-audit", ("audit", "production readiness", "wrapper", "memory pollution")),
    ("agent-introspection-debugging", ("debug agent", "agent failure", "introspection", "retry loop")),
    ("enterprise-agent-ops", ("production agent", "enterprise", "observability", "incident", "sla")),
    ("unified-memory", ("agent memory", "persistent memory", "long-term memory", "agent handoff", "cross-tool memory")),
    ("continuous-learning-v2", ("continuous learning", "instinct", "learn from sessions", "promote skill")),
    ("context-budget", ("context budget", "context window", "context bloat")),
    ("strategic-compact", ("strategic compact", "context limit", "context compaction")),
    ("token-budget-advisor", ("token budget", "token limit", "response budget")),
    ("recursive-decision-ledger", ("rollout", "decision ledger", "stochastic", "local optimum", "ensemble")),
    ("council", ("tradeoff", "go/no-go", "ambiguous decision", "multiple options")),
    ("council-multi-model", ("external critique", "multi-model", "cross-provider review")),
    ("agent-payment-x402", ("x402", "agent payment", "agent wallet", "pay autonomously")),
    ("agent-sort", ("sort skills", "daily skills", "library skills", "trim skills")),
    ("autonomous-agent-harness", ("computer use", "task queue", "self-directing", "scheduled operations")),
)

COMPATIBILITY_ALIASES = {
    "autonomous-loops": "continuous-agent-loop",
    "continuous-learning": "continuous-learning-v2",
}

CONSENT_REQUIRED = {"agent-payment-x402", "council-multi-model"}


def select_capabilities(text: str) -> list[str]:
    """Select ordered, deduplicated capability names from normalized context."""
    selected: list[str] = []
    for name, signals in CAPABILITY_RULES:
        if any(signal in text for signal in signals) and name not in selected:
            selected.append(name)
    return selected


def _read(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]


def gather_context(workspace: Path, extra: str = "") -> str:
    chunks: list[str] = []
    from memory_paths import main_plan_file

    chunks.append(_read(main_plan_file(workspace)))
    for name in ("HANDOFF.md", "DECISIONS.md", "CONTEXT.md", "TASKS.yml"):
        chunks.append(_read(workspace / name))
    plan_dir = workspace / "plan"
    if plan_dir.is_dir():
        for step in sorted(plan_dir.glob("step_*.md")):
            chunks.append(_read(step))
        chunks.append(_read(plan_dir / "SESSION_RECALL.md", 4000))
    try:
        from feature_paths import read_active_feature

        active = read_active_feature(workspace)
        if active:
            feat = Path(active["abs_path"])
            for name in ("spec.md", "feature-plan.md", "tasks.md"):
                chunks.append(_read(feat / name))
    except ImportError:
        pass
    if extra:
        chunks.append(extra)
    return "\n".join(chunks).lower()


def has_agent_signal(text: str) -> bool:
    return any(sig in text for sig in AGENT_SIGNALS)


def classify_shape(text: str) -> dict[str, bool]:
    return {
        shape: any(kw in text for kw in keywords)
        for shape, keywords in SHAPE_PATTERNS.items()
    }


def pick_skills(context: str) -> list[tuple[str, str]]:
    """Return [(skill_name, reason), ...]. Unlike the frontend router there is
    one primary skill (agent-builder) - this signals whether it applies."""
    if not has_agent_signal(context):
        return []
    shape = classify_shape(context)
    active_shapes = [name for name, hit in shape.items() if hit]
    if active_shapes:
        reason = f"agent-development signals matched ({', '.join(active_shapes)})"
    else:
        reason = "agent-development signals matched"
    return [("agent-builder", reason)]


def format_auto_agent_skills_md(
    workspace: Path,
    picks: list[tuple[str, str]],
    shape: dict[str, bool],
    task_hint: str,
    capabilities: list[str] | None = None,
) -> str:
    lines = [
        "# Auto-detected agent-development signals",
        "",
        "Generated by `scripts/agent_skill_router.py`. **Agent: read these before designing/building.**",
        "",
        f"**Task context:** {task_hint or 'from HANDOFF.md, TASKS.yml, plan/, DECISIONS.md'}",
        "",
        "## Agent shape detected",
        "",
    ]
    active_shapes = [name for name, hit in shape.items() if hit]
    if active_shapes:
        for name in active_shapes:
            lines.append(f"- `{name.replace('_', ' ')}`")
    else:
        lines.append("- (no specific shape signals - treat as a single-agent, single-tool default until clarified)")
    lines.append("")
    lines.append("## Read (in order)")
    lines.append("")
    idx = 1
    for rel in ALWAYS_READ:
        lines.append(f"{idx}. `{rel}`")
        idx += 1
    lines.append("")
    capabilities = capabilities if capabilities is not None else select_capabilities(gather_context(workspace))
    lines.append("## Capability chain")
    lines.append("")
    if capabilities:
        for name in capabilities:
            suffix = " - explicit consent required before external transfer or spending" if name in CONSENT_REQUIRED else ""
            lines.append(f"- `{name}` -> `skills/{name}/SKILL.md`{suffix}")
    else:
        lines.append("- `agentic-engineering`")
    lines.append("")
    lines.append("Compatibility aliases: `autonomous-loops` routes to `continuous-agent-loop`; ")
    lines.append("`continuous-learning` routes to `continuous-learning-v2`.")
    lines.append("")
    lines.append("## Scaffold")
    lines.append("")
    lines.append("Run `loop agent scaffold` to create `agent/skills/`, `agent/tools/`, `agent/evals/`,")
    lines.append("and `agent/AGENT_ARCHITECTURE.md` in the product workspace if not already present.")
    lines.append("")
    lines.append("## Record")
    lines.append("")
    lines.append("Capture agent type, tools, memory, guardrails, and model provider in `agent/AGENT_ARCHITECTURE.md`")
    lines.append("and in `DECISIONS.md` once chosen - do not re-ask the user once recorded.")
    lines.append("")
    return "\n".join(lines)


def run_router(workspace: Path, extra: str = "", write: bool = False) -> list[tuple[str, str]]:
    context = gather_context(workspace, extra)
    picks = pick_skills(context)
    if write and picks:
        shape = classify_shape(context)
        out = workspace / "plan" / "AUTO_AGENT_SKILLS.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        task_hint = ""
        handoff = _read(workspace / "HANDOFF.md", 500)
        if handoff:
            task_hint = handoff.strip().split("\n")[0][:200]
        out.write_text(
            format_auto_agent_skills_md(
                workspace, picks, shape, task_hint, select_capabilities(context)
            ),
            encoding="utf-8",
        )
    return picks


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-detect AI-agent-development signals from plan context.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--text", default="", help="Extra context (e.g. current user message).")
    parser.add_argument("--write", action="store_true", help="Write plan/AUTO_AGENT_SKILLS.md")
    parser.add_argument("--quiet", action="store_true", help="Only print skill names.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    picks = run_router(workspace, extra=args.text, write=args.write)

    if not picks:
        if not args.quiet:
            print("No AI-agent-development signals detected.")
        return 0

    if args.quiet:
        for name, _ in picks:
            print(name)
        return 0

    for name, reason in picks:
        path = resolve_skill(name, workspace)
        loc = str(path) if path else f"skills/{name}/SKILL.md"
        print(f"{name}\t{reason}\t{loc}")
    if args.write:
        print(f"\nWrote {workspace / 'plan' / 'AUTO_AGENT_SKILLS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
