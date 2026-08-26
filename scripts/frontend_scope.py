"""Resolve the active scope's frontend code roots in a unified workspace."""

from __future__ import annotations

import json
from pathlib import Path

from workspace_tree import product_folder


def active_scope(workspace: Path):
    """Return the remembered scope record, if it still exists."""
    try:
        import scope_paths as sp

        remembered = sp.read_active(workspace)
        if not remembered:
            return None
        return sp.find_scope(workspace, str(remembered.get("slug", "")))
    except (ImportError, OSError, TypeError, ValueError):
        return None


def scope_code_root(workspace: Path) -> Path | None:
    scope = active_scope(workspace)
    if scope is None:
        return None
    try:
        root = scope.code_path(workspace)
    except (AttributeError, OSError, TypeError, ValueError):
        return None
    return root.resolve() if root is not None and root.is_dir() else None


def _has_package(path: Path) -> bool:
    return (path / "package.json").is_file()


def package_roots(workspace: Path) -> tuple[Path, ...]:
    """Package roots for the selected scope, then the product root.

    A scope may own a monorepo-style ``frontend/package.json`` rather than a package
    at its code directory. Prefer that frontend child, then the scope root, then the
    merged product root. The order is deterministic and de-duplicated.
    """
    product = product_folder(workspace)
    if product is None:
        return ()
    candidates: list[Path] = []
    code = scope_code_root(workspace)
    if code is not None:
        for child in (code / "frontend", code):
            if _has_package(child):
                candidates.append(child.resolve())
    if _has_package(product):
        candidates.append(product.resolve())
    return tuple(dict.fromkeys(candidates))


def frontend_project_root(workspace: Path) -> Path | None:
    """The selected scope's project root, or the merged product root."""
    product = product_folder(workspace)
    if product is None:
        return None
    roots = package_roots(workspace)
    if roots:
        return roots[0]
    code = scope_code_root(workspace)
    return code or product.resolve()


def scope_plan_root(workspace: Path) -> Path | None:
    scope = active_scope(workspace)
    return scope.path.resolve() if scope is not None else None


def package_has_dependency(package_json: Path, package_name: str) -> bool:
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    for group in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        if package_name in (data.get(group) or {}):
            return True
    return False
