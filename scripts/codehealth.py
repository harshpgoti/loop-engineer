#!/usr/bin/env python3
"""Code-health snapshot for the active workspace.

Walks the workspace and emits a JSON file with five signals:
- lint_debt: count of warning/error lines per file (best-effort, language-agnostic)
- test_coverage: line + branch coverage if coverage.py is available
- churn: git-log-based files with the most commits in the last N days
- dep_freshness: out-of-date major-version pins in the lock file (best-effort)
- doc_coverage: public modules with at least one doc reference

The script is intentionally lightweight and deterministic. It is not
intended to replace real linters/coverage tools; it produces a fast
single-file snapshot that the chain can read.

Usage:
    python scripts/codehealth.py --workspace <ws> --out plan/CODEHEALTH.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

LINT_DEBT_FILE_PATTERNS = (
    "src/", "lib/", "pkg/", "app/", "internal/", "cmd/",
)
LINT_DEBT_LINE_PATTERNS = (
    re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b"),
    re.compile(r"\b(?:console\.log|println!|print_stack_trace)\b"),
)


def _lint_debt(workspace: Path) -> dict[str, Any]:
    by_file: dict[str, int] = {}
    total = 0
    for path in workspace.rglob("*.py"):
        try:
            rel = path.relative_to(workspace)
        except ValueError:
            continue
        # Use forward-slash prefix matching so this works on Windows too.
        rel_str = rel.as_posix()
        if not any(rel_str.startswith(p) for p in LINT_DEBT_FILE_PATTERNS):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        count = sum(1 for line in text.splitlines() if any(p.search(line) for p in LINT_DEBT_LINE_PATTERNS))
        if count:
            by_file[rel_str] = count
            total += count
    return {"total": total, "by_file": dict(sorted(by_file.items(), key=lambda kv: -kv[1])[:20])}


def _test_coverage(workspace: Path) -> dict[str, Any]:
    # Best-effort: try `coverage report --format=json` and parse.
    try:
        result = subprocess.run(
            ["coverage", "report", "--format=json", "-i"],
            cwd=workspace, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            totals = data.get("totals", {})
            return {
                "lines_pct": round(float(totals.get("percent_covered", 0)), 1),
                "branches_pct": round(float(totals.get("percent_covered_display", 0)), 1),
                "by_file": {},
            }
    except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError, OSError):
        pass
    return {"lines_pct": None, "branches_pct": None, "by_file": {}}


def _churn(workspace: Path, window_days: int = 30) -> dict[str, Any]:
    by_file: dict[str, int] = {}
    try:
        result = subprocess.run(
            ["git", "log", f"--since={window_days} days ago", "--name-only",
             "--pretty=format:"],
            cwd=workspace, capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line or line.startswith("commit "):
                    continue
                by_file[line] = by_file.get(line, 0) + 1
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return {
        "window_days": window_days,
        "by_file": dict(sorted(by_file.items(), key=lambda kv: -kv[1])[:20]),
    }


def _dep_freshness(workspace: Path) -> dict[str, Any]:
    """Heuristic: count dependencies that don't pin a major version >= 1."""
    outdated_major = 0
    outdated_minor = 0
    for lockfile in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                     "Pipfile.lock", "poetry.lock", "Cargo.lock", "go.sum"):
        path = workspace / lockfile
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Rough: count `^0.` or `~0.` (pre-1.0 = unstable major).
        for line in text.splitlines():
            if '"version"' in line or "'version'" in line:
                if re.search(r'"version":\s*"0\.', line) or re.search(r'"version":\s*"\^0\.', line):
                    outdated_major += 1
                elif re.search(r'"version":\s*"1\.[0-9]+\.[0-9]+', line):
                    # Heuristic: pre-2.0 is "minor" lockfile age; not exact.
                    pass
    return {"outdated_major": outdated_major, "outdated_minor": outdated_minor}


def _doc_coverage(workspace: Path) -> dict[str, Any]:
    public_modules: set[str] = set()
    documented: set[str] = set()
    # Heuristic: public modules are .py files in src/ or lib/ without a
    # leading underscore in the basename.
    for path in workspace.rglob("*.py"):
        rel = str(path.relative_to(workspace))
        if not any(rel.startswith(p) for p in LINT_DEBT_FILE_PATTERNS):
            continue
        if path.stem.startswith("_"):
            continue
        public_modules.add(rel)
    # Documented = at least one docs/ file references the module name.
    docs_dir = workspace / "docs"
    if docs_dir.exists():
        try:
            docs_text = "\n".join(
                p.read_text(encoding="utf-8", errors="ignore")
                for p in docs_dir.rglob("*.md")
            )
        except OSError:
            docs_text = ""
        for mod in public_modules:
            stem = Path(mod).stem
            if stem in docs_text:
                documented.add(mod)
    pct = round(100 * len(documented) / len(public_modules), 1) if public_modules else 0
    return {
        "public_modules": len(public_modules),
        "documented": len(documented),
        "pct": pct,
    }


def _release_blockers(signals: dict[str, Any], thresholds: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if signals["lint_debt"]["total"] > thresholds.get("lint_debt_max", 50):
        blockers.append(
            f"lint_debt = {signals['lint_debt']['total']} > {thresholds.get('lint_debt_max', 50)}"
        )
    coverage = signals.get("test_coverage", {})
    lines_pct = coverage.get("lines_pct")
    if lines_pct is not None and lines_pct < thresholds.get("coverage_min", 70.0):
        blockers.append(
            f"test_coverage lines = {lines_pct}% < {thresholds.get('coverage_min', 70.0)}%"
        )
    if signals["doc_coverage"]["pct"] < thresholds.get("doc_coverage_min", 80.0):
        blockers.append(
            f"doc_coverage = {signals['doc_coverage']['pct']}% < {thresholds.get('doc_coverage_min', 80.0)}%"
        )
    return blockers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--window-days", type=int, default=30)
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    signals = {
        "lint_debt": _lint_debt(workspace),
        "test_coverage": _test_coverage(workspace),
        "churn": _churn(workspace, window_days=args.window_days),
        "dep_freshness": _dep_freshness(workspace),
        "doc_coverage": _doc_coverage(workspace),
    }
    report = {
        "version": 1,
        "workspace": str(workspace),
        "timestamp": int(time.time()),
        "signals": signals,
        "release_blockers": _release_blockers(signals, {}),
    }
    output = json.dumps(report, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())