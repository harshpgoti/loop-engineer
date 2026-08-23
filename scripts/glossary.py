#!/usr/bin/env python3
"""The product's own words, and where the plan stops using them.

`CONTEXT.md` had a Repo Map, an Active Step, and Conventions - everything except the
one thing every other document depends on: what the product's nouns mean. Without it
each session renames things and nothing notices.

On the real sub-product, `denial` appears 113 times in the plan, `decline` 44, and
`rejection` 45. In US claims processing those are genuinely different events, so either
they are three defined terms or two of them are drift - and there is no way to tell
which, because nothing was ever written down.

So: a `## Language` section with one opinionated name per concept, the synonyms it
displaces, and a check that counts where the displaced ones are still being used. The
check reports; it never rewrites. Renaming a domain concept is the author's call.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

TERM = re.compile(r"^\*\*(?P<name>[^*]+)\*\*\s*:?\s*$")
INLINE_TERM = re.compile(r"^\*\*(?P<name>[^*]+)\*\*\s*[:-]\s*(?P<definition>.+)$")
AVOID = re.compile(r"^_?Avoid_?\s*:?\s*(?P<words>.+)$", re.I)
SECTION = re.compile(r"^##\s+(?P<name>.+?)\s*$")
LANGUAGE = "language"

# Where vocabulary drift actually starts. Product source is deliberately excluded: a
# variable named `decline_reason` is a code-naming question, and flagging it here would
# bury the plan findings that matter under hundreds of identifier hits.
SURFACE = (
    "plan/*.md",
    "plan/**/*.md",
    "DECISIONS.md",
    "TASKS.yml",
    "DOUBTS.md",
    "EVIDENCE_LOG.md",
    "CURRENT_STATE.md",
)


@dataclass
class Term:
    name: str
    definition: str = ""
    avoid: list[str] = field(default_factory=list)
    line: int = 0
    issues: list[str] = field(default_factory=list)


def context_file(workspace: Path) -> Path:
    return workspace / "CONTEXT.md"


def terms(workspace: Path) -> list[Term]:
    """Every term under `## Language` in CONTEXT.md."""
    path = context_file(workspace)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    found: list[Term] = []
    in_language = False
    current: Term | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        section = SECTION.match(line)
        if section:
            in_language = section.group("name").strip().lower() == LANGUAGE
            current = None
            continue
        if not in_language or not line:
            continue

        inline = INLINE_TERM.match(line)
        heading = TERM.match(line)
        if heading or inline:
            name = (heading or inline).group("name").strip()
            current = Term(name=name, line=number)
            if inline:
                current.definition = inline.group("definition").strip()
            found.append(current)
            continue

        if current is None:
            continue
        avoid = AVOID.match(line)
        if avoid:
            current.avoid = [w.strip() for w in re.split(r"[,;/]", avoid.group("words")) if w.strip()]
        elif not current.definition and not line.startswith(("#", "-", "*")):
            current.definition = line

    for item in found:
        if not item.definition:
            item.issues.append("named with no definition")
        for word in item.avoid:
            if word.strip().lower() == item.name.strip().lower():
                item.issues.append(f"lists {word!r} as both the term and a word to avoid")
    return found


def surface_files(workspace: Path) -> list[Path]:
    seen: dict[Path, None] = {}
    for pattern in SURFACE:
        for path in workspace.glob(pattern):
            if path.is_file() and path.name != "CONTEXT.md" and "archive" not in path.parts:
                seen.setdefault(path.resolve(), None)
    return sorted(seen)


@dataclass
class Drift:
    word: str
    canonical: str
    hits: list[tuple[str, int, str]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.hits)

    @property
    def shown(self) -> int:
        return len([h for h in self.hits if h[2]])


def drift(workspace: Path, *, limit: int = 5) -> list[Drift]:
    """Displaced synonyms still in use across the plan surface, most-used first.

    Word-boundary and case-insensitive with a short suffix allowance, so `decline`
    matches `Declines` and `declined`. A hit is a fact about the text, never a
    judgement about whether the rename is right.
    """
    defined = terms(workspace)
    watch: list[tuple[re.Pattern[str], str, str]] = []
    for term in defined:
        for word in term.avoid:
            watch.append((re.compile(r"\b" + re.escape(word) + r"\w{0,3}\b", re.I), word, term.name))
    if not watch:
        return []

    results = {word: Drift(word=word, canonical=canonical) for _, word, canonical in watch}
    for path in surface_files(workspace):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        try:
            display = path.relative_to(workspace).as_posix()
        except ValueError:
            display = path.name
        for number, line in enumerate(lines, start=1):
            for pattern, word, _canonical in watch:
                if pattern.search(line):
                    entry = results[word]
                    entry.hits.append((display, number, line.strip()[:120] if entry.shown < limit else ""))
    return sorted((d for d in results.values() if d.count), key=lambda d: -d.count)


def status(workspace: Path) -> dict:
    defined = terms(workspace)
    drifted = drift(workspace)
    return {
        "terms": len(defined),
        "issues": sum(len(t.issues) for t in defined),
        "drift_words": len(drifted),
        "drift_hits": sum(d.count for d in drifted),
        "worst": drifted[0].word if drifted else "",
    }


def manifest_block(workspace: Path) -> list[str]:
    """What the session manifest shows, so the vocabulary is reachable without a command.

    Silent on a workspace with barely any plan to be consistent about - a nudge that
    fires every session on an empty product is noise, and noise is what stops the real
    lines being read.
    """
    state = status(workspace)
    if not state["terms"]:
        if len(surface_files(workspace)) < 3:
            return []
        return [
            "## Language",
            "",
            "`CONTEXT.md` has no `## Language` section, so nothing stops each session renaming "
            "the product's concepts. Name them there - one opinionated name each, plus the "
            "synonyms it displaces - and `loop glossary` will report where the plan drifts.",
            "",
        ]
    if not state["drift_hits"] and not state["issues"]:
        return []
    lines = ["## Language", "", f"{state['terms']} term(s) defined in `CONTEXT.md`."]
    if state["drift_hits"]:
        lines.append(
            f"{state['drift_hits']} use(s) of {state['drift_words']} displaced synonym(s) remain in "
            f"the plan - worst is `{state['worst']}`. Run `loop glossary` for where."
        )
    if state["issues"]:
        lines.append(f"{state['issues']} term(s) have problems - run `loop glossary`.")
    lines.append("")
    return lines


EXAMPLE = """## Language

**Denial**
A claim the payer adjudicated and refused to pay.
_Avoid_: rejection, decline
"""


def describe(workspace: Path) -> str:
    defined = terms(workspace)
    if not defined:
        return (
            "No `## Language` section in CONTEXT.md.\n\n"
            "Add one, in this shape:\n\n" + EXAMPLE + "\n"
            "One opinionated name per concept. `_Avoid_` lists the synonyms it displaces, "
            "which is what makes drift checkable."
        )

    lines = [f"{len(defined)} term(s) in CONTEXT.md:", ""]
    for term in defined:
        lines.append(f"  {term.name}: {term.definition or '(no definition)'}")
        if term.avoid:
            lines.append(f"      displaces: {', '.join(term.avoid)}")
        for issue in term.issues:
            lines.append(f"      ! {issue}")

    drifted = drift(workspace)
    lines.append("")
    if not drifted:
        lines.append("No displaced synonym is still in use across the plan.")
        return "\n".join(lines)

    lines.append("Displaced synonyms still in use:")
    for item in drifted:
        lines.append(f"  {item.word} -> {item.canonical}: {item.count} use(s)")
        for display, number, text in item.hits:
            if text:
                lines.append(f"      {display}:{number}  {text}")
        if item.count > item.shown:
            lines.append(f"      ... and {item.count - item.shown} more")
    lines.append("")
    lines.append("Either the words mean different things - define each one - or one of them wins.")
    lines.append("This reports; it never rewrites. Renaming a domain concept is your call.")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(
        description="The product's own words, and where the plan drifts from them."
    )
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="Defined terms and any displaced synonyms still in use.")
    sub.add_parser("lint", help="Non-zero exit when a displaced synonym is still in use.")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if (args.cmd or "list") == "lint":
        if not drift(workspace) and not [t for t in terms(workspace) if t.issues]:
            print("Every plan file uses the product's own words.")
            return 0
        print(describe(workspace))
        return 1

    print(describe(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
