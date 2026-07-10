"""Stage memory and skill writes for human approval."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def pending_root(workspace: Path) -> Path:
    return workspace / ".loop" / "pending"


def pending_memory_dir(workspace: Path) -> Path:
    return pending_root(workspace) / "memory"


def pending_skills_dir(workspace: Path) -> Path:
    return pending_root(workspace) / "skills"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def stage_memory_write(workspace: Path, *, target: str, action: str, content: str, reason: str) -> str:
    pending_memory_dir(workspace).mkdir(parents=True, exist_ok=True)
    write_id = uuid4().hex[:12]
    payload = {
        "id": write_id,
        "created_at": _now(),
        "target": target,
        "action": action,
        "content": content,
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


def list_pending(workspace: Path) -> list[dict]:
    items: list[dict] = []
    for folder, kind in ((pending_memory_dir(workspace), "memory"), (pending_skills_dir(workspace), "skill")):
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


def approve_pending(workspace: Path, write_id: str | None = None, approve_all: bool = False) -> list[str]:
    from memory_paths import user_skills_dir

    results: list[str] = []
    for item in list_pending(workspace):
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


def reject_pending(workspace: Path, write_id: str | None = None, reject_all: bool = False) -> list[str]:
    results: list[str] = []
    for item in list_pending(workspace):
        if not reject_all and item.get("id") != write_id:
            continue
        Path(item["_path"]).unlink(missing_ok=True)
        results.append(f"rejected {item['kind']} write {item['id']}")
        if not reject_all:
            break
    return results
