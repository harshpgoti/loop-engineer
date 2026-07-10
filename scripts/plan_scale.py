#!/usr/bin/env python3
"""Detect whether a product idea is convenient (single wedge) or platform-scale."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from plan_paths import SCALE_CONVENIENT, SCALE_PLATFORM, scale_file, slugify
from workspace_utils import ROOT, resolve_workspace


PLATFORM_SIGNALS = (
    "multiple product",
    "multi-product",
    "sub-product",
    "sub product",
    "product suite",
    "platform",
    "ecosystem",
    "several agent",
    "multiple agent",
    "multi-agent",
    "multi agent",
    "agent fleet",
    "orchestrat",
    "microservice",
    "modular",
    "product line",
    "suite of",
    "family of product",
)

MODULE_SIGNALS = (
    "portal and",
    "dashboard and",
    " api and ",
    " agent and ",
    " plus ",
    " as well as ",
    " in addition ",
    "another product",
    "second product",
    "third product",
)

AGENT_TYPE_KEYWORDS = ("agent", "bot", "copilot", "assistant", "automation")


def read_text(path: Path, limit: int = 20000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]


def count_bullet_modules(text: str) -> int:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets = sum(1 for ln in lines if re.match(r"^[-*•]\s+\S", ln) or re.match(r"^\d+[.)]\s+\S", ln))
    return bullets


def count_named_modules(text: str) -> int:
    lower = text.lower()
    hits = 0
    for sig in PLATFORM_SIGNALS + MODULE_SIGNALS:
        if sig in lower:
            hits += 1
    # "X agent", "Y portal" patterns
    hits += len(re.findall(r"\b\w[\w-]{2,}\s+(agent|portal|platform|module|service|app)\b", lower))
    return hits


def infer_scale(workspace: Path, extra: str = "") -> dict:
    from memory_paths import main_plan_file

    chunks = [
        read_text(main_plan_file(workspace)),
        read_text(workspace / "CONTEXT.md"),
        read_text(workspace / "HANDOFF.md"),
        read_text(workspace / "DOUBTS.md"),
        read_text(workspace / "memories" / "MEMORY.md"),
        read_text(workspace / "MEMORY.md"),
        extra,
    ]
    plan_dir = workspace / "plan"
    if plan_dir.is_dir():
        for step in sorted(plan_dir.glob("step_*.md")):
            chunks.append(read_text(step, 4000))
        chunks.append(read_text(plan_dir / "PRODUCT_MAP.md"))

    text = "\n".join(chunks).lower()
    bullets = count_bullet_modules("\n".join(chunks))
    signals = count_named_modules(text)
    step_count = len(list(plan_dir.glob("step_*.md"))) if plan_dir.is_dir() else 0
    agent_modules = len(re.findall(r"\bagent\b", text))

    score = 0
    reasons: list[str] = []

    if any(sig in text for sig in PLATFORM_SIGNALS):
        score += 3
        reasons.append("platform-scale language detected")
    if signals >= 3:
        score += 2
        reasons.append(f"multiple module signals ({signals})")
    if bullets >= 4:
        score += 2
        reasons.append(f"long module list ({bullets} items)")
    if step_count >= 4:
        score += 2
        reasons.append(f"existing step count ({step_count})")
    if agent_modules >= 3:
        score += 2
        reasons.append(f"multiple agent references ({agent_modules})")

    scale = SCALE_PLATFORM if score >= 4 else SCALE_CONVENIENT
    if not reasons:
        reasons.append("single wedge / few modules — standard step planning")

    return {
        "scale": scale,
        "score": score,
        "reasons": reasons,
        "step_count": step_count,
        "signals": signals,
        "bullets": bullets,
    }


def render_scale_report(workspace: Path, result: dict) -> str:
    today = date.today().isoformat()
    lines = [
        "# Plan Scale",
        "",
        f"**Updated:** {today}",
        f"**Scale:** `{result['scale']}`",
        f"**Score:** {result['score']} (platform if >= 4)",
        "",
        "## Detection",
        "",
    ]
    for reason in result["reasons"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Harness",
            "",
            "| Scale | Planning depth |",
            "|-------|----------------|",
            "| `convenient` | `plan/step_XX.md` + feature spec (standard `/plan-loop`) |",
            "| `platform` | `PRODUCT_MAP.md` + per-step `plan/steps/NN-slug/` ultraplan pack |",
            "",
            "## Next",
            "",
        ]
    )
    if result["scale"] == SCALE_PLATFORM:
        lines.extend(
            [
                "1. Fill or generate `plan/PRODUCT_MAP.md` (one row per sub-product/agent).",
                "2. Run `loop plan-loop decompose` to create step stubs + ultraplan folders.",
                "3. Run `loop plan-loop ultraplan next` and complete deep docs per step.",
                "4. See `skills/ultraplan/SKILL.md`.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Continue standard `/plan-loop` with `plan/step_XX.md` + feature spec.",
                "2. Override to platform: `loop plan-loop scale --set platform` if idea grows.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect convenient vs platform product scale.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--text", default="", help="Extra context e.g. user's product description.")
    parser.add_argument("--set", choices=(SCALE_CONVENIENT, SCALE_PLATFORM), default=None)
    parser.add_argument("--write", action="store_true", help="Write plan/PLAN_SCALE.md")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    result = infer_scale(workspace, extra=args.text)
    if args.set:
        result["scale"] = args.set
        result["reasons"] = [f"manual override: {args.set}"]

    report = render_scale_report(workspace, result)
    if args.write:
        path = scale_file(workspace)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(report, encoding="utf-8")
        print(f"Wrote {path}")
    else:
        print(report)

    print(f"scale={result['scale']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
