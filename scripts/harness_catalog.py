#!/usr/bin/env python3
"""Harness catalog: consolidate per-coding-agent harness JSON files into one view.

Walks `harnesses/*.json` and emits a Markdown table with one row per
harness. Validates the expected fields and flags structural issues.

Usage:
    python scripts/harness_catalog.py --root <le-app>
    python scripts/harness_catalog.py --root <le-app> --out docs/HARNESS_CATALOG.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

VALID_TRUST_LEVELS = {"project-trust", "user-trust", "untrusted"}


def _classify(row: dict[str, Any], root: Path) -> str:
    """Return 'OK' or a remediation hint."""
    if row.get("trust") not in VALID_TRUST_LEVELS:
        return f"unknown trust level: {row.get('trust')!r}"
    if not row.get("invocation"):
        return "missing invocation"
    skill_paths = row.get("skill_paths", {})
    for key in ("user", "project"):
        path = skill_paths.get(key)
        if path:
            target = (root / path).expanduser()
            if not target.exists():
                return f"skill_paths.{key} = {path!r} does not exist"
    cmd_paths = row.get("commands_paths", row.get("legacy_command_paths", {}))
    for key in ("user", "project"):
        path = cmd_paths.get(key)
        if path:
            target = (root / path).expanduser()
            if not target.exists():
                return f"commands_paths.{key} = {path!r} does not exist"
    return "OK"


def build(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "harnesses").glob("*.json")):
        if path.name == "worker_versions.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append({
            "name": path.stem,
            "trust": data.get("trust", "?"),
            "invocation": data.get("invocation", ""),
            "skill_paths": data.get("skill_paths", {}),
            "commands_paths": data.get("commands_paths", data.get("legacy_command_paths", {})),
            "status": _classify(data, root),
        })
    return {"version": 1, "root": str(root), "harnesses": rows}


def render_markdown(report: dict[str, Any]) -> str:
    rows = report["harnesses"]
    lines = [
        "# Harness Catalog",
        "",
        f"Root: `{report['root']}`",
        f"Total harnesses: **{len(rows)}**",
        "",
        "| Harness | Trust | Invocation | Skill paths | Command paths | Status |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        sp = r.get("skill_paths") or {}
        cp = r.get("commands_paths") or {}
        sp_str = ", ".join(f"`{k}={v}`" for k, v in sp.items() if v) or "—"
        cp_str = ", ".join(f"`{k}={v}`" for k, v in cp.items() if v) or "—"
        lines.append(
            f"| `{r['name']}` | {r['trust']} | `{r['invocation']}` | {sp_str} | {cp_str} | {r['status']} |"
        )
    bad = [r for r in rows if r["status"] != "OK"]
    if bad:
        lines.append("")
        lines.append("## Issues")
        lines.append("")
        for r in bad:
            lines.append(f"- `{r['name']}`: {r['status']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = build(root)
    if args.json:
        output = json.dumps(report, indent=2)
    else:
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