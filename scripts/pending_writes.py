"""Queue for writes that need a human decision.

Deliberately narrow. A workspace's own memory is written directly at closeout -
routing it here made every session end with a chore, so nobody ever drained the
queue and memory stopped updating. What lands here is what a human actually has
to judge:

- a parent workspace proposing a change into a sub-product (which plan is wrong
  is a judgment call, and one workspace must never silently rewrite another)
- agent-authored skill files

Staging is idempotent by content, so a repeated session is a no-op rather than a
new copy (AGENTS.md non-negotiable #8).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
from uuid import uuid4


def pending_root(workspace: Path) -> Path:
    return workspace / ".loop" / "pending"


def pending_memory_dir(workspace: Path) -> Path:
    return pending_root(workspace) / "memory"


def pending_skills_dir(workspace: Path) -> Path:
    return pending_root(workspace) / "skills"


def pending_files_dir(workspace: Path) -> Path:
    return pending_root(workspace) / "files"


# Product-state files another workspace may *propose* a change to. Nothing else is
# writable across workspaces, and the guard is re-checked at approve time so a
# hand-edited pending file cannot widen it.
PENDING_FILE_ALLOWLIST = {
    "DOUBTS.md",
    "HANDOFF.md",
    "DECISIONS.md",
    "CURRENT_STATE.md",
}
PENDING_FILE_ALLOWED_PREFIXES = ("plan/",)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_file_target(relative_path: str) -> str:
    """Validate a staged file target. Raises ValueError when it is not allowed."""
    raw = str(relative_path or "").strip().replace("\\", "/").lstrip("/")
    if not raw:
        raise ValueError("empty target path")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("..", "") for part in path.parts):
        raise ValueError(f"target path must stay inside the workspace: {relative_path}")
    normalized = path.as_posix()
    if normalized in PENDING_FILE_ALLOWLIST:
        return normalized
    if any(normalized.startswith(prefix) for prefix in PENDING_FILE_ALLOWED_PREFIXES):
        return normalized
    allowed = ", ".join(sorted(PENDING_FILE_ALLOWLIST)) + ", plan/*"
    raise ValueError(f"target not allowed for cross-workspace writes: {normalized} (allowed: {allowed})")


def content_key(target: str, action: str, content: str) -> str:
    """Stable identity for a proposed write, so re-proposing it is a no-op."""
    digest = sha256("\x00".join((target, action, content.strip())).encode("utf-8"))
    return digest.hexdigest()[:16]


def stage_memory_write(workspace: Path, *, target: str, action: str, content: str, reason: str) -> str | None:
    """Propose a memory write.

    Returns None when an identical proposal is already queued. Staging runs at
    every closeout, and an unapproved proposal is by definition not yet in
    MEMORY.md - so without this guard the same entry re-stages every session and
    the queue grows without bound (AGENTS.md non-negotiable #8, idempotent
    workflows). Identity is the content itself, not a caller-supplied id.
    """
    key = content_key(target, action, content)
    for item in list_pending(workspace):
        if item.get("kind") == "memory" and item.get("content_key") == key:
            return None

    pending_memory_dir(workspace).mkdir(parents=True, exist_ok=True)
    write_id = uuid4().hex[:12]
    payload = {
        "id": write_id,
        "created_at": _now(),
        "target": target,
        "action": action,
        "content": content,
        "content_key": key,
        "reason": reason,
        "status": "pending",
    }
    path = pending_memory_dir(workspace) / f"{write_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return write_id


def stage_skill_write(workspace: Path, *, relative_path: str, content: str, reason: str) -> str:
    pending_skills_dir(workspace).mkdir(parents=True, exist_ok=True)
    write_id = uuid4().hex[:12]
    payload = {
        "id": write_id,
        "created_at": _now(),
        "relative_path": relative_path,
        "content": content,
        "reason": reason,
        "status": "pending",
    }
    path = pending_skills_dir(workspace) / f"{write_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return write_id


def stage_file_write(
    workspace: Path,
    *,
    relative_path: str,
    action: str,
    content: str,
    reason: str,
    origin: dict | None = None,
) -> str | None:
    """Propose a change to a product-state file - typically from another workspace.

    Returns the write id, or None when the same `origin.finding_id` is already
    staged, so a repeated session never piles up duplicate notes.
    """
    target = normalize_file_target(relative_path)
    origin = dict(origin or {})
    finding_id = origin.get("finding_id")
    if finding_id:
        for item in list_pending(workspace):
            if item.get("kind") == "file" and (item.get("origin") or {}).get("finding_id") == finding_id:
                return None

    pending_files_dir(workspace).mkdir(parents=True, exist_ok=True)
    write_id = uuid4().hex[:12]
    payload = {
        "id": write_id,
        "created_at": _now(),
        "relative_path": target,
        "action": action if action in ("append", "replace") else "append",
        "content": content,
        "reason": reason,
        "origin": origin,
        "status": "pending",
    }
    path = pending_files_dir(workspace) / f"{write_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return write_id


def list_pending(workspace: Path) -> list[dict]:
    items: list[dict] = []
    for folder, kind in (
        (pending_memory_dir(workspace), "memory"),
        (pending_skills_dir(workspace), "skill"),
        (pending_files_dir(workspace), "file"),
    ):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["kind"] = kind
            data["_path"] = str(path)
            if data.get("status") == "pending":
                items.append(data)
    return items


def _memory_target_path(workspace: Path, target: str) -> Path:
    from memory_paths import memory_file, soul_file, user_file

    if target == "user":
        return user_file(workspace)
    if target == "soul":
        return soul_file(workspace)
    return memory_file(workspace)


def approve_pending(
    workspace: Path,
    write_id: str | None = None,
    approve_all: bool = False,
    kind: str | None = None,
) -> list[str]:
    from memory_paths import user_skills_dir

    results: list[str] = []
    for item in list_pending(workspace):
        if kind and item.get("kind") != kind:
            continue
        if not approve_all and item.get("id") != write_id:
            continue
        if item["kind"] == "memory":
            target_path = _memory_target_path(workspace, str(item.get("target", "memory")))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if item.get("action") == "replace":
                target_path.write_text(item["content"], encoding="utf-8")
            else:
                existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
                entry = item["content"].strip()
                sep = "\n§\n" if existing.strip() else ""
                target_path.write_text(existing.rstrip() + sep + entry + "\n", encoding="utf-8")
            results.append(f"approved memory write {item['id']}")
        elif item["kind"] == "file":
            try:
                target = normalize_file_target(str(item.get("relative_path", "")))
            except ValueError as exc:
                results.append(f"rejected file write {item['id']}: {exc}")
                Path(item["_path"]).unlink(missing_ok=True)
                if not approve_all:
                    break
                continue
            target_path = (workspace / target).resolve()
            if not str(target_path).startswith(str(workspace.resolve())):
                results.append(f"rejected file write {item['id']}: resolves outside workspace")
                Path(item["_path"]).unlink(missing_ok=True)
                if not approve_all:
                    break
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if item.get("action") == "replace":
                target_path.write_text(item["content"], encoding="utf-8")
            else:
                existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""
                entry = item["content"].strip()
                sep = "\n\n" if existing.strip() else ""
                target_path.write_text(existing.rstrip() + sep + entry + "\n", encoding="utf-8")
            results.append(f"approved file write {item['id']} -> {target}")
        else:
            rel = item.get("relative_path", f"draft-{item['id']}.md")
            dest = user_skills_dir(workspace) / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item["content"], encoding="utf-8")
            results.append(f"approved skill write {item['id']} -> skills/{rel}")
        Path(item["_path"]).unlink(missing_ok=True)
        if not approve_all:
            break
    return results


def dedupe_pending(workspace: Path, *, dry_run: bool = False) -> list[str]:
    """Collapse queued writes that propose identical content, keeping the oldest.

    Queues built before staging became idempotent hold the same proposal dozens
    of times. Dropping the copies loses no information and makes the remainder
    reviewable, which is the point of a queue that needs a human.
    """
    results: list[str] = []
    seen: set[tuple[str, str]] = set()
    for item in sorted(list_pending(workspace), key=lambda i: str(i.get("created_at", ""))):
        kind = str(item.get("kind", ""))
        if kind == "memory":
            key = item.get("content_key") or content_key(
                str(item.get("target", "")), str(item.get("action", "")), str(item.get("content", ""))
            )
        elif kind == "file":
            key = content_key(
                str(item.get("relative_path", "")), str(item.get("action", "")), str(item.get("content", ""))
            )
        else:
            key = content_key(str(item.get("relative_path", "")), "skill", str(item.get("content", "")))

        if (kind, key) in seen:
            if not dry_run:
                Path(item["_path"]).unlink(missing_ok=True)
            results.append(f"{'would drop' if dry_run else 'dropped'} duplicate {kind} write {item['id']}")
            continue
        seen.add((kind, key))
    return results


def reject_pending(
    workspace: Path,
    write_id: str | None = None,
    reject_all: bool = False,
    kind: str | None = None,
) -> list[str]:
    results: list[str] = []
    for item in list_pending(workspace):
        if kind and item.get("kind") != kind:
            continue
        if not reject_all and item.get("id") != write_id:
            continue
        Path(item["_path"]).unlink(missing_ok=True)
        results.append(f"rejected {item['kind']} write {item['id']}")
        if not reject_all:
            break
    return results
