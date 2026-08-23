"""Deterministic drift checks between a main product plan and its sub-products.

Rules first, AI second (`AGENTS.md` non-negotiable #4): every finding here comes
from parsing structured plan files - tables, map rows, plan status lines - never
from a model. The agent reasons on top of the findings; it does not produce them.

Each finding:

    {"id": "decision-conflict:auth-svc:datastore",   # stable - used to dedupe
     "kind": "decision-conflict",
     "level": "error" | "warn" | "info",
     "sub": "auth-svc",
     "detail": "...",
     "note": "...text staged into the sub's DOUBTS.md..."}
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from plan_paths import slugify


PLACEHOLDERS = {"", "tbd", "n/a", "na", "none", "unknown", "-", "unset", "todo"}

LEVEL_ERROR = "error"
LEVEL_WARN = "warn"
LEVEL_INFO = "info"

STALE_DAYS = 14


# ---------------------------------------------------------------------------
# small readers
# ---------------------------------------------------------------------------


def read_text(path: Path, limit: int = 40000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def is_placeholder(value: str) -> bool:
    cleaned = value.strip().strip("*_`").lower()
    cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned).strip()
    return cleaned in PLACEHOLDERS


def table_pairs(text: str, *, skip_sections: tuple[str, ...] = ()) -> dict[str, str]:
    """Normalized key -> value. See `labelled_pairs` for the display labels."""
    return {key: value for key, (_label, value) in labelled_pairs(text, skip_sections=skip_sections).items()}


def labelled_pairs(text: str, *, skip_sections: tuple[str, ...] = ()) -> dict[str, tuple[str, str]]:
    """`| Key | Value |` rows and `- **Key:** value` bullets.

    Returns normalized key -> (original label, value). Comparisons use the
    normalized key; anything shown to a user uses the label as it was written.

    Header and separator rows are dropped. Sections whose heading contains any
    `skip_sections` token are ignored (e.g. "Pending decisions" - not decided yet).
    """
    pairs: dict[str, tuple[str, str]] = {}
    skipping = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip().lower()
            skipping = any(token in heading for token in skip_sections)
            continue
        if skipping:
            continue
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 2:
                continue
            if re.match(r"^[-:\s|]+$", stripped.strip("|")):
                continue
            key, value = cells[0], cells[1]
            if key.lower() in ("item", "topic", "key", "decision", "id", "name", "step"):
                continue
            if not key or is_placeholder(value):
                continue
            pairs.setdefault(normalize_key(key), (key.strip(), value.strip()))
            continue
        bullet = re.match(r"^[-*]\s+\*\*(.+?):?\*\*:?\s*(.+)$", stripped)
        if bullet:
            key, value = bullet.group(1), bullet.group(2)
            if not is_placeholder(value):
                pairs.setdefault(normalize_key(key), (key.strip(), value.strip()))
    return pairs


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def normalize_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.strip().lower()).strip()


def _short(value: str, limit: int = 180) -> str:
    """One-line, bounded quote of a value for a finding message."""
    flat = re.sub(r"\s+", " ", value).strip()
    return flat if len(flat) <= limit else flat[:limit].rstrip() + "..."


# Structured parsers read the whole file. `read_text`'s 40,000-char default is a
# budget for prose scanning, and applying it here silently truncated a real
# DECISIONS.md at 63,074 chars: 23 of 41 decision keys fell past the cut, the parent
# watermark saw them vanish, and the sub-product got 16 error-level `parent-removed`
# findings for decisions that were still sitting in the file. Parsing structure is
# cheap; a cap on it only ever produces phantom removals.
FULL_FILE = 2_000_000


def _deployment_section(workspace: Path) -> str:
    from memory_paths import main_plan_file

    text = read_text(main_plan_file(workspace), FULL_FILE)
    match = re.search(r"(?ims)^##\s+Deployment\s*&?\s*Infrastructure\s*$(.*?)(?=^##\s|\Z)", text)
    return match.group(1) if match else ""


def deployment_table(workspace: Path) -> dict[str, str]:
    return table_pairs(_deployment_section(workspace))


def deployment_labels(workspace: Path) -> dict[str, tuple[str, str]]:
    return labelled_pairs(_deployment_section(workspace))


ADR_HEADING = re.compile(r"^([A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)\s*[:.]\s*(.+)$")
# A real ADR does not always write a bare `- **Decision:**`. When one section settles
# several things it qualifies each bullet - `- **Decision - Cognito is authentication
# only.**`, `- **Decision - tenant isolation gets a second layer.**` - and the bare-only
# pattern matched none of them. That dropped the whole ADR from the surface a
# sub-product inherits: on the real main product, D-M-018 carried the account model,
# "keep authorization wholly in Postgres" and the row-level-security requirement, and
# none of it reached the two sub-products, which then built on SQLite unopposed while
# the drift check reported clean.
DECISION_BULLET = re.compile(
    r"^[-*]\s+\*\*Decision\s*(?:[-‐-―:]\s*(?P<qualifier>[^*]+?))?\s*:?\*\*:?\s*(?P<value>.+)$",
    re.I,
)


def _adr_topic(heading: str) -> str:
    """`D-M-003: Pricing is flat fee` -> `Pricing is flat fee`.

    The ID prefix is workspace-local numbering - `D-001` in a sub-product, `D-M-001`
    in its parent - so it can never be part of the comparison key. Only the topic is
    shared vocabulary between two workspaces.
    """
    match = ADR_HEADING.match(heading)
    if match and any(char.isdigit() for char in match.group(1)):
        return match.group(2).strip()
    return heading.strip()


def decision_entries(text: str, *, skip_sections: tuple[str, ...] = ()) -> dict[str, tuple[str, str]]:
    """Decisions keyed by *topic*, from the two shapes a DECISIONS.md actually uses.

    1. Decision tables - `| Topic | Decision |` rows.
    2. ADR sections - `## D-007: Datastore is Postgres` with a `- **Decision:**` bullet.

    Bare `- **Key:** value` bullets are deliberately not harvested. Every ADR entry
    repeats the same field names - Date, Rationale, Consequences, Reversibility - so
    harvesting them made any two ADR-formatted logs collide on boilerplate rather
    than on substance: six false `decision-conflict` errors between this repo's own
    main product and its sub-product, each one staged into that sub-product's
    DOUBTS.md as a question no one could answer.
    """
    pairs: dict[str, tuple[str, str]] = {}
    heading = ""
    skipping = False
    # Only a table that *declares* itself a decision table is harvested. A real
    # DECISIONS.md is full of body tables - an ICP segmentation grid inside one
    # decision's rationale - and taking every `| a | b |` row turned four market
    # segments into four "platform decisions" that the sub-product was then told
    # were new. Recognized by the header, exactly like the product map.
    DECISION_HEADERS = {"decision", "topic", "key", "item"}
    in_decision_table = False

    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            skipping = any(token in heading.lower() for token in skip_sections)
            in_decision_table = False
            continue
        if skipping:
            continue

        if stripped.startswith("|"):
            if re.match(r"^[-:\s|]+$", stripped.strip("|")):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 2:
                continue

            following = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if re.match(r"^\|[-:\s|]+\|$", following):
                in_decision_table = cells[0].lower() in DECISION_HEADERS
                continue

            key, value = cells[0], cells[1]
            if not in_decision_table or not key or is_placeholder(value):
                continue
            pairs.setdefault(normalize_key(key), (key, value))
            continue

        if stripped:
            in_decision_table = False  # any non-table line ends the table

        bullet = DECISION_BULLET.match(stripped)
        if bullet and heading and not is_placeholder(bullet.group("value")):
            topic = _adr_topic(heading)
            if topic:
                # Each qualified bullet is its own decision. Keying them all on the ADR
                # heading would keep only the first, which is how five decisions became
                # one and the datastore call stopped travelling.
                qualifier = (bullet.group("qualifier") or "").strip().rstrip(".:")
                # Key on both so sibling bullets stay distinct; *display* the qualifier,
                # because that is the half that tells them apart. Labelled the other way
                # round, four decisions from one ADR all read as the same truncated
                # heading in every report the user actually sees.
                key = normalize_key(f"{topic} - {qualifier}") if qualifier else normalize_key(topic)
                pairs.setdefault(key, (qualifier or topic, bullet.group("value").strip()))

    return pairs


def decisions_table(workspace: Path) -> dict[str, str]:
    return {key: value for key, (_label, value) in decisions_labels(workspace).items()}


def decisions_labels(workspace: Path) -> dict[str, tuple[str, str]]:
    return decision_entries(read_text(workspace / "DECISIONS.md", FULL_FILE), skip_sections=("pending",))


def is_uninitialized(workspace: Path) -> bool:
    from memory_paths import main_plan_file

    text = read_text(main_plan_file(workspace))
    return not text.strip() or "Status: **UNINITIALIZED**" in text


# Generated by the harness, or settled argument. Neither is evidence of what a
# sub-product planned. `PARENT_CONTEXT.md` is the worst of them: it is written *into*
# the sub-product and contains the parent's dependency titles verbatim, so reading it
# back made every dependency check pass on the harness's own output.
CORPUS_EXCLUDED = {
    "SESSION_MANIFEST.md",
    "SESSION_RECALL.md",
    "SESSION_CLOSEOUT.md",
    "PARENT_CONTEXT.md",
    "SUBPRODUCTS.md",
    "BUILD_CONTEXT.md",
    "clarifications.md",
    "research.md",
    "spec-checklist.md",
    "converge-report.md",
}


def plan_corpus(workspace: Path, limit: int = 120000) -> str:
    """Everything a sub-product planned, as one lowercase blob for mention checks.

    Kept for callers that want a prose view. The hierarchy dependency and contract
    checks no longer use it - see `dependency_ledger` for why a substring scan over
    this could not answer the question it was being asked.
    """
    from memory_paths import main_plan_file

    plan_dir = workspace / "plan"
    main_plan = main_plan_file(workspace)
    chunks = [read_text(main_plan), read_text(workspace / "DECISIONS.md")]
    used = sum(len(c) for c in chunks)

    if plan_dir.is_dir():
        # `plan/steps/**` first: it holds the integration specs, and under the old
        # ordering the cap ate 3 of 4 of them while spending the budget on
        # `features/*/research.md`. Sort on a POSIX string, not a Path - `Path.__lt__`
        # case-folds on Windows only, which made the corpus OS-dependent.
        paths = [p for p in plan_dir.rglob("*.md") if p.name not in CORPUS_EXCLUDED and p != main_plan]
        paths.sort(key=lambda p: (0 if "steps" in p.parts else 1, p.relative_to(plan_dir).as_posix()))
        for path in paths:
            text = read_text(path, 8000)
            if used + len(text) > limit:
                break  # checked *before* appending, so the cap is a cap
            chunks.append(text)
            used += len(text)

    return "\n".join(chunks).lower()


def mentions(corpus: str, name: str) -> bool:
    """Word-boundary presence of a name in prose, separator- and wrap-insensitive.

    Was two exact substring probes (all-hyphen, all-space) with tokens of <=2 chars
    dropped. That made `prior-auth copilot` and any line-wrapped title invisible,
    while `Claim Guard` matched `claim guardrails` and `AR Followup Agent` matched any
    follow-up agent at all. Still prose matching, so still not proof a plan accounts
    for something - use `dependency_ledger` for that.
    """
    probe = " ".join(w for w in slugify(name).split("-") if w)
    if not probe or probe == "module":
        return False  # `slugify` returns "module" for input with no alphanumerics
    flat = re.sub(r"[\s\-_]+", " ", corpus)
    return re.search(rf"(?<![a-z0-9]){re.escape(probe)}(?![a-z0-9])", flat) is not None


def last_session_at(workspace: Path) -> datetime | None:
    from session_lifecycle import read_meta

    meta = read_meta(workspace)
    stamp = meta.get("ended_at") or meta.get("started_at")
    if not stamp:
        return None
    try:
        parsed = datetime.fromisoformat(str(stamp))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


DELEGATED_TYPES = {"sub-product", "subproduct"}

# A row's status decides whether a missing workspace is a problem yet. Typing a row
# `sub-product` states where the work will live; it is not a promise to start it now.
# On a real map, 12 of 14 rows were `Deferred` - warning about each one's missing folder
# every session is noise that buries the one row that had actually gone active.
DORMANT_STATUSES = (
    "deferred",
    "planned",
    "parked",
    "backlog",
    "later",
    "on hold",
    "not started",
    "future",
    "out of scope",
)


def row_is_dormant(row: dict) -> bool:
    """True when the plan itself says this row has not started."""
    status = normalize_key(row.get("status", ""))
    return any(word.replace(" ", "-") in status for word in DORMANT_STATUSES)


def row_is_delegated(row: dict) -> bool:
    """True when a map row is meant to become its own sub-product workspace.

    Most rows are not. A real map holds company programs that are not products at
    all, and modules planned and built inside this same workspace - typing every
    row as a missing workspace produced 16 warnings on this repo's own map, none
    of them true. Delegation is therefore declared, not assumed: type
    `sub-product`, or a `Workspace` column naming the folder.
    """
    if str(row.get("workspace", "")).strip():
        return True
    return normalize_key(row.get("type", "")) in DELEGATED_TYPES


def _finding(
    kind: str,
    level: str,
    sub: str,
    key: str,
    detail: str,
    note: str,
    *,
    stage: bool = False,
    material: str | None = None,
) -> dict:
    return {
        "id": f"{kind}:{slugify(sub) or 'main'}:{normalize_key(key) or 'x'}",
        "kind": kind,
        "level": level,
        "sub": sub,
        "detail": detail,
        "note": note,
        # The substance of the disagreement, with nothing incidental in it. A
        # resolution is bound to this, so a finding whose *values* change comes
        # back for a fresh answer while a re-worded `detail` does not.
        "material": material if material is not None else detail,
        # Errors always reach the sub-product. `stage` lets a non-error finding
        # do the same - a parent update is news the sub-product must see even
        # when nothing yet contradicts.
        "stage": stage,
    }


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


def check_children(main_ws: Path, children: list[dict]) -> list[dict]:
    """All hierarchy drift between a main workspace and its sub-products."""
    from ultraplan_harness import parse_product_map

    findings: list[dict] = []
    rows = parse_product_map(main_ws)
    parent_name = main_ws.parent.name if main_ws.name == ".loop-engineer" else main_ws.name

    if children and not rows:
        findings.append(
            _finding(
                "missing-product-map",
                LEVEL_WARN,
                "-",
                "product-map",
                f"{len(children)} sub-product workspace(s) exist but `plan/PRODUCT_MAP.md` has no rows - "
                "the master plan cannot say what each one owns.",
                "",
            )
        )

    bound_ids = {c.get("map_id") for c in children if c.get("map_id")}
    for row in rows:
        if not row_is_delegated(row) or row.get("id") in bound_ids:
            continue
        if row_is_dormant(row):
            # The plan says this one has not started. It will be reported the session
            # its status moves, which is when the missing folder starts to matter.
            continue
        findings.append(
            _finding(
                "unbuilt-row",
                LEVEL_WARN,
                row.get("title", row.get("id", "?")),
                f"row-{row.get('id')}",
                f"Product map row {row.get('id')} ({row.get('title')}) is typed `sub-product`, is no longer "
                f"dormant (`{str(row.get('status') or 'no status').strip()}`), and has no workspace. "
                "Run `loop setup --use-cwd` in its folder, or retype the row if it is built here.",
                "",
            )
        )

    parent_deploy = deployment_labels(main_ws)
    parent_decisions = decisions_labels(main_ws)

    for child in children:
        name = child["name"]
        child_ws = child["data_dir"]

        if child.get("missing"):
            findings.append(
                _finding(
                    "missing-link",
                    LEVEL_ERROR,
                    name,
                    "path",
                    f"Linked sub-product `{name}` is no longer at `{child['path']}`. "
                    f"Run `loop workspace unlink {name}` or restore the folder.",
                    "",
                )
            )
            continue

        if rows and not child.get("map_id"):
            findings.append(
                _finding(
                    "unmapped-sub",
                    LEVEL_ERROR,
                    name,
                    "map-row",
                    f"Sub-product `{name}` has no row in the main `plan/PRODUCT_MAP.md`. "
                    "The master plan does not know it exists.",
                    f"Parent `{parent_name}` has no PRODUCT_MAP row for this sub-product. "
                    "Confirm what this sub-product owns so the master plan can map it.",
                )
            )

        if is_uninitialized(child_ws):
            findings.append(
                _finding(
                    "uninitialized-sub",
                    LEVEL_WARN,
                    name,
                    "main-plan",
                    f"Sub-product `{name}` has no initialized plan yet (`plan/main_plan.md` is UNINITIALIZED).",
                    "",
                )
            )
            continue

        findings.extend(
            _conflicts(name, parent_name, parent_deploy, deployment_labels(child_ws), "deployment-conflict")
        )
        findings.extend(
            _conflicts(name, parent_name, parent_decisions, decisions_labels(child_ws), "decision-conflict")
        )
        findings.extend(_dependency_gaps(main_ws, rows, child, parent_name))
        findings.extend(_contract_gaps(main_ws, rows, child, parent_name))
        findings.extend(_parent_updates(main_ws, child, parent_name))
        findings.extend(_staleness(main_ws, child))

    order = {LEVEL_ERROR: 0, LEVEL_WARN: 1, LEVEL_INFO: 2}
    findings.sort(key=lambda f: (order.get(f["level"], 3), f["sub"], f["kind"]))
    return findings


def _conflicts(
    name: str,
    parent_name: str,
    parent_pairs: dict[str, tuple[str, str]],
    child_pairs: dict[str, tuple[str, str]],
    kind: str,
) -> list[dict]:
    source = "Deployment & Infrastructure" if kind == "deployment-conflict" else "DECISIONS.md"
    findings: list[dict] = []
    for key, (label, parent_value) in parent_pairs.items():
        child_entry = child_pairs.get(key)
        if not child_entry:
            continue
        child_value = child_entry[1]
        if normalize_value(child_value) == normalize_value(parent_value):
            continue
        # Compare in full, quote in brief: an ADR decision body runs to paragraphs,
        # and the note goes straight into the sub-product's DOUBTS.md.
        parent_text, child_text = _short(parent_value), _short(child_value)
        findings.append(
            _finding(
                kind,
                LEVEL_ERROR,
                name,
                key,
                f"{label}: main says **{parent_text}**, `{name}` says **{child_text}** ({source}).",
                f"Conflict with parent `{parent_name}` ({source}): **{label}** is **{parent_text}** at "
                f"platform level but **{child_text}** here. Parent decisions are constraints - resolve "
                "before the next `/develop-product`, or raise it with the platform plan.",
            )
        )
    return findings


def _row_for(rows: list[dict], map_id: str | None) -> dict | None:
    if not map_id:
        return None
    for row in rows:
        if row.get("id") == map_id:
            return row
    return None


def parse_depends(raw: str) -> list[str]:
    """Dependency tokens from a `Depends on` cell, placeholders discarded.

    `is_placeholder` existed but was never applied here, so row 01's `—` survived,
    `slugify` turned it into the literal word `module`, and the check passed because
    that word appears in any long plan. `n/a` split on `/` into two phantom deps.
    """
    tokens = [t.strip() for t in re.split(r"[,;/]| and ", str(raw or "")) if t.strip()]
    return [t for t in tokens if not is_placeholder(t) and re.search(r"[a-zA-Z0-9]", t)]


def _declaration_hint(child_name: str) -> str:
    return (
        "Declare it in `plan/INTEGRATIONS.yml` (`status: planned`, or `declined` with a "
        "rationale if this sub-product deliberately does not integrate), or add a row under "
        "`## Internal platform APIs` in `plan/steps/NN-*/integrations.md`."
    )


def _dependency_gaps(main_ws: Path, rows: list[dict], child: dict, parent_name: str) -> list[dict]:
    """Does this sub-product's plan account for the modules the map says it needs?

    Answered from declarations, not prose. See `dependency_ledger` for why.
    """
    import dependency_ledger as ledger_mod

    row = _row_for(rows, child.get("map_id"))
    if not row:
        return []
    depends = parse_depends(row.get("depends", ""))
    if not depends:
        return []

    child_ws = child["data_dir"]
    resolved = []
    for dep in depends:
        dep_row = _row_for(rows, dep.zfill(2) if dep.isdigit() else dep)
        resolved.append(dep_row or {"id": dep, "title": dep})

    if not ledger_mod.has_surface(child_ws):
        names = ", ".join(f"**{r.get('title', r.get('id'))}**" for r in resolved)
        return [
            _finding(
                "unverifiable-dependency",
                LEVEL_INFO,
                child["name"],
                "no-integration-surface",
                f"`{child['name']}` has no structured integration surface, so its dependency on "
                f"{names} cannot be verified.",
                f"Parent `{parent_name}` maps this sub-product as depending on {names}, and there is "
                "nowhere here that records whether it is accounted for. Run `/ultraplan-loop` to "
                "generate `plan/steps/NN-*/integrations.md`, or add `plan/INTEGRATIONS.yml`.",
            )
        ]

    book = ledger_mod.ledger(child_ws, rows)
    findings: list[dict] = []
    for dep_row in resolved:
        dep_name = dep_row.get("title") or dep_row.get("id")
        entry = ledger_mod.declaration_for(book, dep_row)
        if entry and entry["status"] == ledger_mod.PLANNED:
            continue
        if entry:
            findings.append(
                _finding(
                    "dependency-declined",
                    LEVEL_INFO,
                    child["name"],
                    f"depends-{normalize_key(dep_name)}",
                    f"`{child['name']}` records **{dep_name}** as `{entry['status']}`"
                    + (f": {entry['detail']}" if entry["detail"] else "."),
                    "",
                )
            )
            continue
        findings.append(
            _finding(
                "dependency-gap",
                LEVEL_WARN,
                child["name"],
                f"depends-{normalize_key(dep_name)}",
                f"Product map says `{child['name']}` depends on **{dep_name}** "
                f"(row {dep_row.get('id', '?')}), but no integration is declared for it.",
                f"Parent `{parent_name}` maps this sub-product as depending on **{dep_name}**, and "
                f"nothing here declares how. {_declaration_hint(child['name'])}",
            )
        )
    return findings


def _contract_gaps(main_ws: Path, rows: list[dict], child: dict, parent_name: str) -> list[dict]:
    """Parent wrote a cross-module integration spec the sub-product never picked up."""
    from plan_paths import find_step_folder

    import dependency_ledger as ledger_mod

    row = _row_for(rows, child.get("map_id"))
    if not row:
        return []
    folder = find_step_folder(main_ws, str(row.get("id")))
    if folder is None:
        return []

    # Counterparties come from the parent's declared `## Internal platform APIs`
    # table, not from substring-scanning its prose. Two stacked guesses used to
    # compound here, and this check emits at error level.
    by_id, by_title = ledger_mod.index_rows(rows)
    declared = ledger_mod.parse_internal_apis(folder / "integrations.md", by_id, by_title)
    counterparts = [e for e in declared if e["id"] != str(row.get("id", ""))]
    if not counterparts:
        return []

    child_ws = child["data_dir"]
    if not ledger_mod.has_surface(child_ws):
        joined = ", ".join(f"**{c['label']}**" for c in counterparts)
        return [
            _finding(
                "unverifiable-dependency",
                LEVEL_INFO,
                child["name"],
                "integrations",
                f"Main `{folder.name}/integrations.md` declares contracts with {joined}, and "
                f"`{child['name']}` has no structured integration surface to check against.",
                f"Parent `{parent_name}` declares integration contracts with {joined}. Record how "
                f"this sub-product covers them. {_declaration_hint(child['name'])}",
            )
        ]

    book = ledger_mod.ledger(child_ws, rows)
    missing = [c for c in counterparts if not ledger_mod.declaration_for(book, {"id": c["id"], "title": c["label"]})]
    if not missing:
        return []
    joined = ", ".join(f"**{m['label']}**" for m in missing)
    return [
        _finding(
            "contract-gap",
            LEVEL_ERROR,
            child["name"],
            "integrations",
            f"Main `{folder.name}/integrations.md` declares contracts with {joined}, "
            f"but `{child['name']}` declares no integration for them.",
            f"Parent `{parent_name}` declares integration contracts with {joined} in "
            f"`plan/steps/{folder.name}/integrations.md`. {_declaration_hint(child['name'])}",
        )
    ]


def _parent_updates(main_ws: Path, child: dict, parent_name: str) -> list[dict]:
    """What the master plan changed since this sub-product last synced.

    The conflict checks above only fire when both sides carry the same key, so a
    *new* platform constraint - the case that most often invalidates in-flight
    work - is invisible to them. This compares the parent against the watermark
    the sub-product recorded at its last session and reports the delta itself.
    """
    import parent_watermark as wm

    child_ws = child["data_dir"]
    previous = wm.read_watermark(child_ws, main_ws)
    if previous is None:
        # No baseline yet: the sub-product records one at its next session-start.
        # Reporting here would surface every decision the parent ever made.
        return []

    changes = wm.diff(previous, wm.snapshot(main_ws, map_id=child.get("map_id")))
    if not changes:
        return []

    in_flight = wm.has_work_in_flight(child_ws)
    level = LEVEL_ERROR if in_flight else LEVEL_WARN
    urgency = (
        "This sub-product has work in progress - re-check the active tasks before continuing."
        if in_flight
        else "Fold it into the plan before the next build slice."
    )
    seen = str(previous.get("taken_at", ""))[:10]

    findings: list[dict] = []
    for change in changes:
        findings.append(
            _finding(
                f"parent-{change['change']}",
                level,
                child["name"],
                f"{change['surface']}-{change['key']}",
                f"{wm.describe(change)} (`{child['name']}` last synced {seen or 'unknown'})",
                f"Parent `{parent_name}` updated the master plan since this workspace last "
                f"synced ({seen or 'unknown'}). {wm.describe(change)} {urgency} "
                "If the master plan is the wrong side, fix it there instead.",
                stage=True,
                # Not `detail` - that carries the last-synced date, which moves on
                # its own and would reopen an answered question every session.
                material=wm.describe(change),
            )
        )
    return findings


def _staleness(main_ws: Path, child: dict) -> list[dict]:
    from memory_paths import main_plan_file

    plan = main_plan_file(main_ws)
    if not plan.exists():
        return []
    changed = datetime.fromtimestamp(plan.stat().st_mtime, tz=timezone.utc)
    seen = last_session_at(child["data_dir"])
    if seen is None or seen >= changed:
        return []
    days = (changed - seen).days
    if days < 1:
        return []
    return [
        _finding(
            "stale-sub",
            LEVEL_INFO,
            child["name"],
            "stale",
            f"Main plan changed {days} day(s) after `{child['name']}`'s last session - its roll-up may be behind.",
            "",
        )
    ]


def summarize(findings: list[dict]) -> dict[str, int]:
    counts = {LEVEL_ERROR: 0, LEVEL_WARN: 0, LEVEL_INFO: 0}
    for item in findings:
        counts[item["level"]] = counts.get(item["level"], 0) + 1
    counts["total"] = len(findings)
    return counts
