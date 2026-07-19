#!/usr/bin/env python3
"""Install thin router skills into every coding agent, pointing at the installed app.

Requirement: whether the user works globally or inside a project, any coding
agent must be able to run every Loop command (`/plan-loop`, `/product-develop`,
...) **from the single installed app** — and switching agents mid-task must need
no manual setup. So Loop installs routers into **all known agent skill dirs at
once**, not just the one the user picked.

Loop's canonical skills are not self-contained documents: they read `AGENTS.md`
and `templates/`, and run `scripts/` from the app root. Copying them into a
user's project or a tool's config dir would break those references and create
drift. So this installer never copies content — it generates one ~15-line router
`SKILL.md` per command. Each router carries the command's trigger in its
description and a pointer back to the app, so agents load the real command +
skill from the single installed runtime. Editing canonical commands/skills needs
no reinstall; only adding/renaming a command does (setup/update regenerate).

Directory name is prefixed `loop-<command>` for collision-safety and clear
ownership; the `name:` frontmatter stays the clean command name so `/plan-loop`
still resolves. Ownership is tracked per destination via a
`.loop-engineer-manifest.json` plus a `loop-engineer:generated` marker inside
each router — install/update/uninstall never touch a directory Loop didn't
create, and re-installs clean up older full-copy (v1/v2) installs automatically.

Claude Code needs no plugin: its skills and slash commands are unified, so the
router in `~/.claude/skills/` is directly invokable as `/plan-loop`. See
`docs/DISTRIBUTION.md`.

Standard library only, so it runs in fresh clones and direct-agent environments.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = ROOT / "commands"
SKILLS_DIR = ROOT / "skills"
MANIFEST_NAME = ".loop-engineer-manifest.json"
GENERATOR = "loop-engineer"
MARKER = "loop-engineer:generated"
DIR_PREFIX = "loop-"

# One line per supported agent. `user` is the global skills dir; `project` is the
# per-repo skills dir. Adding an agent = one row, zero code (gstack's model).
# Several agents read the universal `.agents/skills` at project scope, so those
# project paths intentionally collapse and are de-duplicated at install time.
HOSTS: dict[str, dict[str, str]] = {
    "universal": {"user": "~/.agents/skills", "project": ".agents/skills"},
    "claude": {"user": "~/.claude/skills", "project": ".claude/skills"},
    "codex": {"user": "~/.codex/skills", "project": ".agents/skills"},
    "cursor": {"user": "~/.cursor/skills", "project": ".cursor/skills"},
    "opencode": {"user": "~/.config/opencode/skills", "project": ".opencode/skills"},
    "gemini": {"user": "~/.gemini/skills", "project": ".agents/skills"},
    "grok": {"user": "~/.grok/skills", "project": ".grok/skills"},
    "factory": {"user": "~/.factory/skills", "project": ".agents/skills"},
    "kiro": {"user": "~/.kiro/skills", "project": ".agents/skills"},
    "slate": {"user": "~/.slate/skills", "project": ".agents/skills"},
    "hermes": {"user": "~/.hermes/skills", "project": ".agents/skills"},
}


# Documented aliases (LOOP_COMMANDS.md / AGENTS.md). Each gets its own router so
# skills-only tools resolve the alias too, not just the canonical command.
ALIASES: dict[str, str] = {
    "startup-discovery-loop": "plan-loop",
    "startup-build-loop": "product-develop",
    "develop-product": "product-develop",
    "all-in-one": "loop-engine",
}


def command_names() -> list[str]:
    if not COMMANDS_DIR.exists():
        return []
    return sorted(p.stem for p in COMMANDS_DIR.glob("*.md") if p.is_file())


def command_description(name: str) -> str:
    """First non-empty, non-heading line of the command file, cleaned for YAML."""
    path = COMMANDS_DIR / f"{name}.md"
    heading_seen = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            heading_seen = True
            continue
        if heading_seen:
            return re.sub(r"[`*\"]", "", line).strip()
    return f"Loop Engineering command /{name}"


def render_router(name: str, target: str | None = None) -> str:
    """Router for command `name`. When `target` differs, `name` is an alias that
    executes the `target` command's files."""
    target = target or name
    desc = command_description(target)
    if target != name:
        trigger = f" Alias for /{target}; invoke when the user types /{name}."
    else:
        trigger = f" Invoke when the user types /{name} or asks for this workflow."
    app = ROOT.as_posix()
    skill_line = (
        f"3. `{app}/skills/{target}/SKILL.md`\n"
        if (SKILLS_DIR / target / "SKILL.md").exists()
        else ""
    )
    return (
        "---\n"
        f"name: {name}\n"
        f'description: "{desc}{trigger}"\n'
        "---\n"
        f"<!-- {MARKER} name={name} -->\n\n"
        f"Loop Engineering OS - execute the `/{target}` command from the installed app.\n\n"
        f"**App root:** `{app}`\n"
        "(If that path is missing, run `loop home` - the app lives at `<home>/app`.)\n\n"
        "Read and execute these files from the app root, in order:\n\n"
        f"1. `{app}/AGENTS.md` (routing + non-negotiable rules)\n"
        f"2. `{app}/commands/{target}.md`\n"
        f"{skill_line}"
        "\nRun the command against the **active product workspace**: a local "
        "`.loop-engineer/` data dir auto-detected from the current directory, "
        "else the global `~/.loop-engineer/data/`. Do not ask the user to paste "
        "boot prompts.\n"
    )


def _project_root(raw: str | None) -> Path:
    """Normalize a workspace/data-dir path to the product root."""
    base = Path(raw).expanduser().resolve() if raw else Path.cwd()
    if base.name == ".loop-engineer":
        return base.parent
    if base.name == "data" and base.parent.name == ".loop-engineer":
        # global data home has no product root; caller should use --user
        return Path.cwd()
    return base


def host_selection(hosts: list[str] | None, detected_only: bool, project_root: Path, user_scope: bool) -> list[str]:
    names = hosts if hosts else list(HOSTS)
    names = [h for h in names if h in HOSTS]
    if not detected_only:
        return names
    picked = ["universal"]
    for h in names:
        if h == "universal":
            continue
        parent = _dest_for(h, "user" if user_scope else "project", project_root).parent
        if parent.exists():
            picked.append(h)
    # dedupe, keep order
    seen: set[str] = set()
    return [h for h in picked if h in names and not (h in seen or seen.add(h))]


def _dest_for(host: str, scope: str, project_root: Path) -> Path:
    raw = HOSTS[host][scope]
    if raw.startswith("~"):
        return Path(raw).expanduser().resolve()
    return (project_root / raw).resolve()


def iter_destinations(hosts: list[str], scope: str, project_root: Path):
    """Yield (host, dest_dir) for each host, de-duplicated by resolved path."""
    seen: set[Path] = set()
    for host in hosts:
        dest = _dest_for(host, scope, project_root)
        if dest in seen:
            continue
        seen.add(dest)
        yield host, dest


def read_manifest(dest: Path) -> dict:
    path = dest / MANIFEST_NAME
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def write_manifest(dest: Path, installed_dirs: list[str]) -> None:
    payload = {
        "generator": GENERATOR,
        "version": 3,
        "kind": "router",
        "app_root": ROOT.as_posix(),
        "installed": sorted(installed_dirs),
    }
    (dest / MANIFEST_NAME).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def _owned_by_loop(skill_dir: Path) -> bool:
    """A dir is ours if its SKILL.md carries the generated marker."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return False
    try:
        return MARKER in skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def install_dest(dest: Path, names: list[str], *, dry_run: bool) -> tuple[int, int, int]:
    """Write routers into one destination. Returns (written, skipped, pruned)."""
    manifest = read_manifest(dest)
    owned = set(manifest.get("installed", [])) if manifest.get("generator") == GENERATOR else set()

    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    # dir name -> (skill name, target command). Aliases point at their target.
    want: dict[str, tuple[str, str]] = {f"{DIR_PREFIX}{n}": (n, n) for n in names}
    for alias, target in ALIASES.items():
        if target in names:
            want[f"{DIR_PREFIX}{alias}"] = (alias, target)
    want_dirs = want
    written = 0
    skipped = 0
    for dir_name, (name, target) in want_dirs.items():
        dst = dest / dir_name
        if dst.exists() and dir_name not in owned and not _owned_by_loop(dst):
            skipped += 1
            continue
        if not dry_run:
            _remove(dst)
            dst.mkdir(parents=True, exist_ok=True)
            (dst / "SKILL.md").write_text(render_router(name, target), encoding="utf-8")
        written += 1

    # Prune routers we own that no longer map to a command (renamed/removed), and
    # bare-name dirs from older prefix-less installs (v1/v2) that carry our marker.
    pruned = 0
    if dest.exists():
        for entry in list(dest.iterdir()):
            if not entry.is_dir() or entry.name in want_dirs:
                continue
            stale = entry.name in owned or _owned_by_loop(entry)
            if stale:
                if not dry_run:
                    _remove(entry)
                pruned += 1

    if not dry_run:
        write_manifest(dest, list(want_dirs))
    return written, skipped, pruned


def uninstall_dest(dest: Path, *, dry_run: bool) -> int:
    manifest = read_manifest(dest)
    owned = set(manifest.get("installed", [])) if manifest.get("generator") == GENERATOR else set()
    removed = 0
    if dest.exists():
        for entry in list(dest.iterdir()):
            if entry.is_dir() and (entry.name in owned or _owned_by_loop(entry)):
                if not dry_run:
                    _remove(entry)
                removed += 1
        if not dry_run:
            _remove(dest / MANIFEST_NAME)
    return removed


def cmd_install(hosts: list[str], scope: str, project_root: Path, *, dry_run: bool) -> int:
    names = command_names()
    if not names:
        print(f"No command files found in {COMMANDS_DIR}", file=sys.stderr)
        return 1
    total_w = total_s = total_p = dests = 0
    for host, dest in iter_destinations(hosts, scope, project_root):
        w, s, p = install_dest(dest, names, dry_run=dry_run)
        dests += 1
        total_w += w
        total_s += s
        total_p += p
        flag = " (skipped some pre-existing)" if s else ""
        print(f"  [{host}] {w} router(s) -> {dest}{flag}")
    verb = "Would install" if dry_run else "Installed"
    print(f"{verb} routers to {dests} location(s); {total_w} written, {total_p} pruned, {total_s} skipped.")
    print("Routers point at the installed app; canonical command/skill edits need no reinstall.")
    if dry_run:
        print("Dry run only - re-run without --dry-run to apply.")
    return 0


def cmd_uninstall(hosts: list[str], scope: str, project_root: Path, *, dry_run: bool) -> int:
    total = dests = 0
    for host, dest in iter_destinations(hosts, scope, project_root):
        n = uninstall_dest(dest, dry_run=dry_run)
        if n:
            dests += 1
            total += n
            print(f"  [{host}] removed {n} -> {dest}")
    verb = "Would remove" if dry_run else "Removed"
    print(f"{verb} {total} router(s) from {dests} location(s).")
    return 0


def cmd_list(hosts: list[str], scope: str, project_root: Path) -> int:
    found = False
    for host, dest in iter_destinations(hosts, scope, project_root):
        manifest = read_manifest(dest)
        if manifest.get("generator") != GENERATOR:
            continue
        found = True
        installed = manifest.get("installed", [])
        print(f"[{host}] {dest}  ({len(installed)} routers, app: {manifest.get('app_root', '?')})")
    if not found:
        print("No Loop-installed routers found for the selected hosts/scope.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--workspace", default=None, help="Project root for project scope (default: cwd).")
    parser.add_argument("--user", action="store_true", help="Install to each agent's global skills dir (default when neither --user nor --project).")
    parser.add_argument("--project", action="store_true", help="Install to per-repo skills dirs under the workspace.")
    parser.add_argument("--host", action="append", dest="hosts", choices=list(HOSTS), help="Limit to one agent (repeatable). Default: all.")
    parser.add_argument("--detected-only", action="store_true", help="Only agents whose config dir already exists (plus universal).")
    parser.add_argument("--uninstall", action="store_true", help="Remove Loop-installed routers.")
    parser.add_argument("--list", action="store_true", help="Show what Loop installed.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change; write nothing.")
    args = parser.parse_args()

    scope = "project" if args.project else "user"
    project_root = _project_root(args.workspace)
    hosts = host_selection(args.hosts, args.detected_only, project_root, scope == "user")

    if args.list:
        return cmd_list(hosts, scope, project_root)
    if args.uninstall:
        return cmd_uninstall(hosts, scope, project_root, dry_run=args.dry_run)
    return cmd_install(hosts, scope, project_root, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
