"""Auto-select frontend motion/3D skills from task and plan context."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from workspace_utils import ROOT, resolve_workspace


@dataclass(frozen=True)
class SkillRule:
    name: str
    weight: int
    keywords: tuple[str, ...]
    requires_any: tuple[str, ...] = ()  # optional gate keywords
    excludes: tuple[str, ...] = ()


# Higher weight = stronger signal. Rules-first routing per AGENTS.md.
SKILL_RULES: tuple[SkillRule, ...] = (
    SkillRule(
        "react-3d",
        12,
        (
            "react three fiber", "r3f", "@react-three/fiber", "react-three-fiber", "react-3d",
            "drei", "@react-three/drei", "3d react", "three.js react", "threejs react",
            "3d component", "canvas r3f",
        ),
        requires_any=("react", "next.js", "nextjs", "r3f", "three"),
    ),
    SkillRule(
        "webgl-3d",
        11,
        (
            "three.js", "threejs", "webgl", "webgpu", "3d scene", "orbitcontrols",
            "gltf", "glb", "mesh", "shader", "pbr", "product configurator 3d",
            "immersive", "webxr",
        ),
        excludes=("react three fiber", "r3f", "@react-three/fiber"),
    ),
    SkillRule(
        "scroll-animation",
        10,
        (
            "scrolltrigger", "scroll trigger", "scroll-driven", "scroll animation",
            "scroll-linked", "pin section", "pinned section", "scrub", "parallax scroll",
            "scroll storytelling", "scrollytelling", "horizontal scroll", "scroll pin",
        ),
    ),
    SkillRule(
        "animation-timelines",
        9,
        (
            "timeline", "sequence animation", "choreograph", "orchestrated motion",
            "brand motion", "animation sequence", "multi-step animation", "labels gsap",
        ),
    ),
    SkillRule(
        "react-animation",
        8,
        ("usegsap", "gsap react", "gsap.context", "gsap in react", "next.js gsap"),
        requires_any=("react", "next.js", "nextjs", "gsap"),
    ),
    SkillRule(
        "ui-motion",
        9,
        (
            "motion.dev", "framer motion", "motion/react", "whilehover", "whileinview",
            "animatepresence", "spring physics", "hero animation", "hero section",
            "micro-interaction", "micro interaction", "page transition", "gesture",
            "magnetic button", "layout animation", "fade up", "scroll reveal",
        ),
        requires_any=("react", "next.js", "nextjs", "svelte", "astro", "motion", "framer", "ui", "landing", "frontend"),
    ),
    SkillRule(
        "web-animation",
        7,
        (
            "gsap", "greensock", "tween", "stagger", "easing", "fromto", "autoalpha",
            "animation library", "javascript animation",
        ),
        excludes=("scrolltrigger",),  # scrolltrigger skill covers scroll+gsap
    ),
    SkillRule(
        "animation-performance",
        6,
        ("60fps", "animation performance", "jank", "will-change", "gpu animation", "optimize animation"),
    ),
    SkillRule(
        "modern-web-design",
        5,
        (
            "landing page design", "design system", "core web vitals", "cls", "lcp",
            "bold minimalism", "glassmorphism", "scrollytelling design", "cursor ux",
            "modern web design", "marketing site design",
        ),
    ),
)

MOTION_SIGNALS = (
    "animation", "animate", "motion", "parallax", "scroll effect", "hover effect",
    "3d", "webgl", "hero", "transition", "interactive ui", "landing page",
    "frontend ui", "micro-interaction", "gsap", "three.js", "threejs", "r3f",
)

TOPIC_DIR = "skills/frontend-animation/references"

# Topic name (scoring granularity) -> merged reference file
TOPIC_FILES: dict[str, str] = {
    "ui-motion": "ui-motion.md",
    "web-animation": "gsap-animation.md",
    "animation-timelines": "gsap-animation.md",
    "scroll-animation": "gsap-animation.md",
    "react-animation": "gsap-animation.md",
    "animation-performance": "gsap-animation.md",
    "webgl-3d": "3d-rendering.md",
    "react-3d": "3d-rendering.md",
    "modern-web-design": "modern-web-design.md",
}

EXAMPLE_HINTS: dict[str, str] = {
    "ui-motion": "skills/frontend-animation/examples/motion-patterns.md",
}

STACK_DECISION_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"motion\.dev|framer motion|\bmotion\b", "ui-motion"),
    (r"\bgsap\b|greensock|scrolltrigger", "scroll-animation"),
    (r"react three fiber|\br3f\b", "react-3d"),
    (r"three\.?js|webgl", "webgl-3d"),
)


def _read(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]


def gather_context(workspace: Path, extra: str = "") -> str:
    chunks: list[str] = []
    from memory_paths import main_plan_file

    chunks.append(_read(main_plan_file(workspace)))
    for name in ("HANDOFF.md", "DECISIONS.md", "CONTEXT.md", "TASKS.yml"):
        chunks.append(_read(workspace / name))
    plan_dir = workspace / "plan"
    if plan_dir.is_dir():
        for step in sorted(plan_dir.glob("step_*.md")):
            chunks.append(_read(step))
        chunks.append(_read(plan_dir / "SESSION_RECALL.md", 4000))
    try:
        from feature_paths import read_active_feature

        active = read_active_feature(workspace)
        if active:
            feat = Path(active["abs_path"])
            for name in ("spec.md", "feature-plan.md", "tasks.md"):
                chunks.append(_read(feat / name))
    except ImportError:
        pass
    if extra:
        chunks.append(extra)
    return "\n".join(chunks).lower()


def stack_from_decisions(text: str) -> str | None:
    for pattern, skill in STACK_DECISION_PATTERNS:
        if re.search(pattern, text, re.I):
            return skill
    return None


def has_motion_signal(text: str) -> bool:
    return any(sig in text for sig in MOTION_SIGNALS)


def score_rules(text: str) -> dict[str, int]:
    scores: dict[str, int] = {rule.name: 0 for rule in SKILL_RULES}
    for rule in SKILL_RULES:
        if rule.requires_any and not any(gate in text for gate in rule.requires_any):
            continue
        if any(ex in text for ex in rule.excludes):
            continue
        for kw in rule.keywords:
            if kw in text:
                scores[rule.name] += rule.weight
    return scores


def pick_skills(context: str, max_skills: int = 3) -> list[tuple[str, str]]:
    """Return [(skill_name, reason), ...] ordered by relevance."""
    if not has_motion_signal(context):
        return []

    locked = stack_from_decisions(context)
    scores = score_rules(context)

    if locked and locked in scores:
        scores[locked] += 20

    # React frontend + generic animation → ui-motion default over web-animation
    if any(f in context for f in ("react", "next.js", "nextjs")) and scores.get("ui-motion", 0) == 0:
        if has_motion_signal(context) and scores.get("scroll-animation", 0) < 10:
            scores["ui-motion"] += 6

    # Scroll-heavy → ensure scrolltrigger when gsap signals present
    if scores.get("scroll-animation", 0) > 0 and "animation-timelines" not in {k for k, v in scores.items() if v > 0}:
        if any(k in context for k in ("timeline", "sequence", "orchestr")):
            scores["animation-timelines"] += scores["scroll-animation"] // 2

    ranked = sorted(
        ((name, score) for name, score in scores.items() if score > 0),
        key=lambda item: item[1],
        reverse=True,
    )
    if not ranked:
        # Fallback: design direction + ui-motion for react else web-animation
        if any(f in context for f in ("react", "next.js", "nextjs", "svelte", "astro")):
            return [("ui-motion", "default for React/Next frontend motion")]
        return [("web-animation", "default for general web animation")]

    results: list[tuple[str, str]] = []
    for name, score in ranked[:max_skills]:
        reason = f"matched task/plan-loop signals (score {score})"
        if locked == name:
            reason = f"locked by DECISIONS.md ({reason})"
        results.append((name, reason))
    return results


def example_for(skill: str) -> str | None:
    hint = EXAMPLE_HINTS.get(skill)
    if hint and (ROOT / hint).exists():
        return hint
    return None


def format_auto_skills_md(
    workspace: Path,
    picks: list[tuple[str, str]],
    task_hint: str,
) -> str:
    lines = [
        "# Auto-selected skills",
        "",
        "Generated by `scripts/frontend_skill_router.py`. **Agent: read these before coding.**",
        "Do not ask the user which animation library to use unless `Ambiguous` below is true.",
        "",
        f"**Task context:** {task_hint or 'from HANDOFF.md, TASKS.yml, plan/, DECISIONS.md'}",
        "",
        "## Read (in order)",
        "",
        "1. `skills/frontend-animation/SKILL.md`",
    ]
    idx = 2
    ambiguous = len(picks) >= 2
    listed: set[str] = set()
    for name, reason in picks:
        rel = f"{TOPIC_DIR}/{TOPIC_FILES.get(name, name + '.md')}"
        if rel not in listed:
            listed.add(rel)
            lines.append(f"{idx}. `{rel}` — {name}: {reason}")
            idx += 1
        else:
            lines.append(f"   - also `{name}`: {reason} (same reference)")
        ex = example_for(name)
        if ex and ex not in listed:
            listed.add(ex)
            lines.append(f"{idx}. `{ex}` — example patterns")
            idx += 1

    lines.extend(
        [
            "",
            "## Acceptance (motion tasks)",
            "",
            "- `prefers-reduced-motion` supported",
            "- Animate transform/opacity/filter only",
            "- Target 60fps; note bundle impact in handoff",
            "",
            "## Record",
            "",
            "If stack not in `DECISIONS.md`, append the primary skill/library chosen.",
            "",
        ]
    )
    if ambiguous:
        lines.append("**Ambiguous:** two stacks scored similarly — prefer `DECISIONS.md`, else React→`ui-motion`, scroll pin/scrub→`scroll-animation`, 3D→`react-3d`/`webgl-3d`.")
        lines.append("")
    return "\n".join(lines)


def run_router(workspace: Path, extra: str = "", write: bool = False) -> list[tuple[str, str]]:
    context = gather_context(workspace, extra)
    picks = pick_skills(context)
    if write and picks:
        out = workspace / "plan" / "AUTO_SKILLS.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        task_hint = ""
        handoff = _read(workspace / "HANDOFF.md", 500)
        if handoff:
            task_hint = handoff.strip().split("\n")[0][:200]
        out.write_text(format_auto_skills_md(workspace, picks, task_hint), encoding="utf-8")
    return picks


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-select frontend motion/3D skills from plan context.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--text", default="", help="Extra context (e.g. current user message).")
    parser.add_argument("--write", action="store_true", help="Write plan/AUTO_SKILLS.md")
    parser.add_argument("--quiet", action="store_true", help="Only print skill names.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    picks = run_router(workspace, extra=args.text, write=args.write)

    if not picks:
        if not args.quiet:
            print("No frontend motion/3D signals detected.")
        return 0

    if args.quiet:
        for name, _ in picks:
            print(name)
        return 0

    for name, reason in picks:
        print(f"{name}\t{reason}\t{TOPIC_DIR}/{TOPIC_FILES.get(name, name + '.md')}")
    if args.write:
        print(f"\nWrote {workspace / 'plan' / 'AUTO_SKILLS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
