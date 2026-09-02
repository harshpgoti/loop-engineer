#!/usr/bin/env python3
"""List the Loop Engineer chain's roles with class, model, skills, and handoffs.

Emits a Markdown table by default; --json for tooling. The output answers
"who is in the chain and what do they hand off to whom?"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--class", dest="class_filter", default=None, help="Filter by class (e.g. assurance)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    agents = _load_json(root / "manifests" / "agents.json")
    roles = agents.get("roles", [])

    if args.class_filter:
        roles = [r for r in roles if r.get("class") == args.class_filter]

    if args.json:
        print(json.dumps({"version": 1, "count": len(roles), "roles": roles}, indent=2))
    else:
        lines = [
            "# Loop Engineer — Role List",
            "",
            f"Total roles: **{len(roles)}**",
            "",
            "| Role | Class | Model | may_mutate | Skills | Hands off to | Independent from |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in roles:
            skills = ", ".join(r.get("skills", [])) or "—"
            hands = ", ".join(r.get("hands_off_to", [])) or "—"
            indep = ", ".join(r.get("independent_from", [])) or "—"
            model = r.get("model", "—")
            lines.append(
                f"| `{r.get('id', '?')}` | {r.get('class', '?')} | {model} | {r.get('may_mutate', False)} | {skills} | {hands} | {indep} |"
            )
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())