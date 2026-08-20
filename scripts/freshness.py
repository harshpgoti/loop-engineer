#!/usr/bin/env python3
r"""Is a generated file still true of the files it was generated from?

14 of 16 derived views in a real workspace were between 9 and 40 days stale, and the
session read order loaded them as if current - a `STATUS.md` reporting a registered
path the workspace has not used for months. A generated file needs to know what it
was generated *from*, and be checkable against it.

**Content hashes, not `built_at` timestamps.** Timestamps are the obvious choice and
the wrong one here, for reasons that are specific rather than theoretical:

- **git does not preserve mtimes.** Every clone, checkout, branch switch, stash pop or
  `checkout -- .` stamps files with *now*. Switch branches and back and every source is
  newer than every view, so the whole derived layer reports stale and an LLM
  regenerates dozens of markdown files - cost, reworded prose, unreviewable diff.
  Hashes are immune: checkout restores content, content hashes match, nothing is stale.
- **Windows makes it worse.** This workspace is on `H:\`. NTFS file tunneling restores
  the *original* timestamps when a file is deleted-and-recreated or renamed over within
  ~15s, which is exactly the write-then-rename that editors use for atomic saves. The
  result is a modified file with an old mtime - a false *clean*, the dangerous direction.
- **A timestamp cannot see a removed input.** Drop a source and every survivor is still
  older than the view; nothing ever rebuilds. A recorded input set notices immediately.
- **No early cutoff.** Rewording one decision marks every downstream view stale even
  when the regenerated output would be byte-identical.

This is the "verifying traces" rebuilder of Mokhov, Mitchell & Peyton Jones,
*Build Systems à la Carte* (ICFP 2018) - record the hashes of the inputs actually used,
rebuild iff one differs. Deliberately not "constructive traces" (needs a shared output
cache we do not have) nor Nix-style deep hashing (assumes a deterministic generator,
which an LLM is not).

Three failure modes this design has, all named in the literature and all guarded:

1. **Undeclared inputs.** Hashing fails *silently and permanently* when a generator
   reads something it did not declare - unlike mtime, which fails loud. `test_freshness`
   build-fuzzes this (Licker & Rice, ICSE 2019).
2. **Forgetting to hash the generator.** Make's most famous defect: edit the template
   and every existing view is wrong-but-clean. `generator.version` covers it.
3. **Line endings.** `core.autocrlf` on a fresh Windows clone would otherwise mark
   every file changed. Normalized before hashing.
"""

from __future__ import annotations

import argparse
import json
import re
from hashlib import sha256
from pathlib import Path

STAMP_START = "<!-- loop:freshness"
STAMP_END = "-->"

# Fields that change without changing meaning. Hashing raw bytes would make a view
# stale because a sibling line was re-dated. dbt learned this one in production: its
# `state:modified` deliberately ignores `tags` and `meta`.
VOLATILE = re.compile(
    r"(?im)^\s*(?:\*\*)?(?:updated|generated|last[ _-]?reviewed|date|as of)(?:\*\*)?\s*:.*$"
)


def normalize(text: str) -> str:
    """Semantic content only: CRLF folded, volatile lines dropped, edges trimmed."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = VOLATILE.sub("", text)
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def content_hash(path: Path) -> str | None:
    """Hash of a source file's semantic content, or None when it does not exist."""
    if not path.is_file():
        return None
    try:
        return sha256(normalize(path.read_text(encoding="utf-8", errors="ignore")).encode("utf-8")).hexdigest()[:16]
    except OSError:
        return None


def body_of(text: str) -> str:
    """The generated content, without its own stamp - a file is never its own input."""
    if text.startswith(STAMP_START):
        end = text.find(STAMP_END)
        if end != -1:
            return text[end + len(STAMP_END) :].lstrip("\n")
    return text


def stamp(
    view: Path,
    sources: list[Path],
    *,
    generator: str,
    version: int = 1,
    workspace: Path | None = None,
    command: str = "",
) -> None:
    """Prepend the provenance record to a generated file. Call after writing it."""
    if not view.is_file():
        return
    text = view.read_text(encoding="utf-8", errors="ignore")
    body = body_of(text)
    root = workspace or view.parent

    derived_from = []
    for source in sources:
        digest = content_hash(source)
        try:
            # Relative where possible so the stamp survives moving the workspace.
            rel = source.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            # A cross-workspace input - PARENT_CONTEXT.md derives from the parent
            # product's files. Absolute is the only honest record, and losing it to
            # a bare filename would silently point the check at the wrong file.
            rel = source.resolve().as_posix()
        derived_from.append({"path": rel, "hash": digest})

    record = {
        "generator": generator,
        "version": version,
        # Provenance, deliberately NOT a staleness input. Timestamps are excellent for
        # auditing and useless for invalidation; keeping the roles separate is the point.
        "command": command,
        "derived_from": derived_from,
        "output_hash": sha256(normalize(body).encode("utf-8")).hexdigest()[:16],
    }
    view.write_text(f"{STAMP_START} {json.dumps(record, sort_keys=True)} {STAMP_END}\n\n{body}", encoding="utf-8")


def read_stamp(view: Path) -> dict | None:
    if not view.is_file():
        return None
    try:
        head = view.read_text(encoding="utf-8", errors="ignore")[:4000]
    except OSError:
        return None
    if not head.startswith(STAMP_START):
        return None
    end = head.find(STAMP_END)
    if end == -1:
        return None
    try:
        return json.loads(head[len(STAMP_START) : end].strip())
    except json.JSONDecodeError:
        return None


def check(view: Path, *, workspace: Path | None = None, version: int | None = None) -> dict:
    """Why this view is or is not still true. Never raises.

    `fresh` is False with a reason; the reason names the specific input that moved, so
    a caller can regenerate one section rather than the whole file.
    """
    root = workspace or view.parent
    record = read_stamp(view)
    if record is None:
        return {"view": str(view), "fresh": False, "reason": "no provenance stamp", "changed": []}

    if version is not None and record.get("version") != version:
        return {
            "view": str(view),
            "fresh": False,
            "reason": f"generator changed (v{record.get('version')} -> v{version})",
            "changed": [],
        }

    changed: list[dict] = []
    for entry in record.get("derived_from", []):
        raw = Path(entry["path"])
        current = content_hash(raw if raw.is_absolute() else root / raw)
        if current == entry.get("hash"):
            continue
        changed.append(
            {
                "path": entry["path"],
                "was": entry.get("hash"),
                "now": current,
                # A removed input is invisible to any timestamp scheme.
                "gone": current is None,
            }
        )

    if changed:
        names = ", ".join(c["path"] + (" (removed)" if c["gone"] else "") for c in changed[:4])
        return {"view": str(view), "fresh": False, "reason": f"inputs changed: {names}", "changed": changed}

    body = body_of(view.read_text(encoding="utf-8", errors="ignore"))
    if record.get("output_hash") and sha256(normalize(body).encode("utf-8")).hexdigest()[:16] != record["output_hash"]:
        return {"view": str(view), "fresh": False, "reason": "hand-edited since generation", "changed": [], "edited": True}

    return {"view": str(view), "fresh": True, "reason": "", "changed": []}


def stale_views(workspace: Path) -> list[dict]:
    """Every stamped view in the workspace that no longer matches its inputs."""
    results = []
    for path in sorted(workspace.rglob("*.md")):
        if ".loop" in path.parts and "graph" in path.name:
            continue
        if read_stamp(path) is None:
            continue
        result = check(path, workspace=workspace)
        if not result["fresh"]:
            try:
                result["view"] = path.relative_to(workspace).as_posix()
            except ValueError:
                pass
            results.append(result)
    return results


def main() -> int:
    from workspace_utils import resolve_workspace

    parser = argparse.ArgumentParser(description="Which generated files no longer match their sources.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--all", action="store_true", help="List stamped views that are fresh too.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    stale = stale_views(workspace)
    stamped = sum(1 for p in workspace.rglob("*.md") if read_stamp(p) is not None)

    if not stamped:
        print("No generated file carries a provenance stamp yet.")
        return 0
    if not stale:
        print(f"All {stamped} stamped view(s) still match their sources.")
        return 0

    print(f"{len(stale)} of {stamped} stamped view(s) are out of date:\n")
    for item in stale:
        print(f"  {item['view']}")
        print(f"      {item['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
