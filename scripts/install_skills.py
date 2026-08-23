#!/usr/bin/env python3
"""Install thin router skills into every coding agent, pointing at the installed app.

Requirement: whether the user works globally or inside a project, any coding
agent must be able to run every Loop command (`/plan-loop`, `/develop-product`,
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

Exactly one router per command must be visible to each agent, or every command
shows up twice in its menu. Two sources of doubles are handled at install time:
`~/.agents/skills` is skipped at user scope, since the agents that read it
(codex, gemini, ...) also have their own global dir; and the flat command
wrappers written by Loop <= v2 are pruned unless `--keep-legacy-commands` is
passed. That prune is the migration path off the old generator (removed in v3)
and must outlive it - installs from before the switch still have those files.

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

# Loop <= v2 also generated flat command wrappers via a per-tool generator that
# v3 removed. Claude Code unifies slash commands and skills in
# one namespace, so a leftover `~/.claude/commands/plan-loop.md` next to the
# `loop-plan-loop` router lists `/plan-loop` twice; for the others the wrappers
# are dead weight pointing at the same app. Install prunes any file carrying our
# marker, and never touches hand-written commands. Codex's legacy wrappers went
# to `~/.codex/skills/<name>/SKILL.md` (bare, unprefixed) and are already caught
# by the stale-router prune in `install_dest`.
LEGACY_COMMAND_DIRS: dict[str, dict[str, str]] = {
    "claude": {"user": "~/.claude/commands", "project": ".claude/commands"},
    "cursor": {"user": "~/.cursor/commands", "project": ".cursor/commands"},
    "opencode": {"user": "~/.config/opencode/commands", "project": ".opencode/commands"},
}


# Documented aliases (LOOP_COMMANDS.md / AGENTS.md). Each gets its own router so
# skills-only tools resolve the alias too, not just the canonical command.
ALIASES: dict[str, str] = {
    "startup-discovery-loop": "plan-loop",
    "startup-build-loop": "develop-product",
    "all-in-one": "loop-engine",
}


# Some agents unify slash commands and skills in one namespace; opencode does not.
# There, a skill is model-invoked - the agent chooses it from its description - and
# `/name` reads a separate command directory. Installing only skills left `opencode
# debug skill` listing all 36 routers while `/plan-loop` matched nothing, because the
# user was typing into the namespace we had not populated.
#
# Paths are opencode's own documented layout (`opencode debug skill` -> the built-in
# `customize-opencode` skill): `~/.config/opencode/command/<name>.md`, singular.
SLASH_COMMAND_HOSTS: dict[str, dict[str, str]] = {
    "opencode": {"user": "~/.config/opencode/command", "project": ".opencode/command"},
}


# A router points at the installed app, which by construction sits outside whatever
# product folder the user is working in. opencode guards reads outside the project with
# its `external_directory` permission, so without a rule it asks on the first loop
# command in every new workspace - and the answer is always yes, which makes it a prompt
# that teaches people to click through prompts.
#
# Config lives at `~/.config/opencode/opencode.json[c]`. opencode hard-fails on invalid
# config, so this only ever writes a file it could parse, and never edits a value the
# user already set.
PERMISSION_HOSTS: dict[str, dict[str, str]] = {
    "opencode": {"user": "~/.config/opencode", "project": ".opencode"},
}
CONFIG_NAMES = ("opencode.jsonc", "opencode.json")
SCHEMA_URL = "https://opencode.ai/config.json"


def app_globs() -> list[str]:
    """Paths a router may send an agent to read, as permission globs."""
    globs = ["~/.loop-engineer/**"]
    try:
        from loop_home import loop_home

        home = loop_home().resolve().as_posix()
        if not home.startswith(str(Path.home().as_posix()) + "/.loop-engineer"):
            globs.append(f"{home}/**")
    except Exception:  # noqa: BLE001 - a missing home must not stop the install
        pass
    app = APP_ROOT.resolve().as_posix()
    if not any(app.startswith(g.rstrip("*").rstrip("/").replace("~", Path.home().as_posix())) for g in globs):
        globs.append(f"{app}/**")
    return globs


def _config_path(folder: Path) -> Path:
    for name in CONFIG_NAMES:
        if (folder / name).is_file():
            return folder / name
    return folder / CONFIG_NAMES[1]


def ensure_permissions(folder: Path, *, dry_run: bool) -> tuple[Path, list[str], str]:
    """Grant read access to the app root. Returns (path, globs added, note)."""
    path = _config_path(folder)
    config: dict = {}
    if path.is_file():
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            config = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            # Comments, trailing commas, or a hand-rolled JSONC file. Rewriting it
            # would drop whatever the author wrote there, and a broken opencode config
            # stops opencode starting - so say what to add and change nothing.
            return path, [], "not plain JSON - left alone"
    if not isinstance(config, dict):
        return path, [], "not an object - left alone"

    permission = config.setdefault("permission", {})
    if not isinstance(permission, dict):
        return path, [], "`permission` is not an object - left alone"
    external = permission.setdefault("external_directory", {})
    if isinstance(external, str):
        return path, [], f"`external_directory` is already {external!r} - left alone"
    if not isinstance(external, dict):
        return path, [], "`external_directory` is not an object - left alone"

    added: list[str] = []
    # opencode evaluates the LAST matching rule, so the broad default goes in first and
    # every allow is appended after it.
    if not external:
        external["*"] = "ask"
        added.append("*")
    for glob in app_globs():
        if glob in external:
            continue
        external[glob] = "allow"
        added.append(glob)

    if not added:
        return path, [], "already granted"
    config.setdefault("$schema", SCHEMA_URL)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path, added, ""


def render_command(name: str, target: str | None = None) -> str:
    """A slash command for a host that keeps commands separate from skills.

    The filename is the command, so the frontmatter carries no `name`; the body is
    the template opencode runs when the user types `/<name>`.
    """
    target = target or name
    desc = command_description(target)
    body = render_router(name, target).split("---\n", 2)[-1].lstrip()
    return "---\n" + f'description: "{desc}"\n' + "---\n\n" + body


def install_commands(dest: Path, names: list[str], *, dry_run: bool) -> tuple[int, int]:
    """Write slash commands into one directory. Returns (written, pruned)."""
    want: dict[str, str] = {n: n for n in names}
    for alias, target in ALIASES.items():
        if target in names:
            want[alias] = target

    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)

    written = 0
    for name, target in want.items():
        path = dest / f"{name}.md"
        # Never clobber a command the user wrote themselves.
        if path.exists() and MARKER not in path.read_text(encoding="utf-8", errors="ignore"):
            continue
        if not dry_run:
            path.write_text(render_command(name, target), encoding="utf-8")
        written += 1

    pruned = 0
    if dest.exists():
        for entry in dest.glob("*.md"):
            if entry.stem in want:
                continue
            if MARKER in entry.read_text(encoding="utf-8", errors="ignore"):
                if not dry_run:
                    entry.unlink()
                pruned += 1
    return written, pruned


def _check_aliases() -> None:
    """An alias pointing at itself would install a router shadowing the real command.

    The rename of `product-develop` to `develop-product` produced exactly that for one
    commit: the old alias key and its new target became the same string.
    """
    for alias, target in ALIASES.items():
        if alias == target:
            raise SystemExit(f"ALIASES: `{alias}` points at itself - drop the row or fix the target.")


def command_names() -> list[str]:
    if not COMMANDS_DIR.exists():
        return []
    return sorted(p.stem for p in COMMANDS_DIR.glob("*.md") if p.is_file())


# Where the routers send agents. Running install from a working checkout used to point
# every router at that checkout - so a user who happened to have the repo cloned had
# their routers silently repointed at it, and `/loop-engine` in an unrelated product
# started reading `<checkout>/AGENTS.md`. The installed runtime is the default target
# whenever it exists; `--from-here` is how a contributor aims at their checkout, and the
# summary always prints which one was used so it can never move without saying so.
def router_app_root(from_here: bool = False) -> Path:
    if from_here:
        return ROOT
    try:
        from loop_home import app_path

        installed = app_path()
    except Exception:  # noqa: BLE001 - no loop home yet; this checkout is the runtime
        return ROOT
    if installed.resolve() == ROOT.resolve():
        return ROOT
    if (installed / "AGENTS.md").is_file():
        return installed
    return ROOT


APP_ROOT = ROOT


def set_app_root(path: Path) -> None:
    global APP_ROOT
    APP_ROOT = path


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
    app = APP_ROOT.as_posix()
    skill_line = (
        f"3. `{app}/skills/{target}/SKILL.md`\n"
        if (SKILLS_DIR / target / "SKILL.md").exists()
        else ""
    )
    return (
        "---\n"
        # opencode documents that a skill's `name` must match its folder, and the
        # folder carries DIR_PREFIX. Claude Code already addresses these by folder
        # name, so matching is right everywhere and wrong nowhere.
        f"name: {DIR_PREFIX}{name}\n"
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


def _resolve(raw: str, project_root: Path) -> Path:
    if raw.startswith("~"):
        return Path(raw).expanduser().resolve()
    return (project_root / raw).resolve()


def _dest_for(host: str, scope: str, project_root: Path) -> Path:
    return _resolve(HOSTS[host][scope], project_root)


def install_hosts(hosts: list[str], scope: str) -> list[str]:
    """Drop the redundant `universal` destination at user scope.

    Every host in HOSTS has its own global skills dir, and the universal-dir
    readers (codex, gemini, factory, kiro, slate, hermes - the rows whose
    project path is `.agents/skills`) read `~/.agents/skills` *as well as*
    their own. Writing both lists every command twice in those tools. At project
    scope the paths already collapse in `iter_destinations`, so nothing changes
    there; `--host universal` still installs it when asked for explicitly.
    """
    if scope != "user" or "universal" not in hosts or hosts == ["universal"]:
        return hosts
    return [h for h in hosts if h != "universal"]


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
        "app_root": APP_ROOT.as_posix(),
        "installed": sorted(installed_dirs),
    }
    (dest / MANIFEST_NAME).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def _is_bootstrap(skill_dir: Path) -> bool:
    """`loop team-init` writes a `loop-engineer` bootstrap skill that carries the
    same generated marker but is not a router - it is a committed team artifact
    describing how to install Loop. It must survive install and uninstall."""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return False
    try:
        return "kind=bootstrap" in skill_md.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


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
            stale = (entry.name in owned or _owned_by_loop(entry)) and not _is_bootstrap(entry)
            if stale:
                if not dry_run:
                    _remove(entry)
                pruned += 1

    if not dry_run:
        write_manifest(dest, list(want_dirs))
    return written, skipped, pruned


def prune_legacy_commands(host: str, scope: str, project_root: Path, *, dry_run: bool) -> tuple[Path | None, int]:
    """Delete this host's marker-carrying wrappers from the deprecated generator."""
    cfg = LEGACY_COMMAND_DIRS.get(host)
    if cfg is None:
        return None, 0
    dest = _resolve(cfg[scope], project_root)
    if not dest.is_dir():
        return None, 0
    removed = 0
    for path in sorted(dest.glob("*.md")):
        try:
            body = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if MARKER not in body:
            continue  # never touch hand-written commands
        if not dry_run:
            path.unlink()
        removed += 1
    return dest, removed


def uninstall_dest(dest: Path, *, dry_run: bool) -> int:
    manifest = read_manifest(dest)
    owned = set(manifest.get("installed", [])) if manifest.get("generator") == GENERATOR else set()
    removed = 0
    if dest.exists():
        for entry in list(dest.iterdir()):
            if entry.is_dir() and (entry.name in owned or _owned_by_loop(entry)) and not _is_bootstrap(entry):
                if not dry_run:
                    _remove(entry)
                removed += 1
        if not dry_run:
            _remove(dest / MANIFEST_NAME)
    return removed


def cmd_install(
    hosts: list[str],
    scope: str,
    project_root: Path,
    *,
    dry_run: bool,
    keep_legacy: bool = False,
    from_here: bool = False,
) -> int:
    set_app_root(router_app_root(from_here))
    print(f"Routers will point at: {APP_ROOT}")
    _check_aliases()
    names = command_names()
    if not names:
        print(f"No command files found in {COMMANDS_DIR}", file=sys.stderr)
        return 1
    selected = install_hosts(hosts, scope)
    total_w = total_s = total_p = dests = 0
    for host, dest in iter_destinations(selected, scope, project_root):
        w, s, p = install_dest(dest, names, dry_run=dry_run)
        dests += 1
        total_w += w
        total_s += s
        total_p += p
        flag = " (skipped some pre-existing)" if s else ""
        print(f"  [{host}] {w} router(s) -> {dest}{flag}")

    # A previous version installed the universal dir at user scope too; sweep it
    # so the tools that read both stop listing every command twice.
    for host in hosts:
        if host in selected:
            continue
        dest = _dest_for(host, scope, project_root)
        n = uninstall_dest(dest, dry_run=dry_run)
        total_p += n
        if n:
            print(f"  [{host}] removed {n} duplicate router(s) -> {dest}  (covered by each agent's own dir)")

    for host in selected:
        cfg = SLASH_COMMAND_HOSTS.get(host)
        if not cfg:
            continue
        cmd_dest = _resolve(cfg[scope], project_root)
        w, n = install_commands(cmd_dest, names, dry_run=dry_run)
        total_w += w
        total_p += n
        print(f"  [{host}] {w} slash command(s) -> {cmd_dest}")

    for host in selected:
        cfg = PERMISSION_HOSTS.get(host)
        if not cfg:
            continue
        path, added, note = ensure_permissions(_resolve(cfg[scope], project_root), dry_run=dry_run)
        if added:
            print(f"  [{host}] granted read access to the app in {path}: {', '.join(added)}")
        elif note not in ("", "already granted"):
            print(f"  [{host}] {path}: {note} - add this yourself:")
            print('           "permission": {"external_directory": {"*": "ask", "~/.loop-engineer/**": "allow"}}')

    if not keep_legacy:
        for host in hosts:
            legacy_dest, n = prune_legacy_commands(host, scope, project_root, dry_run=dry_run)
            total_p += n
            if n:
                print(f"  [{host}] removed {n} legacy command wrapper(s) -> {legacy_dest}  (superseded by routers)")

    verb = "Would install" if dry_run else "Installed"
    print(f"{verb} routers to {dests} location(s); {total_w} written, {total_p} pruned, {total_s} skipped.")
    print(f"Routers point at {APP_ROOT}; canonical command/skill edits need no reinstall.")
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
    for host in hosts:
        legacy_dest, n = prune_legacy_commands(host, scope, project_root, dry_run=dry_run)
        if n:
            dests += 1
            total += n
            print(f"  [{host}] removed {n} legacy command wrapper(s) -> {legacy_dest}")
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
    parser.add_argument(
        "--from-here",
        action="store_true",
        help="Point routers at this checkout instead of the installed runtime.",
    )
    parser.add_argument("--keep-legacy-commands", action="store_true", help="Keep pre-router command wrappers left by Loop <= v2 instead of pruning them.")
    args = parser.parse_args()

    scope = "project" if args.project else "user"
    project_root = _project_root(args.workspace)
    hosts = host_selection(args.hosts, args.detected_only, project_root, scope == "user")

    if args.list:
        return cmd_list(hosts, scope, project_root)
    if args.uninstall:
        return cmd_uninstall(hosts, scope, project_root, dry_run=args.dry_run)
    return cmd_install(
        hosts, scope, project_root, dry_run=args.dry_run, keep_legacy=args.keep_legacy_commands
    , from_here=args.from_here)


if __name__ == "__main__":
    raise SystemExit(main())
