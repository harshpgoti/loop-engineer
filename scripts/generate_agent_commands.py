#!/usr/bin/env python3
"""Generate native slash-command wrappers for every coding agent Loop Engineer supports.

Loop Engineer's commands live in `commands/*.md` (+ `skills/*/SKILL.md`) and are
"portable commands" - an agent reads the file and executes it. Most agent CLIs,
however, only autocomplete *native* slash commands they discover in a per-tool
directory. This script emits thin native wrappers, one per command per tool, that
tell the agent to read+execute the canonical Loop Engineer command against the
active product workspace.

Single source of truth = `commands/*.md`. Re-run any time commands change.

Supported tools and where their native commands live:

  claude    ~/.claude/commands/<name>.md            -> /<name>
  cursor    ~/.cursor/commands/<name>.md            -> /<name>
  codex     ~/.codex/prompts/<name>.md              -> /prompts:<name>   (home only)
  opencode  ~/.config/opencode/commands/<name>.md   -> /<name>

Project scope writes to <workspace>/.claude|.cursor|.opencode/commands/ instead
(Codex only supports the home prompts dir, so project scope skips Codex).

Grok Build has no reliable file-based custom-command mechanism, so it keeps using
portable interpretation via GROK.md + AGENTS.md - nothing to generate.

Every generated file carries a MARKER line; the script refuses to overwrite a file
that lacks the marker unless --force is given, so it never clobbers hand-written
commands.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "commands"
SKILLS_DIR = ROOT / "skills"

MARKER = "loop-engineer:generated"

# scope="user": absolute dir. scope="project": relative to workspace.
TOOLS: dict[str, dict] = {
    "claude": {
        "user": Path.home() / ".claude" / "commands",
        "project": ".claude/commands",
        "prefix": "",          # invoked as /<name>
        "frontmatter": True,
    },
    "cursor": {
        "user": Path.home() / ".cursor" / "commands",
        "project": ".cursor/commands",
        "prefix": "",
        "frontmatter": False,  # Cursor commands are plain markdown
    },
    "codex": {
        "user": Path.home() / ".codex" / "prompts",
        "project": None,       # Codex only reads the home prompts dir
        "prefix": "prompts:",  # invoked as /prompts:<name>
        "frontmatter": True,
    },
    "opencode": {
        "user": Path.home() / ".config" / "opencode" / "commands",
        "project": ".opencode/commands",
        "prefix": "",
        "frontmatter": True,
    },
}


def command_description(path: Path) -> str:
    """First non-empty, non-heading line of a command file."""
    heading_seen = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            heading_seen = True
            continue
        if heading_seen:
            # strip markdown emphasis/backticks for a clean one-liner
            return re.sub(r"[`*]", "", line).strip()
    return f"Loop Engineering command /{path.stem}"


def wrapper_body(name: str, description: str, app_root: Path) -> str:
    app = app_root.as_posix()
    skill = SKILLS_DIR / name / "SKILL.md"
    skill_line = (
        f"3. `{app}/skills/{name}/SKILL.md`\n" if skill.exists() else ""
    )
    return (
        f"Loop Engineering OS - execute the `/{name}` command.\n\n"
        f"{description}\n\n"
        f"Read and execute these files from the Loop Engineer app, in order:\n"
        f"1. `{app}/AGENTS.md` (routing + non-negotiable rules)\n"
        f"2. `{app}/commands/{name}.md`\n"
        f"{skill_line}"
        f"\nRun the command against the **active product workspace**: a local "
        f"`.loop-engineer/` data dir auto-detected from the current directory, "
        f"else the global `~/.loop-engineer/data/`. Do not ask the user to paste "
        f"boot prompts.\n\n"
        f"Arguments (e.g. a product idea): $ARGUMENTS\n"
    )


def render(name: str, description: str, app_root: Path, frontmatter: bool) -> str:
    body = wrapper_body(name, description, app_root)
    fm = ""
    if frontmatter:
        # escape double quotes in description for YAML
        desc = description.replace('"', "'")
        fm = (
            "---\n"
            f'description: "{desc}"\n'
            "argument-hint: [args]\n"
            "---\n"
        )
    return f"{fm}<!-- {MARKER} name={name} -->\n{body}"


def target_dir(tool: str, scope: str, workspace: Path) -> Path | None:
    cfg = TOOLS[tool]
    if scope == "user":
        return cfg["user"]
    rel = cfg["project"]
    if rel is None:
        return None
    return workspace / rel


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--tool",
        choices=[*TOOLS.keys(), "all"],
        default="all",
        help="Which agent to generate for (default: all).",
    )
    parser.add_argument(
        "--scope",
        choices=["user", "project"],
        default="user",
        help="user = global agent config dirs (default); project = <workspace>/.<tool>/commands/.",
    )
    parser.add_argument("--workspace", default=".", help="Product folder for --scope project (default: cwd).")
    parser.add_argument(
        "--app-root",
        default=str(ROOT),
        help="Loop Engineer app dir the wrappers point at (default: this repo).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be written; write nothing.")
    parser.add_argument("--force", action="store_true", help="Overwrite files even without the generated marker.")
    args = parser.parse_args()

    app_root = Path(args.app_root).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    tools = list(TOOLS.keys()) if args.tool == "all" else [args.tool]

    commands = sorted(p for p in COMMANDS_DIR.glob("*.md") if p.is_file())
    if not commands:
        print(f"No command files found in {COMMANDS_DIR}", flush=True)
        return 1

    print(f"App root:  {app_root}")
    print(f"Scope:     {args.scope}" + (f"  (workspace: {workspace})" if args.scope == "project" else ""))
    print(f"Commands:  {len(commands)}")
    print()

    total_written = 0
    total_skipped = 0
    total_pruned = 0
    for tool in tools:
        dest = target_dir(tool, args.scope, workspace)
        if dest is None:
            print(f"[{tool}] no {args.scope}-scope command dir (skipped)")
            continue
        prefix = TOOLS[tool]["prefix"]
        frontmatter = TOOLS[tool]["frontmatter"]
        written = skipped = 0
        if not args.dry_run:
            dest.mkdir(parents=True, exist_ok=True)
        for cmd in commands:
            name = cmd.stem
            out = dest / f"{name}.md"
            if out.exists() and not args.force:
                existing = out.read_text(encoding="utf-8", errors="ignore")
                if MARKER not in existing:
                    print(f"[{tool}] SKIP {out}  (exists, not generated - use --force)")
                    skipped += 1
                    continue
            content = render(name, command_description(cmd), app_root, frontmatter)
            if args.dry_run:
                pass
            else:
                out.write_text(content, encoding="utf-8")
            written += 1
        # Prune stale generated wrappers whose command was removed/renamed.
        current = {cmd.stem for cmd in commands}
        pruned = 0
        if dest.exists():
            for existing in dest.glob("*.md"):
                if existing.stem in current:
                    continue
                try:
                    body = existing.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if MARKER not in body:
                    continue  # never touch hand-written commands
                if not args.dry_run:
                    existing.unlink()
                pruned += 1
                print(f"[{tool}] prune {existing.name}  (command no longer exists)")
        invoke = f"/{prefix}<name>"
        print(f"[{tool}] {written} command(s) -> {dest}   (invoke: {invoke})")
        total_written += written
        total_skipped += skipped
        total_pruned += pruned

    print()
    verb = "Would write" if args.dry_run else "Wrote"
    print(f"{verb} {total_written} wrapper file(s); pruned {total_pruned}; skipped {total_skipped}.")
    if args.dry_run:
        print("Dry run only - re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
