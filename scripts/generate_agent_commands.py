#!/usr/bin/env python3
"""Generate native command/skill wrappers for every coding agent Loop Engineer supports.

DEPRECATED — prefer `install_skills.py` (router skills in every agent's skills
dir; see `docs/DISTRIBUTION.md`). This generator is retained only for tool
versions that predate SKILL.md support and is run solely via
`loop setup --legacy-commands` / `loop update --legacy-commands` /
`loop commands install`. It will be removed after a deprecation window.

Loop Engineer's commands live in `commands/*.md` (+ `skills/*/SKILL.md`) and are
"portable commands" - an agent reads the file and executes it. Most agent CLIs,
however, only autocomplete *native* commands they discover in a per-tool
directory. This script emits thin native wrappers, one per command per tool, that
tell the agent to read+execute the canonical Loop Engineer command against the
active product workspace.

Single source of truth = `commands/*.md`. Re-run any time commands change.

Supported tools and where their native wrappers live:

  claude    ~/.claude/commands/<name>.md              -> /<name>
  cursor    ~/.cursor/commands/<name>.md              -> /<name>
  opencode  ~/.config/opencode/commands/<name>.md     -> /<name>
  codex     ~/.codex/skills/<name>/SKILL.md           -> $<name> (or implicit)

Project scope writes to <workspace>/.claude|.cursor|.opencode|.codex/... instead.

Codex note: Codex CLI's file-based custom *prompts* (`~/.codex/prompts/*.md`,
invoked as `/prompts:<name>`) were removed upstream in codex-cli >= 0.117.0 -
see openai/codex#15941 and #15972. Codex reserves `/` for built-in session
commands; the current mechanism is *Skills* (`SKILL.md` in a named folder),
invoked explicitly with `$<name>` or implicitly when the prompt matches the
skill's description. This generator writes Codex wrappers in that format. Any
previously generated `~/.codex/prompts/*.md` files (dead weight now) are
cleaned up automatically since they carry our generated marker.

Grok Build now reads SKILL.md skills from ~/.grok/skills (and .grok/skills), so it
is covered by the router install (scripts/install_skills.py), not this legacy
generator. Older Grok Build builds without skills support fall back to portable
interpretation via GROK.md + AGENTS.md.

Every generated file carries a MARKER line; the script refuses to overwrite a file
that lacks the marker unless --force is given, so it never clobbers hand-written
commands/skills.
"""
from __future__ import annotations

import argparse
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "commands"
SKILLS_DIR = ROOT / "skills"

MARKER = "loop-engineer:generated"

# style="command": flat `<dest>/<name>.md` file, invoked as f"{invoke_prefix}<name>".
# style="skill":    `<dest>/<name>/SKILL.md` folder, invoked as f"{invoke_prefix}<name>"
#                    and requires a `name:` field in frontmatter.
TOOLS: dict[str, dict] = {
    "claude": {
        "user": Path.home() / ".claude" / "commands",
        "project": ".claude/commands",
        "style": "command",
        "invoke_prefix": "/",
        "frontmatter": True,
    },
    "cursor": {
        "user": Path.home() / ".cursor" / "commands",
        "project": ".cursor/commands",
        "style": "command",
        "invoke_prefix": "/",
        "frontmatter": False,  # Cursor commands are plain markdown
    },
    "opencode": {
        "user": Path.home() / ".config" / "opencode" / "commands",
        "project": ".opencode/commands",
        "style": "command",
        "invoke_prefix": "/",
        "frontmatter": True,
    },
    "codex": {
        "user": Path.home() / ".codex" / "skills",
        "project": ".codex/skills",
        "style": "skill",
        "invoke_prefix": "$",
        "frontmatter": True,
    },
}

# Legacy locations this generator used to write to before a tool's native
# mechanism changed. Cleaned up automatically (marker-guarded) so stale,
# non-functional wrappers don't linger and confuse users.
LEGACY_LOCATIONS: dict[str, list[dict]] = {
    "codex": [
        {"user": Path.home() / ".codex" / "prompts", "project": None, "style": "command"},
    ],
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


def render(name: str, description: str, app_root: Path, *, style: str, frontmatter: bool) -> str:
    body = wrapper_body(name, description, app_root)
    fm = ""
    if frontmatter:
        # escape double quotes in description for YAML
        desc = description.replace('"', "'")
        if style == "skill":
            # Codex SKILL.md requires `name:`; keep it short and match the folder.
            fm = "---\n" f"name: {name}\n" f'description: "{desc}"\n' "---\n"
        else:
            fm = "---\n" f'description: "{desc}"\n' "argument-hint: [args]\n" "---\n"
    return f"{fm}<!-- {MARKER} name={name} -->\n{body}"


def target_dir(cfg: dict, scope: str, workspace: Path) -> Path | None:
    if scope == "user":
        return cfg.get("user")
    rel = cfg.get("project")
    if rel is None:
        return None
    return workspace / rel


def wrapper_path(dest: Path, name: str, style: str) -> Path:
    if style == "skill":
        return dest / name / "SKILL.md"
    return dest / f"{name}.md"


def existing_wrapper_paths(dest: Path, style: str):
    if not dest.exists():
        return
    if style == "skill":
        for skill_md in dest.glob("*/SKILL.md"):
            yield skill_md.parent.name, skill_md
    else:
        for md in dest.glob("*.md"):
            yield md.stem, md


def remove_wrapper(path: Path, style: str) -> None:
    if style == "skill":
        shutil.rmtree(path.parent, ignore_errors=True)
    else:
        path.unlink()


def clean_legacy(tool: str, scope: str, workspace: Path, *, dry_run: bool) -> int:
    removed = 0
    for legacy in LEGACY_LOCATIONS.get(tool, []):
        dest = target_dir(legacy, scope, workspace)
        if dest is None or not dest.exists():
            continue
        for name, path in list(existing_wrapper_paths(dest, legacy["style"])):
            try:
                body = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if MARKER not in body:
                continue  # never touch hand-written files
            if not dry_run:
                remove_wrapper(path, legacy["style"])
            print(f"[{tool}] remove legacy {path}  (superseded mechanism)")
            removed += 1
    return removed


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
        help="user = global agent config dirs (default); project = <workspace>/.<tool>/....",
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
    total_legacy_removed = 0
    for tool in tools:
        cfg = TOOLS[tool]
        dest = target_dir(cfg, args.scope, workspace)
        if dest is None:
            print(f"[{tool}] no {args.scope}-scope command dir (skipped)")
            continue
        style = cfg["style"]
        frontmatter = cfg["frontmatter"]
        written = skipped = 0
        if not args.dry_run:
            dest.mkdir(parents=True, exist_ok=True)
        for cmd in commands:
            name = cmd.stem
            out = wrapper_path(dest, name, style)
            if out.exists() and not args.force:
                existing = out.read_text(encoding="utf-8", errors="ignore")
                if MARKER not in existing:
                    print(f"[{tool}] SKIP {out}  (exists, not generated - use --force)")
                    skipped += 1
                    continue
            content = render(name, command_description(cmd), app_root, style=style, frontmatter=frontmatter)
            if not args.dry_run:
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(content, encoding="utf-8")
            written += 1
        # Prune stale generated wrappers whose command was removed/renamed.
        current = {cmd.stem for cmd in commands}
        pruned = 0
        for existing_name, existing_path in list(existing_wrapper_paths(dest, style)):
            if existing_name in current:
                continue
            try:
                body = existing_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if MARKER not in body:
                continue  # never touch hand-written commands
            if not args.dry_run:
                remove_wrapper(existing_path, style)
            pruned += 1
            print(f"[{tool}] prune {existing_name}  (command no longer exists)")
        legacy_removed = clean_legacy(tool, args.scope, workspace, dry_run=args.dry_run)
        invoke = f"{cfg['invoke_prefix']}<name>"
        print(f"[{tool}] {written} command(s) -> {dest}   (invoke: {invoke})")
        total_written += written
        total_skipped += skipped
        total_pruned += pruned
        total_legacy_removed += legacy_removed

    print()
    verb = "Would write" if args.dry_run else "Wrote"
    print(
        f"{verb} {total_written} wrapper file(s); pruned {total_pruned}; "
        f"removed {total_legacy_removed} legacy; skipped {total_skipped}."
    )
    if args.dry_run:
        print("Dry run only - re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
