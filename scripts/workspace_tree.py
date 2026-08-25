"""Product hierarchy: a main product workspace and its sub-product workspaces.

Workspace resolution (`workspace_resolver`) only walks *upward* - from a sub-product
folder it finds that sub-product's `.loop-engineer/`. This module adds the missing
downward and upward *links* so a main-product session can see its sub-products and a
sub-product session can see the constraints it inherits.

State lives in `<workspace>/.loop/workspace.json`:

    {"role": "main", "children": [{"name": "auth-svc", "path": "auth-svc", ...}]}
    {"role": "sub",  "parent": "..", "map_id": "02"}

No file means `standalone` - every workspace that predates this feature keeps
behaving exactly as before.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from source_tree_scan import SKIP_DIRS
from workspace_resolver import (
    LOCAL_DATA_DIRNAME,
    has_local_loop_data,
    is_global_data_home,
    local_data_dir,
)


WORKSPACE_META = ".loop/workspace.json"

ROLE_MAIN = "main"
ROLE_SUB = "sub"
ROLE_STANDALONE = "standalone"
ROLES = (ROLE_MAIN, ROLE_SUB, ROLE_STANDALONE)

DEFAULT_SCAN_DEPTH = 3

# Never descend into these while looking for sub-products.
SCAN_SKIP_DIRS = set(SKIP_DIRS) | {LOCAL_DATA_DIRNAME, ".loop", "site-packages"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------


def meta_path(workspace: Path) -> Path:
    return workspace / WORKSPACE_META


def product_folder(workspace: Path) -> Path | None:
    """The folder a workspace describes - the parent of `.loop-engineer/`.

    Returns None for the global data home, which has no product folder and
    therefore cannot take part in a hierarchy.
    """
    resolved = workspace.resolve()
    if is_global_data_home(resolved):
        return None
    if resolved.name == LOCAL_DATA_DIRNAME:
        return resolved.parent
    # Legacy flat layout: data sits directly in the product folder.
    return resolved


def data_dir_for(folder: Path) -> Path:
    """The workspace path for a product folder (new nested layout, else itself)."""
    nested = local_data_dir(folder)
    if nested.is_dir():
        return nested
    return folder


def relpath(from_folder: Path, target: Path) -> str:
    """POSIX relative path, falling back to absolute across drives (Windows)."""
    try:
        return Path(os.path.relpath(target, from_folder)).as_posix()
    except ValueError:
        return target.resolve().as_posix()


def _resolve_child_path(folder: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path.resolve()
    return (folder / path).resolve()


# ---------------------------------------------------------------------------
# meta read / write
# ---------------------------------------------------------------------------


def read_meta(workspace: Path) -> dict:
    """Tolerant read - a malformed file must never break a session."""
    path = meta_path(workspace)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def write_meta(workspace: Path, data: dict) -> Path:
    path = meta_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(data)
    payload["updated_at"] = _now()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def get_role(workspace: Path) -> str:
    role = read_meta(workspace).get("role")
    return role if role in ROLES else ROLE_STANDALONE


def role_is_pinned(workspace: Path) -> bool:
    """True when the user set the role explicitly (`loop workspace role ...`)."""
    return read_meta(workspace).get("role_source") == "user"


def set_role(workspace: Path, role: str, *, pinned: bool = True) -> dict:
    if role not in ROLES:
        raise ValueError(f"unknown role: {role} (expected one of {', '.join(ROLES)})")
    meta = read_meta(workspace)
    meta["role"] = role
    meta["role_source"] = "user" if pinned else "auto"
    if role != ROLE_MAIN:
        meta.pop("children", None)
    if role != ROLE_SUB:
        meta.pop("parent", None)
    write_meta(workspace, meta)
    return meta


# ---------------------------------------------------------------------------
# discovery
# ---------------------------------------------------------------------------


def scan_children(folder: Path, max_depth: int = DEFAULT_SCAN_DEPTH) -> list[Path]:
    """Product folders under `folder` that hold their own loop data.

    A discovered sub-product is not descended into - its own sub-products belong
    to it, not to this workspace.
    """
    found: list[Path] = []
    if max_depth < 1 or not folder.is_dir():
        return found

    def walk(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError:
            return
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            name = entry.name
            if name in SCAN_SKIP_DIRS or name.startswith("."):
                continue
            child = Path(entry.path)
            if has_local_loop_data(child):
                found.append(child.resolve())
                continue
            walk(child, depth + 1)

    walk(folder, 1)
    return found


def _map_rows(workspace: Path) -> list[dict]:
    try:
        from ultraplan_harness import parse_product_map

        return parse_product_map(workspace)
    except Exception:
        return []


def map_id_for(workspace: Path, child_name: str) -> str | None:
    """PRODUCT_MAP row id bound to this sub-product folder.

    Two sources, both exact: a row whose `Workspace` column names the folder, or a
    row whose `Title` slug equals the folder name. A substring fallback used to sit
    here and would bind a folder named `api` to whichever of `api-gateway` or
    `public-api` appeared first in the map. A silent mis-binding is worse than none:
    every downstream check then reads a row that belongs to a different sub-product.
    When neither matches, bind it explicitly - `loop workspace link <path> --map-id NN`.
    """
    from plan_paths import slugify

    target = slugify(child_name)
    if not target:
        return None
    rows = _map_rows(workspace)
    for row in rows:
        declared = str(row.get("workspace", "")).strip().strip("`/")
        if declared and slugify(Path(declared).name) == target:
            return row.get("id")
    for row in rows:
        if slugify(row.get("title", "")) == target:
            return row.get("id")
    return None


def resolve_children(workspace: Path, max_depth: int = DEFAULT_SCAN_DEPTH) -> list[dict]:
    """Scanned children merged with explicitly linked ones.

    Each entry: name, path (relative), folder, data_dir, map_id, source, missing.
    """
    folder = product_folder(workspace)
    if folder is None:
        return []

    merged: dict[str, dict] = {}

    for stored in read_meta(workspace).get("children", []) or []:
        if not isinstance(stored, dict) or not stored.get("path"):
            continue
        child_folder = _resolve_child_path(folder, str(stored["path"]))
        merged[str(child_folder)] = {
            "name": stored.get("name") or child_folder.name,
            "path": relpath(folder, child_folder),
            "folder": child_folder,
            "data_dir": data_dir_for(child_folder),
            "map_id": stored.get("map_id"),
            "source": stored.get("source") or "link",
            "missing": not has_local_loop_data(child_folder),
        }

    for child_folder in scan_children(folder, max_depth=max_depth):
        key = str(child_folder)
        if key in merged:
            merged[key]["missing"] = False
            continue
        merged[key] = {
            "name": child_folder.name,
            "path": relpath(folder, child_folder),
            "folder": child_folder,
            "data_dir": data_dir_for(child_folder),
            "map_id": None,
            "source": "scan",
            "missing": False,
        }

    children = sorted(merged.values(), key=lambda item: item["name"].lower())
    for child in children:
        if not child.get("map_id"):
            child["map_id"] = map_id_for(workspace, child["name"])
    return children


def resolve_parent(workspace: Path, max_depth: int = DEFAULT_SCAN_DEPTH) -> dict | None:
    """The main workspace this one belongs to, or None.

    An explicit `parent` wins. Otherwise the nearest ancestor holding loop data
    counts as the parent only if it would discover us - the same rule the main
    side scans by, so the link can never be one-way by accident.
    """
    folder = product_folder(workspace)
    if folder is None:
        return None

    stored = read_meta(workspace).get("parent")
    if stored:
        parent_folder = _resolve_child_path(folder, str(stored))
        if has_local_loop_data(parent_folder):
            return _parent_entry(folder, parent_folder)
        return None

    for ancestor in folder.resolve().parents:
        if not has_local_loop_data(ancestor):
            continue
        parent_ws = data_dir_for(ancestor)
        listed = {str(item["folder"]) for item in resolve_children(parent_ws, max_depth=max_depth)}
        if str(folder.resolve()) in listed:
            return _parent_entry(folder, ancestor)
        return None
    return None


def _parent_entry(folder: Path, parent_folder: Path) -> dict:
    return {
        "name": parent_folder.name,
        "path": relpath(folder, parent_folder),
        "folder": parent_folder,
        "data_dir": data_dir_for(parent_folder),
    }


# ---------------------------------------------------------------------------
# link / unlink
# ---------------------------------------------------------------------------


def link(workspace: Path, target: str | Path, *, name: str | None = None, map_id: str | None = None) -> dict:
    """Register a sub-product that lives outside the main folder (or confirm one inside it)."""
    folder = product_folder(workspace)
    if folder is None:
        raise SystemExit("Global workspace has no product folder - hierarchy is local-only.")

    child_folder = _resolve_child_path(folder, str(target))
    if not child_folder.is_dir():
        raise SystemExit(f"No such folder: {child_folder}")
    if child_folder.resolve() == folder.resolve():
        raise SystemExit("A workspace cannot be its own sub-product.")
    if not has_local_loop_data(child_folder):
        raise SystemExit(
            f"{child_folder} has no loop data. Run `loop setup --use-cwd` there first."
        )

    entry = {
        "name": name or child_folder.name,
        "path": relpath(folder, child_folder),
        "map_id": map_id or map_id_for(workspace, name or child_folder.name),
        "source": "link",
    }

    meta = read_meta(workspace)
    children = [c for c in (meta.get("children") or []) if isinstance(c, dict)]
    children = [
        c for c in children if _resolve_child_path(folder, str(c.get("path", ""))) != child_folder
    ]
    children.append(entry)
    meta["children"] = sorted(children, key=lambda c: str(c.get("name", "")).lower())
    meta["role"] = ROLE_MAIN
    meta.setdefault("role_source", "auto")
    meta.setdefault("name", folder.name)
    write_meta(workspace, meta)

    stamp_child(data_dir_for(child_folder), folder, map_id=entry["map_id"])
    return entry


def unlink(workspace: Path, name: str) -> bool:
    folder = product_folder(workspace)
    if folder is None:
        return False
    meta = read_meta(workspace)
    children = [c for c in (meta.get("children") or []) if isinstance(c, dict)]
    kept = [c for c in children if str(c.get("name", "")).lower() != name.lower()]
    if len(kept) == len(children):
        return False
    meta["children"] = kept
    write_meta(workspace, meta)
    return True


def stamp_child(child_workspace: Path, parent_folder: Path, *, map_id: str | None = None) -> None:
    """Record the parent link in the sub-product's own metadata.

    Metadata only. Authored product state never crosses workspaces; generated
    hierarchy views are refreshed separately by tree_sync.
    """
    child_folder = product_folder(child_workspace)
    if child_folder is None:
        return
    meta = read_meta(child_workspace)
    if meta.get("role_source") == "user" and meta.get("role") != ROLE_SUB:
        return
    meta["role"] = ROLE_SUB
    meta.setdefault("role_source", "auto")
    meta.setdefault("name", child_folder.name)
    meta["parent"] = relpath(child_folder, parent_folder)
    if map_id:
        meta["map_id"] = map_id
    write_meta(child_workspace, meta)


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------


def refresh(workspace: Path, max_depth: int = DEFAULT_SCAN_DEPTH) -> dict:
    """Resolve and persist this workspace's place in the hierarchy. Idempotent."""
    folder = product_folder(workspace)
    if folder is None:
        return {
            "role": ROLE_STANDALONE,
            "enabled": False,
            "reason": "global workspace has no product folder",
            "children": [],
            "parent": None,
        }

    meta = read_meta(workspace)
    pinned = meta.get("role_source") == "user"
    pinned_role = meta.get("role") if pinned and meta.get("role") in ROLES else None

    children = [] if pinned_role == ROLE_SUB else resolve_children(workspace, max_depth=max_depth)
    parent = None if pinned_role == ROLE_MAIN else resolve_parent(workspace, max_depth=max_depth)

    if pinned_role == ROLE_STANDALONE:
        role, children, parent = ROLE_STANDALONE, [], None
    elif pinned_role:
        role = pinned_role
    elif children:
        role = ROLE_MAIN
    elif parent:
        role = ROLE_SUB
    else:
        role = ROLE_STANDALONE

    meta["role"] = role
    meta.setdefault("role_source", "user" if pinned else "auto")
    meta["name"] = meta.get("name") or folder.name
    # A middle node in a deeper tree is a main *and* a sub - keep both links so it
    # still inherits its parent's constraints while rolling up its own children.
    if children:
        meta["children"] = [
            {
                "name": c["name"],
                "path": c["path"],
                "map_id": c["map_id"],
                "source": c["source"],
            }
            for c in children
        ]
    else:
        meta.pop("children", None)
    if parent:
        meta["parent"] = parent["path"]
    else:
        meta.pop("parent", None)
    write_meta(workspace, meta)

    if role == ROLE_MAIN:
        for child in children:
            if not child["missing"]:
                stamp_child(child["data_dir"], folder, map_id=child.get("map_id"))

    return {
        "role": role,
        "enabled": True,
        "name": meta["name"],
        "folder": folder,
        "children": children,
        "parent": parent,
        "pinned": pinned,
    }


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


def describe_tree(workspace: Path, tree: dict | None = None) -> str:
    tree = tree or refresh(workspace)
    if not tree.get("enabled"):
        return (
            "Hierarchy: disabled\n"
            f"  {tree.get('reason', 'not a local product workspace')}\n"
            "  Run `loop setup --use-cwd` in a product folder to use main/sub products."
        )

    lines = [
        f"Workspace: {tree['name']}  [{tree['role']}{'  pinned' if tree.get('pinned') else ''}]",
        f"  folder: {tree['folder']}",
    ]
    parent = tree.get("parent")
    if parent:
        lines.append(f"  parent: {parent['name']} -> {parent['path']}")
    children = tree.get("children") or []
    if children:
        lines.append(f"  sub-products: {len(children)}")
        for child in children:
            flags = [child["source"]]
            if child["map_id"]:
                flags.append(f"map {child['map_id']}")
            if child["missing"]:
                flags.append("MISSING")
            lines.append(f"    - {child['name']:<24} {child['path']}  ({', '.join(flags)})")
    elif tree["role"] == ROLE_MAIN:
        lines.append("  sub-products: none resolved")

    scope_lines = _scope_lines(workspace)
    if scope_lines:
        # `role` describes this workspace's place among *workspaces*. A unified main
        # product has no workspace children, so it reads `standalone` - true of the
        # hierarchy and misleading about the product. Say both.
        lines[0] = lines[0].replace(
            f"[{tree['role']}", f"[{tree['role']} - unified, sub-products are scopes here"
        )
        lines.extend(scope_lines)
    elif tree["role"] == ROLE_STANDALONE:
        lines.append("  standalone - no parent or sub-product workspaces detected")
    return "\n".join(lines)


def _scope_lines(workspace: Path) -> list[str]:
    """Sub-products held as scopes in this workspace.

    Without this, a workspace that has absorbed every sub-product reports "standalone -
    no parent or sub-product workspaces detected" while holding three of them. That
    sentence is true about *workspaces* and false about the product, and it is the sort
    of report that makes someone re-carve a sub-product that already exists.
    """
    try:
        import scope_paths

        scopes = scope_paths.list_scopes(workspace)
        if not scopes:
            return []
        ordered, cycles = scope_paths.dependency_order(workspace)
        out = [f"  scopes: {len(scopes)} (in this workspace, `plan/products/`)"]
        for scope in ordered or scopes:
            flags = [f"map {scope.map_id}"] if scope.map_id else ["unbound"]
            if scope.code_dir:
                flags.append(scope.code_dir)
            out.append(f"    - {scope.slug:<24} ({', '.join(flags)})")
        for cycle in cycles:
            out.append("    ! dependency cycle: " + " -> ".join(cycle))
        return out
    except Exception:  # noqa: BLE001 - a federated workspace has no scopes
        return []
