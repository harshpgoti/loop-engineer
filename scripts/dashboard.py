#!/usr/bin/env python3
"""Build a self-contained HTML dashboard from a YAML spec.

Walks the spec, runs each panel's source command, and emits a single
HTML file with inline SVG. No JS frameworks, no CDN, no external
dependencies. The HTML works in file:// and offline.

Usage:
    python scripts/dashboard.py --spec <spec.yaml> --out <dashboard.html>
"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run_source(source: str, workspace: Path, timeout: int = 30) -> Any:
    """Run a panel's source command and return the JSON-decoded result.
    Returns None on failure."""
    try:
        result = subprocess.run(
            source, shell=True, cwd=workspace, capture_output=True, text=True, timeout=timeout,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    out = result.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out  # raw text


def _render_panel(title: str, value: Any, panel_type: str) -> str:
    safe_title = html.escape(title)
    if value is None:
        return f'<section><h2>{safe_title}</h2><p class="muted">no data</p></section>'
    if panel_type == "counter":
        return f'<section><h2>{safe_title}</h2><p class="counter">{html.escape(str(value))}</p></section>'
    if panel_type == "table" and isinstance(value, list):
        rows = "".join(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
            for row in value
        )
        return f'<section><h2>{safe_title}</h2><table>{rows}</table></section>'
    return f'<section><h2>{safe_title}</h2><pre>{html.escape(str(value))}</pre></section>'


def render_html(spec: dict[str, Any], panel_html: list[str]) -> str:
    title = html.escape(str(spec.get("title", "Dashboard")))
    body = "\n".join(panel_html)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 2rem; max-width: 80rem; }}
    h1 {{ margin: 0 0 1rem; }}
    section {{ border: 1px solid #e2e8f0; border-radius: 0.5rem; padding: 1rem; margin: 0.5rem 0; }}
    h2 {{ margin: 0 0 0.5rem; font-size: 1rem; }}
    .counter {{ font-size: 2rem; font-weight: 700; margin: 0; }}
    .muted {{ color: #94a3b8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 0.4rem; text-align: left; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
{body}
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--workspace", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.spec.exists():
        print(f"Spec not found: {args.spec}", file=sys.stderr)
        return 1
    try:
        import yaml

        spec = yaml.safe_load(args.spec.read_text(encoding="utf-8"))
    except ImportError:
        print(
            "PyYAML is required for dashboard specs: pip install pyyaml",
            file=sys.stderr,
        )
        return 1
    except yaml.YAMLError as exc:
        print(f"Failed to load spec: {exc}", file=sys.stderr)
        return 1
    workspace = args.workspace.resolve()
    panels: list[str] = []
    for panel in spec.get("dashboard", {}).get("panels", []):
        title = panel.get("title", "?")
        ptype = panel.get("type", "counter")
        source = panel.get("source", "")
        value = _run_source(source, workspace)
        panels.append(_render_panel(title, value, ptype))
    output = render_html(spec, panels)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())