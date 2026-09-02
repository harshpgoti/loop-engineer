#!/usr/bin/env python3
"""The Grill: structured interview for /plan-loop.

Walks the 50+ questions in `skills/plan-loop/phases/grill.md` and surfaces
them as a structured interview. Each question has a `Default if unavailable`
and a `Why it matters` rationale; the interview asks in groups, stops on
Stop Conditions, and records answers in `<workspace>/plan/GRILL_ANSWERS.md`.

Usage:
    python scripts/grill.py --workspace <ws> [--non-interactive]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


# Pull the question catalog from the grill.md phase file. The file is the
# single source of truth; this script parses it so the runtime does not
# drift from the documentation.
GRILL_FILE = ROOT / "skills" / "plan-loop" / "phases" / "grill.md"


# Categories of questions, in the order they appear in grill.md.
CATEGORIES = [
    "Product, user, and buyer",
    "Distribution, pricing, and commercial",
    "Legal, compliance, and data",
    "Operations, support, and on-call",
    "Security and threat model",
    "Design, UX, and accessibility",
    "Engineering, architecture, and quality",
    "Data, ML, and LLM",
    "Integrations, vendors, and lock-in",
    "People, team, and timing",
    "Meta and process",
]


def _parse_questions(text: str) -> list[dict[str, str]]:
    """Parse the question catalog from grill.md.

    Each question block is a Markdown table row with three cells:
    | Q | Default if unavailable | Why it matters |

    Returns a list of dicts with keys: category, question, default, why.
    """
    # First, find each `### <category>` section, then within it find the
    # table rows that are NOT the header or separator.
    sections = re.split(r"^###\s+", text, flags=re.MULTILINE)
    questions: list[dict[str, str]] = []
    for section in sections[1:]:
        lines = section.splitlines()
        if not lines:
            continue
        category = lines[0].strip()
        if category not in CATEGORIES:
            continue
        # Find the table.
        rows = []
        in_table = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("|"):
                in_table = True
                if stripped.startswith("| Q ") or stripped.startswith("|---") or stripped.startswith("| Q |"):
                    continue
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if len(cells) >= 3:
                    rows.append(cells[:3])
            elif in_table and stripped == "":
                continue
            elif in_table:
                # End of table.
                break
        for cells in rows:
            q, default, why = cells
            questions.append({
                "category": category,
                "question": q,
                "default": default,
                "why": why,
            })
    return questions


def _render_markdown(questions: list[dict[str, str]]) -> str:
    by_cat: dict[str, list[dict[str, str]]] = {}
    for q in questions:
        by_cat.setdefault(q["category"], []).append(q)
    lines = [
        "# Grill Interview",
        "",
        "A structured interview for the `/plan-loop` planning phase.",
        "Each question has a `Default if unavailable` answer (the chain",
        "proceeds with that default when the user is not available) and a",
        "`Why it matters` rationale (the reason the question is asked).",
        "",
        "Stop conditions:",
        "- A question whose answer changes product direction and only the user can settle it.",
        "- Sensitive data or regulated data requested before the relevant gate passes.",
        "- A build task would create irreversible architecture.",
        "",
        "---",
        "",
    ]
    for cat in CATEGORIES:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        for i, q in enumerate(by_cat[cat], 1):
            lines.append(f"### Q{i}. {q['question']}")
            lines.append("")
            lines.append(f"**Default if unavailable:** {q['default']}")
            lines.append("")
            lines.append(f"**Why it matters:** {q['why']}")
            lines.append("")
        lines.append("")
    return "\n".join(lines)


def _ask(question: str, default: str, *, non_interactive: bool) -> str:
    if non_interactive:
        return default
    print()
    print(f"Q: {question}")
    print(f"Default: {default}")
    try:
        answer = input("Your answer (Enter for default): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return answer or default


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="Active workspace; the answers file lands at <ws>/plan/GRILL_ANSWERS.md")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Use the default answer for every question (no input)")
    parser.add_argument("--render-only", action="store_true",
                        help="Render the interview as Markdown and print; do not interact")
    args = parser.parse_args(argv)

    if not GRILL_FILE.exists():
        print(f"Grill file not found: {GRILL_FILE}", file=sys.stderr)
        return 1
    text = GRILL_FILE.read_text(encoding="utf-8")
    questions = _parse_questions(text)
    if not questions:
        print("No questions parsed from grill.md; the file format may have changed.", file=sys.stderr)
        return 1

    if args.render_only:
        print(_render_markdown(questions))
        return 0

    answers: list[dict[str, str]] = []
    for q in questions:
        answer = _ask(q["question"], q["default"], non_interactive=args.non_interactive)
        answers.append({
            "category": q["category"],
            "question": q["question"],
            "default": q["default"],
            "answer": answer,
        })

    out = args.workspace / "plan" / "GRILL_ANSWERS.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Grill Answers",
        "",
        f"Generated by `python scripts/grill.py --workspace {args.workspace}`",
        "",
    ]
    for a in answers:
        lines.append(f"## {a['category']}")
        lines.append("")
        lines.append(f"**Q:** {a['question']}")
        lines.append("")
        lines.append(f"**Default:** {a['default']}")
        lines.append("")
        lines.append(f"**Answer:** {a['answer']}")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {len(answers)} answers to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())