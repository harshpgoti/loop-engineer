#!/usr/bin/env python3
"""Team mode: commit a path-free bootstrap so teammates get Loop automatically.

gstack's insight is that the committed artifact is a **bootstrap instruction, not
the tool**. Loop commits into the product repo:
  - a bootstrap skill (`<host>/loop-engineer/SKILL.md`) with NO absolute paths -
    it tells any agent to install Loop if the `loop` CLI is missing, then route
    commands to the installed app,
  - a marker-guarded "Loop Engineering OS" section appended to CLAUDE.md.

A teammate clones the repo, opens any agent, and is walked through installing Loop
on first session - no out-of-band instructions.

`required` blocks AI-assisted product work until Loop is installed; `optional`
just nudges. Idempotent and marker-guarded; re-running updates in place.

Stdlib only.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- loop-engineer:team-init -->"
END = "<!-- /loop-engineer:team-init -->"
MARKER = "loop-engineer:generated"

# Project-scope skill dirs to seed the bootstrap into. Kept in sync with
# install_skills.HOSTS project paths; imported lazily to avoid a hard dep.
def _project_skill_dirs() -> list[str]:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from install_skills import HOSTS

        dirs = {v["project"] for v in HOSTS.values()}
        return sorted(dirs)
    except Exception:
        return [".agents/skills", ".claude/skills", ".cursor/skills", ".opencode/skills"]


def clone_url() -> str:
    """Best-effort clone URL for the install instruction."""
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "https://github.com/<org>/loop-engineer"


def bootstrap_skill(mode: str, url: str) -> str:
    required = mode == "required"
    policy = (
        "Do not perform substantial AI-assisted product work in this repo outside "
        "the Loop process. If Loop is not installed, stop and install it first."
        if required
        else "Prefer the Loop process for product work here. If Loop is not "
        "installed, offer to install it, then continue."
    )
    heading = (
        "Loop Engineering OS - required for AI-assisted work in this repo"
        if required
        else "Loop Engineering OS - recommended for AI-assisted work in this repo"
    )
    return (
        "---\n"
        "name: loop-engineer\n"
        'description: "This repository uses Loop Engineering OS for AI-assisted '
        'product work. Bootstrap it before running any Loop command or substantial '
        'planning/build/review/ship task."\n'
        "---\n"
        f"<!-- {MARKER} kind=bootstrap mode={mode} -->\n\n"
        f"# {heading}\n\n"
        "This repo standardizes AI-assisted development on **Loop Engineering OS**.\n\n"
        "## If the `loop` CLI is not installed\n\n"
        "Install it once (any shell):\n\n"
        "```bash\n"
        f"git clone --depth 1 {url} ~/.loop-engineer/app\n"
        "cd ~/.loop-engineer/app && ./install.sh    # Windows: ./install.ps1\n"
        "loop skills install                          # wire every coding agent\n"
        "```\n\n"
        "Then re-open this repo. Every agent (Claude, Codex, Cursor, Gemini, "
        "OpenCode, ...) will route Loop commands to the installed app.\n\n"
        "## Using it\n\n"
        "Type a Loop command (`/plan-loop`, `/product-develop`, `/loop-engine`, "
        "...) or describe the task; your agent routes it to the installed app per "
        "its `AGENTS.md`. Full list: the app's `LOOP_COMMANDS.md`.\n\n"
        "## Policy\n\n"
        f"{policy}\n"
    )


def claude_md_block(mode: str) -> str:
    note = "required" if mode == "required" else "recommended"
    return (
        f"{BEGIN}\n"
        "## Loop Engineering OS\n\n"
        f"This repo uses Loop Engineering OS for AI-assisted work ({note}). If the "
        "`loop` CLI is missing, follow `.agents/skills/loop-engineer/SKILL.md` to "
        "install it, then run `loop skills install`. Use Loop commands "
        "(`/plan-loop`, `/product-develop`, ...) for product work; they route to "
        "the installed app.\n"
        f"{END}"
    )


def upsert_block(path: Path, block: str, *, dry_run: bool) -> str:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if BEGIN in existing and END in existing:
        pre = existing.split(BEGIN)[0].rstrip()
        post = existing.split(END, 1)[1].lstrip()
        new = (pre + "\n\n" + block + ("\n\n" + post if post else "\n")).strip() + "\n"
        action = "update"
    else:
        base = existing.rstrip()
        new = (base + "\n\n" + block + "\n") if base else (block + "\n")
        action = "append" if base else "create"
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    return action


def team_init(project_root: Path, mode: str, *, commit: bool, dry_run: bool) -> int:
    url = clone_url()
    written: list[Path] = []

    skill_body = bootstrap_skill(mode, url)
    for rel in _project_skill_dirs():
        skill_path = project_root / rel / "loop-engineer" / "SKILL.md"
        if not dry_run:
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(skill_body, encoding="utf-8")
        written.append(skill_path)
        print(f"  {'would write' if dry_run else 'wrote'} {skill_path.relative_to(project_root)}")

    claude_md = project_root / "CLAUDE.md"
    action = upsert_block(claude_md, claude_md_block(mode), dry_run=dry_run)
    written.append(claude_md)
    print(f"  {action} CLAUDE.md (Loop Engineering OS section)")

    print(f"\nTeam mode: {mode}. Teammates who open any coding agent get bootstrapped on first session.")

    if commit and not dry_run:
        rels = [str(p.relative_to(project_root)) for p in written]
        add = subprocess.run(["git", "-C", str(project_root), "add", *rels], capture_output=True, text=True)
        if add.returncode == 0:
            msg = f"{'require' if mode == 'required' else 'recommend'} Loop Engineering OS for AI-assisted work"
            subprocess.run(["git", "-C", str(project_root), "commit", "-m", msg], capture_output=True, text=True)
            print("Committed.")
        else:
            print("git add failed; commit manually:", add.stderr.strip())
    elif not dry_run:
        print("Review, then commit:")
        print("  git add .agents/ .claude/ .cursor/ .opencode/ CLAUDE.md && git commit -m 'require Loop for AI work'")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", nargs="?", choices=("required", "optional"), default="required")
    parser.add_argument("--workspace", default=None, help="Repo root (default: cwd).")
    parser.add_argument("--commit", action="store_true", help="git add + commit the bootstrap.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing.")
    args = parser.parse_args()

    raw = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if raw.name == ".loop-engineer":
        raw = raw.parent
    return team_init(raw, args.mode, commit=args.commit, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
