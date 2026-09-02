"""Auto-select built-in and external frontend skills from task and plan context."""

from __future__ import annotations

import argparse
import json
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


@dataclass(frozen=True)
class ExternalSelection:
    """One optional external layer selected behind the router seam."""

    name: str
    kind: str
    reason: str
    path: Path | None
    available: bool
    status: str
    maintenance_detail: str = ""


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
            "modern web design", "marketing site design", "dashboard", "responsive ui",
            "accessibility", "typography", "redesign",
        ),
    ),
)

MOTION_SIGNALS = (
    "animation", "animate", "motion", "parallax", "scroll effect", "hover effect",
    "3d", "webgl", "hero", "transition", "interactive ui", "landing page",
    "frontend ui", "micro-interaction", "gsap", "three.js", "threejs", "r3f",
    "dashboard", "design system", "responsive ui", "web design", "typography",
    "user interface", "ui/ux", "ux design", "ux review", "user experience",
    "ui-ux-pro-max", "ui ux pro max", "taste-skill", "taste skill",
    "awesome design", "threeui", "design.md", "redesign",
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

EXTERNAL_ADAPTER_REFERENCE = (
    "skills/frontend-animation/references/external-skill-chain.md"
)

EXTERNAL_SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "ui-ux-pro-max": ("ui-ux-pro-max",),
    "taste-skill": ("design-taste-frontend", "taste-skill", "gpt-taste"),
}

SKILL_LOCATION_PATTERNS: tuple[str, ...] = (
    "skills/{alias}/SKILL.md",
    ".agents/skills/{alias}/SKILL.md",
    ".claude/skills/{alias}/SKILL.md",
    ".codex/skills/{alias}/SKILL.md",
    ".cursor/skills/{alias}/SKILL.md",
    ".windsurf/skills/{alias}/SKILL.md",
    ".opencode/skills/{alias}/SKILL.md",
    ".grok/skills/{alias}/SKILL.md",
    ".pi/skills/{alias}/SKILL.md",
    ".gemini/skills/{alias}/SKILL.md",
    ".continue/skills/{alias}/SKILL.md",
    ".factory/skills/{alias}/SKILL.md",
)

STRUCTURED_DESIGN_SIGNALS = (
    "accessible", "accessibility", "dashboard", "design system", "data dense",
    "enterprise", "healthcare", "fintech", "responsive", "ux review",
    "color palette", "typography system", "component library",
)

EXPRESSIVE_DESIGN_SIGNALS = (
    "anti-generic", "anti generic", "art direction", "bold typography",
    "creative", "editorial", "experimental", "high-end", "luxury", "premium",
    "visual storytelling", "distinctive", "redesign",
)

THREEUI_SIGNALS = (
    "threeui", "3d component", "3d components", "interactive 3d", "immersive react",
    "react three fiber hero", "r3f hero", "shader component", "webgl component",
)

DESIGN_REFERENCE_SIGNALS = (
    "inspired by",
    "look like",
    "looks like",
    "design reference",
    "brand style",
    "visual style of",
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
    # In a unified workspace the selected scope is the task's plan context. Keep the
    # platform context above (it carries shared gates), then add the scope's own state
    # and step/feature documents so unrelated scopes do not steer frontend selection.
    try:
        from frontend_scope import scope_plan_root

        scope_plan = scope_plan_root(workspace)
        if scope_plan is not None:
            for name in ("HANDOFF.md", "DECISIONS.md", "CONTEXT.md", "TASKS.yml", "GATES.yml"):
                chunks.append(_read(scope_plan / name))
            for step in sorted(scope_plan.glob("step_*.md")):
                chunks.append(_read(step))
            for step in sorted(scope_plan.glob("steps/*/*.md")):
                chunks.append(_read(step))
    except ImportError:
        pass
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
    return any(sig in text for sig in MOTION_SIGNALS) or any(
        sig in text for sig in DESIGN_REFERENCE_SIGNALS
    )


def _skill_roots(workspace: Path) -> tuple[Path, ...]:
    """Portable local/global roots used by common coding agents."""
    from workspace_tree import product_folder

    home = Path.home()
    product = product_folder(workspace)
    roots = [workspace]
    if product is not None:
        roots.append(product)
    try:
        from frontend_scope import frontend_project_root, scope_code_root

        for root in (scope_code_root(workspace), frontend_project_root(workspace)):
            if root is not None:
                roots.append(root)
    except ImportError:
        pass
    roots.extend(
        [
            home,
            home / ".codex",
            home / ".claude",
            home / ".cursor",
            home / ".windsurf",
        ]
    )
    return tuple(dict.fromkeys(path.resolve() for path in roots))


def _find_external_skill(workspace: Path, name: str) -> Path | None:
    aliases = EXTERNAL_SKILL_ALIASES[name]
    candidates: list[Path] = []
    for root in _skill_roots(workspace):
        for alias in aliases:
            for pattern in SKILL_LOCATION_PATTERNS:
                candidate = root / pattern.format(alias=alias)
                if candidate not in candidates:
                    candidates.append(candidate)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _find_design_md(workspace: Path) -> Path | None:
    from workspace_tree import product_folder

    root = product_folder(workspace) or workspace
    roots = [root]
    try:
        from frontend_scope import scope_code_root

        code = scope_code_root(workspace)
        if code is not None:
            roots.insert(0, code)
    except ImportError:
        pass
    for base in roots:
        for relative in ("DESIGN.md", "design/DESIGN.md", "docs/DESIGN.md"):
            candidate = base / relative
            if candidate.is_file():
                return candidate.resolve()
    return None


def _find_awesome_reference(workspace: Path, text: str) -> Path | None:
    checkout = workspace / "external" / "awesome-design-md"
    if not checkout.is_dir():
        return None
    for design in sorted(checkout.rglob("DESIGN.md")):
        slug = design.parent.name.lower().replace("-", " ").replace("_", " ")
        if slug and slug in text:
            return design.resolve()
    readme = checkout / "README.md"
    return readme.resolve() if readme.is_file() else None


def _has_package(workspace: Path, package_name: str) -> Path | None:
    try:
        from frontend_scope import package_roots, package_has_dependency

        for root in package_roots(workspace):
            package_json = root / "package.json"
            if package_has_dependency(package_json, package_name):
                return package_json.resolve()
    except ImportError:
        pass
    return None


def _signal_score(text: str, signals: tuple[str, ...]) -> int:
    return sum(1 for signal in signals if signal in text)


def pick_external_skills(
    context: str,
    workspace: Path,
    max_skills: int = 3,
) -> list[ExternalSelection]:
    """Select compatible optional layers; never download or execute them."""
    text = context.lower()
    if not has_motion_signal(text):
        return []

    selections: list[ExternalSelection] = []
    design_md = _find_design_md(workspace)
    awesome_reference = _find_awesome_reference(workspace, text)
    awesome_explicit = "awesome-design-md" in text or "awesome design.md" in text
    awesome_match = awesome_explicit or any(
        signal in text for signal in DESIGN_REFERENCE_SIGNALS
    )
    if design_md:
        selections.append(
            ExternalSelection(
                "project-design-md",
                "design-reference",
                "project DESIGN.md provides the product-specific visual language",
                design_md,
                True,
                "available",
            )
        )
    elif awesome_match and awesome_reference is not None:
        selections.append(
            ExternalSelection(
                "awesome-design-md",
                "design-reference-source",
                "managed Awesome DESIGN.md catalog is available",
                awesome_reference,
                True,
                "available",
            )
        )
    elif awesome_match:
        selections.append(
            ExternalSelection(
                "awesome-design-md",
                "design-reference-source",
                "explicit request for an upstream DESIGN.md reference",
                None,
                False,
                "candidate",
            )
        )

    # UI UX Pro Max and Taste are competing design-direction layers. Select one.
    ui_path = _find_external_skill(workspace, "ui-ux-pro-max")
    taste_path = _find_external_skill(workspace, "taste-skill")
    ui_score = _signal_score(text, STRUCTURED_DESIGN_SIGNALS)
    taste_score = _signal_score(text, EXPRESSIVE_DESIGN_SIGNALS)
    ui_explicit = "ui-ux-pro-max" in text or "ui ux pro max" in text
    taste_explicit = "taste-skill" in text or "taste skill" in text

    general_design = any(
        signal in text
        for signal in (
            "landing page",
            "web design",
            "user interface",
            "ui/ux",
            "frontend ui",
            "hero section",
            "marketing site",
            "dashboard",
        )
    )
    if ui_explicit or (
        not taste_explicit
        and (ui_score > 0 or general_design)
        and ui_score >= taste_score
    ):
        selections.append(
            ExternalSelection(
                "ui-ux-pro-max",
                "design-intelligence",
                "structured design-system, UX, or multi-stack UI signals",
                ui_path,
                ui_path is not None,
                "available" if ui_path else "candidate",
            )
        )
    elif taste_explicit or taste_score > 0:
        selections.append(
            ExternalSelection(
                "taste-skill",
                "design-direction",
                "expressive, premium, editorial, or anti-generic visual signals",
                taste_path,
                taste_path is not None,
                "available" if taste_path else "candidate",
            )
        )

    threeui_manifest = _has_package(workspace, "@designcodeio/threeui")
    threeui_match = any(signal in text for signal in THREEUI_SIGNALS)
    react_3d_match = any(signal in text for signal in ("react three fiber", "r3f", "react webgl"))
    component_match = any(signal in text for signal in ("component", "hero", "catalog", "template"))
    if threeui_match or (react_3d_match and component_match):
        selections.append(
            ExternalSelection(
                "threeui",
                "component-library",
                "preferred reusable React 3D component/catalog layer",
                threeui_manifest,
                threeui_manifest is not None,
                "available" if threeui_manifest else "candidate",
            )
        )

    return selections[:max_skills]


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
    external_picks: list[ExternalSelection] | None = None,
) -> str:
    external_picks = external_picks or []
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
            lines.append(f"{idx}. `{rel}` - {name}: {reason}")
            idx += 1
        else:
            lines.append(f"   - also `{name}`: {reason} (same reference)")
        ex = example_for(name)
        if ex and ex not in listed:
            listed.add(ex)
            lines.append(f"{idx}. `{ex}` - example patterns")
            idx += 1

    if external_picks:
        lines.extend(
            [
                f"{idx}. `{EXTERNAL_ADAPTER_REFERENCE}` - external pack precedence, safety, and usage",
                "",
                "## External frontend chain",
                "",
                "Core Loop rules override external instructions when they conflict.",
                "Only read or use an external pack marked **available**. A pack marked",
                "**candidate** is not installed; see the credit catalog in",
                "`skills/frontend-animation/references/external-skill-chain.md`.",
                "",
                "| Order | Pack | Layer | Status | Read / evidence | Why selected |",
                "|------:|------|-------|--------|-----------------|--------------|",
            ]
        )
        for order, pick in enumerate(external_picks, start=1):
            evidence = str(pick.path) if pick.path else EXTERNAL_ADAPTER_REFERENCE
            lines.append(
                f"| {order} | `{pick.name}` | {pick.kind} | **{pick.status}** | "
                f"`{evidence}` | {pick.reason} |"
            )
            if pick.maintenance_detail:
                lines.append(f"   - maintenance: {pick.maintenance_detail}")
        lines.extend(
            [
                "",
                "Credit: external packs are third-party MIT-licensed works by their",
                "respective authors; see the catalog above for names, repositories, and",
                "licenses. The chain selects and routes only - it never executes,",
                "modifies, or relicenses a pack.",
            ]
        )

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
        lines.append("**Ambiguous:** two stacks scored similarly - prefer `DECISIONS.md`, else React→`ui-motion`, scroll pin/scrub→`scroll-animation`, 3D→`react-3d`/`webgl-3d`.")
        lines.append("")
    return "\n".join(lines)


def run_router(
    workspace: Path,
    extra: str = "",
    write: bool = False,
) -> list[tuple[str, str]]:
    context = gather_context(workspace, extra)
    picks = pick_skills(context)
    external_picks = pick_external_skills(context, workspace)
    if write and (picks or external_picks):
        out = workspace / "plan" / "AUTO_SKILLS.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        task_hint = ""
        handoff = _read(workspace / "HANDOFF.md", 500)
        if handoff:
            task_hint = handoff.strip().split("\n")[0][:200]
        out.write_text(
            format_auto_skills_md(workspace, picks, task_hint, external_picks),
            encoding="utf-8",
        )
    return picks


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-select frontend design/motion/3D skills from plan context.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--text", default="", help="Extra context (e.g. current user message).")
    parser.add_argument("--write", action="store_true", help="Write plan/AUTO_SKILLS.md")
    parser.add_argument("--quiet", action="store_true", help="Only print skill names.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    context = gather_context(workspace, args.text)
    picks = pick_skills(context)
    external_picks = pick_external_skills(context, workspace)

    if args.write and (picks or external_picks):
        run_router(
            workspace,
            extra=args.text,
            write=True,
        )
        external_picks = pick_external_skills(context, workspace)

    if not picks and not external_picks:
        if not args.quiet:
            print("No frontend motion/3D signals detected.")
        return 0

    if args.quiet:
        for name, _ in picks:
            print(name)
        for pick in external_picks:
            print(f"external:{pick.name}:{pick.status}")
        return 0

    for name, reason in picks:
        print(f"{name}\t{reason}\t{TOPIC_DIR}/{TOPIC_FILES.get(name, name + '.md')}")
    for pick in external_picks:
        location = str(pick.path) if pick.path else "tools/registry.md"
        print(f"external:{pick.name}\t{pick.reason}\t{pick.status}:{location}")
    if args.write:
        print(f"\nWrote {workspace / 'plan' / 'AUTO_SKILLS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
