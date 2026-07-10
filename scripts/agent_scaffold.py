#!/usr/bin/env python3
"""Scaffold agent/ (skills, tools, evals, architecture doc) in the product workspace.

Gives a product that is, or includes, an AI agent the same portable
SKILL.md authoring convention Loop Engineer uses for its own skills —
without vendoring any third-party agent runtime.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from workspace_utils import ROOT, resolve_workspace

AGENT_SKILLS_README = """# Product agent skills

This folder holds **this product's own agent skills** — not Loop Engineer's
operational skills (those live in the repo-root `skills/`).

Each skill is a folder with a `SKILL.md` (frontmatter `name` + `description`,
same convention as Loop Engineer's own skills). Copy `_template/SKILL.md` to
start one:

```bash
cp -r agent/skills/_template agent/skills/<your-skill-name>
```

## Rules

- One skill = one clear trigger + one clear job. Don't build a mega-skill.
- Declare every tool the skill uses and whether it is destructive (ties to
  AGENTS.md rule 5 — human approval for high-risk actions).
- Reference `agent/AGENT_ARCHITECTURE.md` for the overall agent shape; put
  skill-specific detail here, not there.
- Prior art: the agent skill hubs listed in `tools/registry.md` are a useful
  **read-only** reference — do not vendor their code or packages.
"""

AGENT_TOOLS_README = """# Product agent tools

Tool/function definitions the agent can call, separate from the skills that
decide when to call them. One file per tool (or per tool group) works well:
name, JSON schema, side effects, and whether it is destructive.

Destructive or high-risk tools need human approval per AGENTS.md rule 5 —
say so explicitly in the tool's doc, not just in code comments.
"""

AGENT_EVALS_README = """# Product agent evals

Golden cases and eval harness for the agent, distinct from unit tests.
Tie into `skills/qa-validation/SKILL.md` — an agent PR should not merge on
code review alone if its behavior is what changed.

Suggested layout:

- `cases/` — golden input/expected-output pairs
- `run_evals.py` (or equivalent) — replays cases against the current agent
- Track pass rate over time; regressions block merge same as failing tests.
"""

SCAFFOLD_FILES: dict[str, str] = {
    "agent/skills/README.md": AGENT_SKILLS_README,
    "agent/skills/_template/SKILL.md": None,  # rendered from templates/agent_skill.template.md
    "agent/tools/README.md": AGENT_TOOLS_README,
    "agent/evals/README.md": AGENT_EVALS_README,
    "agent/AGENT_ARCHITECTURE.md": None,  # rendered from templates/agent_architecture.template.md
}


def _load_template(name: str) -> str:
    path = ROOT / "templates" / name
    if not path.exists():
        return f"# {name}\n\n"
    return path.read_text(encoding="utf-8")


def scaffold(workspace: Path, force: bool = False) -> list[tuple[str, str]]:
    """Create agent/ scaffold files. Returns [(relative_path, status), ...]."""
    results: list[tuple[str, str]] = []
    contents = dict(SCAFFOLD_FILES)
    contents["agent/skills/_template/SKILL.md"] = _load_template("agent_skill.template.md")
    contents["agent/AGENT_ARCHITECTURE.md"] = _load_template("agent_architecture.template.md")

    for rel, content in contents.items():
        dest = workspace / rel
        if dest.exists() and not force:
            results.append((rel, "skipped (exists)"))
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        results.append((rel, "written"))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold agent/ structure in the product workspace.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold files.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    results = scaffold(workspace, force=args.force)
    for rel, status in results:
        print(f"{status}: {rel}")
    print("\nNext: fill agent/AGENT_ARCHITECTURE.md, then copy agent/skills/_template/ per skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
