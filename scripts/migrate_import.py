#!/usr/bin/env python3
"""Import memory and skills from an external agent workspace into Loop Engineer."""

from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

from memory_paths import ensure_memory_layout, state_db, user_skills_dir
from session_store import init_db, log_session
from workspace_utils import resolve_workspace


IMPORT_FILES = (
    ("MEMORY.md", "memories/MEMORY.md"),
    ("USER.md", "memories/USER.md"),
    ("SOUL.md", "memories/SOUL.md"),
    ("AGENTS.md", "AGENTS.imported.md"),
)

# Maps IMPORT_FILES dest_rel -> the key ensure_memory_layout() reports it under,
# so run_import() can tell "freshly created placeholder" (safe to supersede)
# from "genuinely pre-existing content" (respect --overwrite).
MEMORY_ACTION_KEYS = {
    "memories/MEMORY.md": "MEMORY.md",
    "memories/USER.md": "USER.md",
    "memories/SOUL.md": "SOUL.md",
}


def find_source_root(explicit: str | None) -> Path | None:
    if not explicit:
        return None
    path = Path(explicit).expanduser().resolve()
    return path if path.exists() else None


def copy_if_exists(source_root: Path, relative: str, target: Path, dry_run: bool) -> str:
    """Copy source_root/relative to target. Caller decides whether target may be written —
    this function does not re-check target.exists() for that decision."""
    src = source_root / relative
    if not src.exists():
        return "missing"
    if dry_run:
        return "would-copy"
    target.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(src, target)
        return "copied-dir"
    shutil.copy2(src, target)
    return "copied"


def import_skills(source_root: Path, workspace: Path, dry_run: bool, overwrite: bool) -> list[str]:
    results: list[str] = []
    candidates = [
        source_root / "skills",
        source_root / "workspace" / "skills",
    ]
    target_root = user_skills_dir(workspace) / "imported"
    for src in candidates:
        if not src.exists():
            continue
        if dry_run:
            results.append(f"would import skills from {src}")
            continue
        target_root.mkdir(parents=True, exist_ok=True)
        for item in src.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(src)
            dest = target_root / rel
            if dest.exists() and not overwrite:
                results.append(f"skipped skill {rel}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            results.append(f"imported skill {rel}")
    return results


def append_handoff(workspace: Path, summary: list[str]) -> None:
    path = workspace / "HANDOFF.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} — External workspace import\n\n"
            + "".join(f"- {line}\n" for line in summary)
            + "- Review imported files under `memories/` and `skills/imported/`.\n"
            + "- Secrets/API keys were not copied automatically; configure them manually.\n"
        )


def run_import(
    workspace: Path,
    source: str,
    *,
    dry_run: bool = False,
    overwrite: bool = False,
    preset: str = "full",
    log_command: str = "/migrate-import",
    memory_actions: dict[str, str] | None = None,
) -> list[str]:
    """Import memory/skills from `source` into `workspace`. Returns a summary line list.

    Shared by the standalone `/migrate-import` command and `/setup-loop-engine --source`.

    `memory_actions`: pass the dict already returned by a caller's own
    `ensure_memory_layout()` call (e.g. `/setup-loop-engine` seeding starter files)
    so this function knows which memory files are brand-new placeholders — safe for
    the import to supersede — versus genuinely pre-existing content. If omitted,
    this function calls `ensure_memory_layout()` itself (standalone `/migrate-import`
    usage, where nothing has touched memory yet).
    """
    source_root = find_source_root(source)
    if source_root is None:
        raise SystemExit(f"Source path not found: {source}")

    workspace.mkdir(parents=True, exist_ok=True)
    if memory_actions is None:
        memory_actions = ensure_memory_layout(workspace)
    else:
        ensure_memory_layout(workspace)  # idempotent: ensures dirs/state.db exist
    init_db(state_db(workspace))

    # Files ensure_memory_layout() just seeded with Loop Engineer's own placeholder
    # content (not real prior data) — safe for an import to supersede even without
    # --overwrite, otherwise a fresh `setup --source` can never actually land memory.
    freshly_seeded = {
        dest_rel
        for dest_rel, key in MEMORY_ACTION_KEYS.items()
        if memory_actions.get(key, "").startswith("created")
    }

    summary: list[str] = []
    for src_name, dest_rel in IMPORT_FILES:
        if preset == "user-data" and src_name == "AGENTS.md":
            continue
        dest = workspace / dest_rel
        force = dest_rel in freshly_seeded
        if dest.exists() and not overwrite and not force:
            summary.append(f"skipped existing {dest_rel}")
            continue
        status = copy_if_exists(source_root, src_name, dest, dry_run)
        summary.append(f"{src_name} -> {dest_rel}: {status}")

    workspace_candidates = [source_root / "workspace", source_root]
    for candidate in workspace_candidates:
        if candidate.exists():
            skill_results = import_skills(candidate, workspace, dry_run, overwrite)
            summary.extend(skill_results or [f"no skills under {candidate}"])
            break

    if not dry_run:
        append_handoff(workspace, summary)
        log_session(
            state_db(workspace),
            workspace=str(workspace),
            command=log_command,
            title="External workspace import",
            body="\n".join(summary),
            tags="migration import",
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Import external memory/skills into a Loop workspace.")
    parser.add_argument("--workspace", default=None, help="Target product workspace.")
    parser.add_argument("--source", required=True, help="Source directory containing MEMORY.md, skills/, etc.")
    parser.add_argument("--dry-run", action="store_true", help="Preview import without writing.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing imported files.")
    parser.add_argument(
        "--preset",
        choices=("full", "user-data"),
        default="full",
        help="full imports memory/skills/agents; user-data skips AGENTS.md.",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Also classify every other file in --source by content and route it "
        "(memory/user/soul -> memories/, how-tos -> skills/imported/, plans -> plan/imported/).",
    )
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    summary = run_import(
        workspace,
        args.source,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        preset=args.preset,
    )
    if args.scan:
        from import_scanner import run_scan_import

        source_root = find_source_root(args.source)
        scan_summary = run_scan_import(
            workspace, source_root, dry_run=args.dry_run, exclude_known=True
        )
        summary.extend(scan_summary)
        if not args.dry_run:
            append_handoff(workspace, scan_summary)

    print(f"Source: {Path(args.source).expanduser().resolve()}")
    print(f"Target workspace: {workspace}")
    for line in summary:
        print(f"- {line}")
    if args.dry_run:
        print("\nDry run only. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
