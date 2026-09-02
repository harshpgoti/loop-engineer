#!/usr/bin/env python3
"""Audit every automation the chain runs.

Walks the LE app's automation surface (hooks, harnesses, scripts, CI
workflows, manifests) and emits a Markdown report with the four
categories: healthy, stale, unowned, risky.

Usage:
    python scripts/automation_audit.py --root <le-app> --out plan/AUTOMATION_AUDIT.md
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _walk_hooks(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in (root / ".claude").glob("settings.json*"):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for event, hooks in data.get("hooks", {}).items():
            if not isinstance(hooks, list):
                continue
            for h in hooks:
                for inner in h.get("hooks", []):
                    rows.append({
                        "source": str(path.relative_to(root)),
                        "type": "hook",
                        "event": event,
                        "matcher": h.get("matcher", ""),
                        "command": inner.get("command", ""),
                    })
    return rows


def _walk_harnesses(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in (root / "harnesses").glob("*.json"):
        if path.name == "worker_versions.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({
            "source": str(path.relative_to(root)),
            "type": "harness",
            "name": path.stem,
            "trust": data.get("trust", "?"),
            "invocation": data.get("invocation", "?"),
        })
    return rows


def _walk_scripts(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in (root / "scripts").glob("*.py"):
        name = path.stem
        if name.startswith("test_") or name.startswith("_"):
            continue
        has_test = (root / "scripts" / f"test_{name}.py").exists()
        rows.append({
            "source": str(path.relative_to(root)),
            "type": "script",
            "name": name,
            "has_test": has_test,
        })
    return rows


def _walk_manifests(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in ("install_profiles.json", "capabilities.json", "agents.json"):
        path = root / "manifests" / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({"source": f"manifests/{name}", "type": "manifest", "ok": True})
    return rows


def _classify(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    healthy: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    unowned: list[dict[str, Any]] = []
    risky: list[dict[str, Any]] = []
    for r in rows:
        if r["type"] == "script" and not r.get("has_test"):
            stale.append({**r, "reason": "no matching test_<name>.py"})
        elif r["type"] == "harness" and r.get("trust", "?") == "?":
            stale.append({**r, "reason": "missing trust level"})
        elif "secrets" in r.get("command", "").lower() or "${" in r.get("command", ""):
            risky.append({**r, "reason": "may reference an interpolated secret; review"})
        else:
            healthy.append(r)
    return {
        "healthy": healthy,
        "stale": stale,
        "unowned": unowned,
        "risky": risky,
    }


def render_markdown(report: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        "# Automation Audit",
        "",
        f"Total automations: **{sum(len(v) for v in report.values())}**",
        "",
        f"- Healthy: **{len(report['healthy'])}**",
        f"- Stale: **{len(report['stale'])}**",
        f"- Unowned: **{len(report['unowned'])}**",
        f"- Risky: **{len(report['risky'])}**",
        "",
    ]
    for category in ("stale", "unowned", "risky", "healthy"):
        rows = report[category]
        if not rows:
            continue
        lines.append(f"## {category.title()} ({len(rows)})")
        lines.append("")
        for r in rows:
            source = r.get("source", "?")
            name = r.get("name", r.get("event", "?"))
            reason = r.get("reason", "")
            if reason:
                lines.append(f"- `{source}` ({name}) — {reason}")
            else:
                lines.append(f"- `{source}` ({name})")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    rows = (
        _walk_hooks(root)
        + _walk_harnesses(root)
        + _walk_scripts(root)
        + _walk_manifests(root)
    )
    report = _classify(rows)
    output = render_markdown(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())