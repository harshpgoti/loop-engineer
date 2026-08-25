#!/usr/bin/env python3
"""Whether this product's sub-products are ready, for /status, /prod-gap and /release-check.

Replaces the roll-up the federated layout produced by reading every sub-product
*workspace*. Sub-products are scopes here, so the same question is answered from files
this workspace already holds - no cross-workspace read, and nothing to keep in sync.

The rule it enforces is unchanged and is the reason this exists at all: **a platform is
only as ready as its sub-products.** A scope consuming a contract nobody provides, or
blocked on a task that does not exist, is a launch blocker for the whole product - not a
detail hidden inside one folder.

Writes nothing.
"""

from __future__ import annotations

from pathlib import Path


EMPTY: dict = {"role": None, "children": 0, "parent": None, "lines": [], "blockers": []}


def readiness(workspace: Path) -> dict:
    """`{role, children, parent, lines, blockers}` - the shape the callers already expect.

    `children` counts scopes, so a caller that only prints a number keeps working.
    `blockers` are error-level findings that should stop a release.
    """
    try:
        import scope_paths as sp
        import scope_state
        import contracts as ct
    except Exception:  # noqa: BLE001 - readiness must never break a status call
        return dict(EMPTY)

    try:
        scopes = sp.list_scopes(workspace)
    except Exception:  # noqa: BLE001
        return dict(EMPTY)
    if not scopes:
        return dict(EMPTY)

    lines: list[str] = []
    blockers: list[str] = []

    try:
        tasks = scope_state.load_tasks(workspace)
        findings = ct.check(workspace, tasks=tasks)
        dangling = scope_state.unresolved_blockers(tasks)
        clashes = scope_state.duplicate_gate_ids(scope_state.load_gates(workspace))
        _ordered, cycles = sp.dependency_order(workspace)
    except Exception:  # noqa: BLE001
        tasks, findings, dangling, clashes, cycles = [], [], [], [], []

    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]

    lines.append(
        f"- **Sub-products:** {len(scopes)} scope(s) in `plan/products/` "
        f"({len(errors)} error, {len(warns)} warning finding(s))"
    )

    for summary in _summaries(workspace, scope_state):
        lines.append(f"  - {summary}")

    blockers.extend(f.line() for f in errors)
    blockers.extend(str(item) for item in dangling)
    blockers.extend(f"duplicate gate: {c}" for c in clashes)
    blockers.extend("dependency cycle between scopes: " + " -> ".join(c) for c in cycles)

    for scope in scopes:
        if not scope.map_id:
            lines.append(f"  - `{scope.slug}` has no PRODUCT_MAP row bound")

    return {
        "role": "main" if scopes else None,
        "children": len(scopes),
        "parent": None,
        "lines": lines,
        "blockers": blockers,
    }


def _summaries(workspace: Path, scope_state) -> list[str]:
    try:
        return [row.line() for row in scope_state.summarize(workspace)]
    except Exception:  # noqa: BLE001
        return []
