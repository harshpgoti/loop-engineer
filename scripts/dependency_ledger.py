#!/usr/bin/env python3
"""What a sub-product has *declared* about the modules it depends on.

The checks this replaces asked "does this counterparty's name appear anywhere in
~120KB of the sub-product's prose?". Measured on a real workspace, that was not a
weak signal - it was a circular one:

- `parent_context.write_context` writes `plan/PARENT_CONTEXT.md` **into** the
  sub-product, containing the parent's dependency titles verbatim.
- `plan_corpus` then read everything under `plan/`, including that file.
- So every dependency matched, always, on the harness's own output.

Three further failures came with it: "we explicitly do NOT integrate with X" scored
as compliance; a `Depends on` of `—` passed because `slugify` returns `"module"` and
that word appears in any long plan; and the 120KB cap silently dropped 3 of the 4
`integrations.md` files - the single most on-point evidence for the contract check.

So this reads *declarations*, not prose. Keys are `PRODUCT_MAP` row IDs where
available, never substrings, so line wrapping, separators, synonyms and prefix
collisions stop mattering. Absence of a declaration is honest evidence; absence of a
substring never was.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

LEDGER_FILE = "plan/INTEGRATIONS.yml"
MAX_SOURCE_BYTES = 8_000

PLANNED = "planned"
DECLINED = "declined"
DEFERRED = "deferred"
STATUSES = (PLANNED, DECLINED, DEFERRED)

INTERNAL_HEADING = re.compile(r"(?i)^#{2,4}\s+internal platform apis\s*$")
SECTION = re.compile(r"^#{1,6}\s+")
SEPARATOR = re.compile(r"^\|[-:\s|]+\|$")
ITEM = re.compile(r"^-\s+(?P<key>[a-z_]+):\s*(?P<value>.*)$")
FIELD = re.compile(r"^(?P<key>[a-z_]+):\s*(?P<value>.*)$")


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).strip().lower()).strip("-")


def _clean(value: str) -> str:
    return str(value).strip().strip("`\"'* ")


def index_rows(rows: list[dict]) -> tuple[dict, dict]:
    """`'07' -> row` and `'ar-followup-agent' -> row`, for resolving a counterparty."""
    by_id = {str(r.get("id", "")).strip(): r for r in rows if str(r.get("id", "")).strip()}
    by_title = {_key(r.get("title", "")): r for r in rows if r.get("title")}
    return by_id, by_title


def resolve(token: str, by_id: dict, by_title: dict) -> dict | None:
    """A counterparty token -> its map row. ID first, then an exact title key."""
    raw = _clean(token)
    if not raw:
        return None
    if raw.isdigit() and raw.zfill(2) in by_id:
        return by_id[raw.zfill(2)]
    if raw in by_id:
        return by_id[raw]
    return by_title.get(_key(raw))


def _entry(row: dict, *, status: str, detail: str, source: str) -> dict:
    return {
        "key": _key(row.get("title", "")) or str(row.get("id", "")),
        "id": str(row.get("id", "")),
        "label": row.get("title", ""),
        "status": status if status in STATUSES else PLANNED,
        "detail": _clean(detail),
        "source": source,
    }


def _read(path: Path, limit: int = MAX_SOURCE_BYTES) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# sources, in precedence order
# ---------------------------------------------------------------------------


def _explicit(workspace: Path, by_id: dict, by_title: dict) -> list[dict]:
    """`plan/INTEGRATIONS.yml` - the authoritative declaration, hand-written or generated.

    Parsed without a yaml dependency, the same way `TASKS.yml` is read elsewhere.
    """
    text = _read(workspace / LEDGER_FILE, 20_000)
    if not text.strip():
        return []

    entries: list[dict] = []
    current: dict = {}

    def flush() -> None:
        if not current.get("counterparty"):
            return
        row = resolve(current["counterparty"], by_id, by_title)
        if row is None:
            row = {"id": "", "title": _clean(current["counterparty"])}
        entries.append(
            _entry(
                row,
                status=_clean(current.get("status", PLANNED)).lower(),
                detail=current.get("contract") or current.get("rationale") or "",
                source=LEDGER_FILE,
            )
        )
        current.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        item = ITEM.match(stripped)
        if item:
            flush()
            current[item.group("key")] = _clean(item.group("value"))
            continue
        field = FIELD.match(stripped)
        if field and current:
            current[field.group("key")] = _clean(field.group("value"))
    flush()
    return entries


def parse_internal_apis(path: Path, by_id: dict, by_title: dict) -> list[dict]:
    """Rows of an `## Internal platform APIs` table, resolved to map rows.

    Also used by `parent_watermark._counterparts`, which had the same substring
    defect one layer up and made the contracts watermark flap.
    """
    text = _read(path)
    if not text.strip():
        return []

    out: list[dict] = []
    inside = False
    header_seen = False
    for line in text.splitlines():
        stripped = line.strip()
        if SECTION.match(stripped):
            inside = bool(INTERNAL_HEADING.match(stripped))
            header_seen = False
            continue
        if not inside or not stripped.startswith("|") or SEPARATOR.match(stripped):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not header_seen:
            header_seen = True  # the column names, not a row
            continue
        if not cells or not _clean(cells[0]):
            continue
        row = resolve(cells[0], by_id, by_title)
        if row is None:
            continue
        out.append(
            _entry(
                row,
                status=PLANNED,
                detail=" ".join(_clean(c) for c in cells[1:] if _clean(c)),
                source=path.name,
            )
        )
    return out


def _step_integrations(workspace: Path, by_id: dict, by_title: dict) -> list[dict]:
    steps = workspace / "plan" / "steps"
    if not steps.is_dir():
        return []
    entries: list[dict] = []
    # Sort on a plain string, not a Path: `Path.__lt__` case-folds on Windows and
    # does not on POSIX, which made the old corpus - and its findings - OS-dependent.
    for folder in sorted((d for d in steps.iterdir() if d.is_dir()), key=lambda d: d.name):
        entries.extend(parse_internal_apis(folder / "integrations.md", by_id, by_title))
    return entries


def _own_map(workspace: Path, by_id: dict, by_title: dict) -> list[dict]:
    """The sub-product's own PRODUCT_MAP - if it lists a module, it knows about it."""
    try:
        from ultraplan_harness import parse_product_map
    except ImportError:
        return []
    entries: list[dict] = []
    for row in parse_product_map(workspace):
        resolved = resolve(row.get("title", ""), by_id, by_title)
        if resolved is not None:
            entries.append(_entry(resolved, status=PLANNED, detail="own product map row", source="plan/PRODUCT_MAP.md"))
    return entries


def _feature_contracts(workspace: Path, by_id: dict, by_title: dict) -> list[dict]:
    root = workspace / "plan" / "features"
    if not root.is_dir():
        return []
    entries: list[dict] = []
    for feature in sorted((d for d in root.iterdir() if d.is_dir()), key=lambda d: d.name):
        contracts = feature / "contracts"
        if not contracts.is_dir():
            continue
        for item in sorted((f for f in contracts.iterdir() if f.is_file()), key=lambda f: f.name):
            row = resolve(item.stem, by_id, by_title)
            if row is not None:
                entries.append(
                    _entry(row, status=PLANNED, detail=f"contract file `{item.name}`", source="plan/features/*/contracts/")
                )
    return entries


SOURCES = (_explicit, _step_integrations, _own_map, _feature_contracts)


def has_surface(workspace: Path) -> bool:
    """True when this workspace has somewhere to declare an integration at all."""
    if (workspace / LEDGER_FILE).is_file():
        return True
    steps = workspace / "plan" / "steps"
    if steps.is_dir() and any((d / "integrations.md").is_file() for d in steps.iterdir() if d.is_dir()):
        return True
    return (workspace / "plan" / "PRODUCT_MAP.md").is_file()


def ledger(workspace: Path, rows: list[dict]) -> dict[str, dict]:
    """Normalized counterparty key -> declaration. Bounded and order-independent."""
    by_id, by_title = index_rows(rows)
    book: dict[str, dict] = {}
    for source in SOURCES:
        try:
            found = source(workspace, by_id, by_title)
        except Exception:
            continue
        for entry in found:
            if entry["key"]:
                book.setdefault(entry["key"], entry)  # first source wins
    return book


def declaration_for(book: dict[str, dict], row: dict) -> dict | None:
    key = _key(row.get("title", ""))
    if key and key in book:
        return book[key]
    row_id = str(row.get("id", ""))
    return next((e for e in book.values() if e["id"] and e["id"] == row_id), None)


def main() -> int:
    from workspace_utils import resolve_workspace

    parser = argparse.ArgumentParser(description="Integrations this workspace has declared.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--parent", default=None, help="Parent workspace holding PRODUCT_MAP.md.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    from ultraplan_harness import parse_product_map

    rows = parse_product_map(Path(args.parent) if args.parent else workspace)
    book = ledger(workspace, rows)
    if not book:
        print("No declared integrations.")
        print(f"Structured surface present: {has_surface(workspace)}")
        return 0
    for entry in book.values():
        print(f"{entry['status']:9} {entry['id'] or '--':>3}  {entry['label']}  ({entry['source']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
