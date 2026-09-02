#!/usr/bin/env python3
"""Append and diff chain benchmarks over time.

Wraps `scripts/chain_bench.py` to record snapshots in
`benchmarks/<date>.json` and emit a trend delta against the prior
snapshot.

Usage:
    python scripts/bench_history.py --workspace <le-app> --append
    python scripts/bench_history.py --workspace <le-app> --diff
    python scripts/bench_history.py --workspace <le-app> --diff --since-days 7
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _run_chain_bench(workspace: Path) -> dict[str, Any] | None:
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "chain_bench.py"),
             "--workspace", str(workspace), "--json"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _load_history(bench_dir: Path) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for p in sorted(bench_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            history.extend(data)
        elif isinstance(data, dict):
            history.append(data)
    return history


def _append(bench_dir: Path, snapshot: dict[str, Any], kind: str = "dev") -> Path:
    bench_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out = bench_dir / f"{today}.json"
    history = _load_history(bench_dir)
    if out.exists():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []
        if isinstance(existing, list):
            history = existing
        elif isinstance(existing, dict):
            history = [existing]
    snapshot_with_kind = {**snapshot, "kind": kind}
    history.append(snapshot_with_kind)
    out.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return out


def _diff(bench_dir: Path, since_days: int) -> str:
    history = _load_history(bench_dir)
    if len(history) < 2:
        return "# Bench History Diff\n\nNot enough snapshots to diff.\n"
    latest = history[-1]
    cutoff_ts = latest["timestamp"] - since_days * 86400
    baseline_candidates = [h for h in history[:-1] if h["timestamp"] <= cutoff_ts]
    if not baseline_candidates:
        baseline_candidates = history[:-1]
    baseline = baseline_candidates[-1]
    lines = [
        "# Bench History Diff",
        "",
        f"Latest: {dt.datetime.fromtimestamp(latest['timestamp']).isoformat()}",
        f"Baseline: {dt.datetime.fromtimestamp(baseline['timestamp']).isoformat()} ({since_days}d window)",
        "",
        "| Signal | Baseline | Latest | Delta |",
        "|---|---|---|---|",
    ]
    b_signals = baseline["signals"]
    l_signals = latest["signals"]
    for key in ("skills_total", "commands_total"):
        b_total = sum(v if isinstance(v, int) else 0 for v in [
            b_signals.get("skills", {}).get("skills_total", 0),
        ])
        # skills_total/commands_total are at top-level in baseline
        b_top = b_signals.get("skills", {}).get("skills_total", 0) if "skills" in b_signals else 0
        l_top = l_signals.get("skills", {}).get("skills_total", 0) if "skills" in l_signals else 0
        delta = l_top - b_top
        lines.append(f"| skills_total | {b_top} | {l_top} | {delta:+d} |")
    for key in ("commands_total",):
        b_top = b_signals.get("commands", {}).get("commands_total", 0) if "commands" in b_signals else 0
        l_top = l_signals.get("commands", {}).get("commands_total", 0) if "commands" in l_signals else 0
        delta = l_top - b_top
        lines.append(f"| commands_total | {b_top} | {l_top} | {delta:+d} |")
    for key in ("roles_total",):
        b_top = b_signals.get("roles", {}).get("roles_total", 0) if "roles" in b_signals else 0
        l_top = l_signals.get("roles", {}).get("roles_total", 0) if "roles" in l_signals else 0
        delta = l_top - b_top
        lines.append(f"| roles_total | {b_top} | {l_top} | {delta:+d} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--bench-dir", type=Path, default=None)
    parser.add_argument("--append", action="store_true", help="Run chain-bench and append the snapshot")
    parser.add_argument("--diff", action="store_true", help="Emit a trend delta against the prior snapshot")
    parser.add_argument("--since-days", type=int, default=30)
    parser.add_argument("--kind", default="dev", help="Snapshot kind (release | dev)")
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    bench_dir = (args.bench_dir or (workspace / "benchmarks")).resolve()
    if args.append:
        snapshot = _run_chain_bench(workspace)
        if snapshot is None:
            print("chain-bench failed; nothing to append", file=sys.stderr)
            return 1
        out = _append(bench_dir, snapshot, kind=args.kind)
        print(f"Appended to {out}")
        return 0
    if args.diff:
        print(_diff(bench_dir, since_days=args.since_days))
        return 0
    print("Specify --append or --diff", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())