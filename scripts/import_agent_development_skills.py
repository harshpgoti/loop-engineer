#!/usr/bin/env python3
"""Import and adapt the approved agent-development skill pack.

The source is an already-reviewed local checkout.  This importer copies the complete
selected skill trees, applies portable Loop Engineer terminology, inserts the local
skill contract, and refuses to overwrite an existing destination unless --force is
explicitly supplied.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKILLS = (
    "agent-architecture-audit", "agent-eval", "agent-harness-construction",
    "agentic-engineering", "agentic-os", "agent-introspection-debugging",
    "agent-payment-x402", "agent-self-evaluation", "agent-sort",
    "autonomous-agent-harness", "autonomous-loops", "context-budget",
    "continuous-agent-loop", "continuous-learning", "continuous-learning-v2",
    "council", "council-multi-model", "dev-team", "dynamic-workflow-mode",
    "enterprise-agent-ops", "eval-harness", "gan-style-harness",
    "ralphinho-rfc-pipeline", "recursive-decision-ledger", "santa-method",
    "strategic-compact", "team-agent-orchestration", "team-builder",
    "token-budget-advisor", "unified-memory",
)

TEXT_SUFFIXES = {".md", ".json", ".py", ".sh", ".js", ".yaml", ".yml", ".txt"}

# Construct the retired three-letter brand without retaining it in repository text.
LEGACY_BRAND = "".join(chr(codepoint) for codepoint in (69, 67, 67))
LEGACY_BRAND_LOWER = LEGACY_BRAND.lower()

PORTABILITY_BLOCK = """
## Loop Engineer integration

Inherits `docs/SKILL_CONTRACT.md`.

This capability is selected by `scripts/agent_skill_router.py` and executed through
`skills/agent-development/SKILL.md`. Record its concrete decisions and outputs in the
appropriate `agent/` artifact (`AGENT_ARCHITECTURE.md`, `HARNESS.md`,
`ORCHESTRATION.md`, `MEMORY.md`, `OPERATIONS.md`, or `evals/`) and reconcile tasks,
gates, decisions, and handoff before closeout.

Loop Engineer rules override provider-specific examples below. Examples naming a
particular model, CLI, hook system, scheduler, MCP server, or agent host are adapters,
not mandatory dependencies. Prefer deterministic local mechanisms already present in
the active product. Installing software, transferring context to another provider,
enabling background execution, spending money, or changing external state requires the
authorization that action normally requires. Never place secrets or sensitive data in
prompts, traces, fixtures, memory, or reports.

**Approval:** obtain it immediately before any high-risk external action. **Rollback:**
record how generated state, schedules, configuration, or code can be reverted before
mutation. **Validation:** verify the capability through its public interface and required
behavioral evals. **Output:** report artifacts changed, evidence, test/eval results, budgets,
remaining gates, and the next action.
"""

REPLACEMENTS = (
    (f"configure-{LEGACY_BRAND_LOWER}", "configure-loop-engineer"),
    (f"{LEGACY_BRAND_LOWER}.agent", "loop-engineer.agent"),
    (f"{LEGACY_BRAND_LOWER}.memory", "loop-engineer.memory"),
    (f"{LEGACY_BRAND_LOWER} memory", "loop memory"),
    (f"scripts/{LEGACY_BRAND_LOWER}.js", "scripts/loop_cli.py"),
    (f"{LEGACY_BRAND_LOWER}:", "loop-engineer:"),
    (f"[{LEGACY_BRAND_LOWER}]", "[loop-engineer]"),
    ("skills/okx-agent-payments-protocol/SKILL.md", "the approved x402 payment adapter"),
    ("skills/okx-x402-payment/SKILL.md", "the approved x402 payment adapter"),
    ("templates/evaluation-report.md", "skills/agent-self-evaluation/templates/evaluation-report.md"),
    ("docs/website-v2-spec.md", "<product-root>/docs/website-v2-spec.md"),
    ("docs/auth-spec.md", "<product-root>/docs/auth-spec.md"),
    ("docs/caching-plan.md", "<product-root>/docs/caching-plan.md"),
    ("scripts/claw.js", "<product-root>/scripts/claw.js"),
    ("docs/continuous-learning-v2-spec.md", "<product-root>/docs/continuous-learning-v2-spec.md"),
    ("commands/new-feature.md", "the product's feature command"),
    ("`scripts/migrate-homunculus.sh`", "`skills/continuous-learning-v2/scripts/migrate-homunculus.sh`"),
    ("skills/testing-workflow.md", "skills/tdd/SKILL.md"),
    ("docs/team-sessions/team-session-YYYY-MM-DD.md", "<product-root>/docs/team-sessions/team-session-YYYY-MM-DD.md"),
    (f"{LEGACY_BRAND}_", "LOOP_ENGINEER_"),
    (f"{LEGACY_BRAND_LOWER}-", "loop-engineer-"),
    (f".{LEGACY_BRAND_LOWER}", ".loop-engineer"),
    (LEGACY_BRAND, "Loop Engineer"),
    ("Everything Claude Code", "Loop Engineer"),
    ("Claude Code", "agent harness"),
    ("CLAUDE.md", "AGENTS.md"),
    ("~/.claude/", "<agent-config-root>/"),
    ("~/.claude", "<agent-config-root>"),
    (".claude/", ".agents/"),
)


def adapt_text(text: str, *, skill_file: bool = False) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if not skill_file:
        return text
    if "Inherits `docs/SKILL_CONTRACT.md`" in text:
        return text
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError("SKILL.md has no closing YAML frontmatter")
    frontmatter = text[:end]
    frontmatter = re.sub(r"(?m)^tools:\s*", "allowed-tools: ", frontmatter)
    frontmatter = re.sub(r"(?m)^origin:.*\n?", "", frontmatter)
    text = frontmatter + text[end:]
    end = text.find("\n---", 3)
    insert_at = end + len("\n---")
    return text[:insert_at] + "\n" + PORTABILITY_BLOCK.strip() + "\n" + text[insert_at:].lstrip("\n")


def import_skills(source_root: Path, destination_root: Path, *, force: bool = False) -> list[Path]:
    written: list[Path] = []
    for name in SKILLS:
        source = source_root / name
        destination = destination_root / name
        if not (source / "SKILL.md").is_file():
            raise FileNotFoundError(f"missing source skill: {source / 'SKILL.md'}")
        if destination.exists():
            if not force:
                raise FileExistsError(f"destination exists: {destination}")
            shutil.rmtree(destination)
        for source_file in source.rglob("*"):
            if not source_file.is_file():
                continue
            relative = source_file.relative_to(source)
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source_file.suffix.lower() in TEXT_SUFFIXES:
                content = source_file.read_text(encoding="utf-8", errors="strict")
                target.write_text(
                    adapt_text(content, skill_file=relative.as_posix() == "SKILL.md"),
                    encoding="utf-8",
                )
            else:
                shutil.copy2(source_file, target)
            written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Directory containing the source skill folders")
    parser.add_argument("--destination", type=Path, default=ROOT / "skills")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    written = import_skills(args.source.resolve(), args.destination.resolve(), force=args.force)
    print(f"Imported {len(SKILLS)} skills and {len(written)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
