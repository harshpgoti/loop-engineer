#!/usr/bin/env python3
"""What the plan knows it does not know yet.

A plan has three kinds of unknown and the harness only tracked one of them.

    a question you can state          -> DOUBTS.md, asked in rounds
    a decision you can see coming     -> nowhere
    work you have ruled out           -> nowhere

The middle one is fog: in scope, definitely coming, not yet sharp enough to phrase as a
question. With nowhere to put it a plan does one of two bad things - guesses at it and
over-specifies, or drops it silently and rediscovers it during the build.

The test is not whether you can answer it. It is whether you can **state** it precisely
now. Sharp enough to state -> it is a doubt. Not yet -> it is fog.

The third one is scope, not sharpness. Out-of-scope work never graduates; it returns only
if the destination is redrawn, and then as a fresh decision.

Fog is meant to clear. A patch that has sat unchanged for weeks is either a question you
can now state or work you have quietly decided not to do, and this says so rather than
letting it settle into the plan as permanent furniture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

FOG_HEADINGS = ("not yet specified", "fog of war", "fog")
SCOPE_HEADINGS = ("out of scope",)
SECTION = re.compile(r"^#{2,3}\s+(?P<name>.+?)\s*$")
BULLET = re.compile(r"^[-*]\s+(?P<text>.+?)\s*$")

# How long a patch of fog may sit before the harness asks about it. Long enough that a
# plan under active revision is never nagged; short enough that a patch cannot quietly
# become permanent. Matches the deferral horizon used elsewhere in the harness, x4.
STALE_DAYS = 28


@dataclass
class Patch:
    text: str
    kind: str  # "fog" or "out-of-scope"
    line: int
    first_seen: str = ""

    @property
    def key(self) -> str:
        """Identity by content, so editing a patch honestly restarts its clock."""
        normalized = re.sub(r"\s+", " ", self.text.strip().lower())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]

    def age_days(self, today: date | None = None) -> int:
        if not self.first_seen:
            return 0
        try:
            seen = datetime.strptime(self.first_seen, "%Y-%m-%d").date()
        except ValueError:
            return 0
        return max(0, ((today or date.today()) - seen).days)


def plan_file(workspace: Path) -> Path:
    return workspace / "plan" / "main_plan.md"


def ledger_file(workspace: Path) -> Path:
    return workspace / ".loop" / "fog.json"


def _read_ledger(workspace: Path) -> dict:
    path = ledger_file(workspace)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def parse(workspace: Path) -> list[Patch]:
    """Every bullet under the plan's fog and out-of-scope headings."""
    path = plan_file(workspace)
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    found: list[Patch] = []
    kind = ""
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        section = SECTION.match(line)
        if section:
            name = section.group("name").strip().lower().strip("*_ ")
            name = re.sub(r"^\d+[.)]\s*", "", name)
            if any(name.startswith(h) for h in FOG_HEADINGS):
                kind = "fog"
            elif any(name.startswith(h) for h in SCOPE_HEADINGS):
                kind = "out-of-scope"
            else:
                kind = ""
            continue
        if not kind:
            continue
        bullet = BULLET.match(line)
        if bullet and not line.startswith("- [ ]"):
            body = bullet.group("text").strip()
            if body and not body.startswith("<!--"):
                found.append(Patch(text=body, kind=kind, line=number))

    ledger = _read_ledger(workspace)
    for patch in found:
        patch.first_seen = ledger.get(patch.key, {}).get("first_seen", "")
    return found


def record(workspace: Path, *, today: date | None = None) -> list[Patch]:
    """Stamp anything new, forget anything gone, and return the current patches.

    The clock starts the first time a patch is seen, not the first time somebody asks
    about it - otherwise a patch is only ever as old as the last person who looked.
    """
    patches = parse(workspace)
    ledger = _read_ledger(workspace)
    stamp = (today or date.today()).isoformat()
    live = {p.key for p in patches}

    for patch in patches:
        if patch.key not in ledger:
            ledger[patch.key] = {"first_seen": stamp, "kind": patch.kind, "text": patch.text[:200]}
            patch.first_seen = stamp
        else:
            ledger[patch.key]["kind"] = patch.kind
            patch.first_seen = ledger[patch.key].get("first_seen", stamp)

    for key in [k for k in ledger if k not in live]:
        # Cleared fog leaves no residue. It became a doubt, a decision, or a scope call,
        # and each of those has its own record.
        ledger.pop(key)

    path = ledger_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return patches


def fog(workspace: Path) -> list[Patch]:
    return [p for p in parse(workspace) if p.kind == "fog"]


def out_of_scope(workspace: Path) -> list[Patch]:
    return [p for p in parse(workspace) if p.kind == "out-of-scope"]


def stale(workspace: Path, *, days: int = STALE_DAYS, today: date | None = None) -> list[Patch]:
    """Fog that has not cleared. Out-of-scope work is excluded - it is not meant to."""
    return sorted(
        (p for p in fog(workspace) if p.age_days(today) >= days),
        key=lambda p: -p.age_days(today),
    )


def promote(workspace: Path, index: int, *, blocking: bool = True) -> str | None:
    """Turn a patch of fog into a stated question, and clear it from the plan.

    Returns the new doubt id, or None when the index does not name a patch. The patch
    text becomes the question verbatim - sharpening the wording is the author's job, and
    a machine paraphrase would lose whatever nuance made it worth writing down.
    """
    import doubts

    patches = fog(workspace)
    if not 1 <= index <= len(patches):
        return None
    patch = patches[index - 1]

    title = patch.text.split(".")[0].strip()[:80] or patch.text[:80]
    doubt_id = doubts.add(
        workspace,
        title=title,
        question=patch.text,
        why="Promoted from the plan's fog - it became sharp enough to state.",
        blocking=blocking,
    )
    if doubt_id is None:
        return None

    path = plan_file(workspace)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    del lines[patch.line - 1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record(workspace)
    return doubt_id


def manifest_block(workspace: Path, *, today: date | None = None) -> list[str]:
    """Surfaced in the session manifest, so fog cannot quietly become permanent."""
    patches = record(workspace, today=today)
    unclear = [p for p in patches if p.kind == "fog"]
    if not unclear:
        return []
    old = [p for p in unclear if p.age_days(today) >= STALE_DAYS]
    lines = ["## Not yet specified", "", f"{len(unclear)} patch(es) of fog in `plan/main_plan.md`."]
    if old:
        lines.append(
            f"{len(old)} of them have sat unchanged for {STALE_DAYS}+ days. Each is now either a "
            "question you can state (`loop fog promote <n>`) or work you have decided not to do "
            "(move it to `## Out of scope`)."
        )
        for patch in old[:3]:
            lines.append(f"  - {patch.age_days(today)}d: {patch.text[:110]}")
    lines.append("")
    return lines


def describe(workspace: Path, *, today: date | None = None) -> str:
    patches = record(workspace, today=today)
    unclear = [p for p in patches if p.kind == "fog"]
    ruled_out = [p for p in patches if p.kind == "out-of-scope"]

    if not patches:
        return (
            "`plan/main_plan.md` has no `## Not yet specified` section.\n\n"
            "Add one for the decisions you can see coming but cannot yet phrase as a question. "
            "The test is whether you can state it precisely now, not whether you can answer it - "
            "sharp enough to state means it belongs in DOUBTS.md instead.\n\n"
            "Add `## Out of scope` alongside it for work ruled beyond this plan. That never "
            "graduates; it returns only if the plan's destination is redrawn."
        )

    lines = []
    if unclear:
        lines.append(f"{len(unclear)} patch(es) of fog:")
        for index, patch in enumerate(unclear, start=1):
            age = f"{patch.age_days(today)}d" if patch.first_seen else "new"
            flag = "  <- stale" if patch.age_days(today) >= STALE_DAYS else ""
            lines.append(f"  {index}. [{age}] {patch.text}{flag}")
        lines.append("")
        lines.append("`loop fog promote <n>` states one as a doubt. Anything you have decided")
        lines.append("not to do belongs under `## Out of scope` instead.")
    else:
        lines.append("No fog. Every in-scope unknown in the plan is a stated question.")

    if ruled_out:
        lines.append("")
        lines.append(f"{len(ruled_out)} item(s) ruled out of scope:")
        for patch in ruled_out:
            lines.append(f"  - {patch.text}")
        lines.append("")
        lines.append("These do not graduate. Reopening one means redrawing the plan's destination.")
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="What the plan knows it does not know yet.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="Fog and out-of-scope items, with how long each has sat.")
    promote_p = sub.add_parser("promote", help="State a patch of fog as a doubt and clear it.")
    promote_p.add_argument("index", type=int)
    promote_p.add_argument("--non-blocking", action="store_true")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if (args.cmd or "list") == "promote":
        doubt_id = promote(workspace, args.index, blocking=not args.non_blocking)
        if doubt_id is None:
            print(f"No fog at position {args.index}. Run `loop fog` for the list.")
            return 1
        print(f"{doubt_id}: recorded, and cleared from the plan.")
        print("Give it a `Default if unavailable` so it comes with a recommended answer.")
        return 0

    print(describe(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
