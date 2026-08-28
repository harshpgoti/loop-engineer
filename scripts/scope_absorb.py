#!/usr/bin/env python3
"""Fold a sub-product's own `.loop-engineer/` workspace into the main product as a scope.

The federated layout gave each sub-product a workspace of its own. This moves one into
`plan/products/<slug>/` so both ends stop needing to be kept in sync across a boundary.
See `docs/SCOPES.md` for the shipped scope and absorb model.

Three rules the design turns on:

- **Nothing is written until everything has been checked.** The whole move is planned
  first - id rewrites, decision conflicts, dangling references - and a blocker stops the
  run before the first file is touched. A half-absorbed sub-product is worse than an
  un-absorbed one.
- **The child workspace is renamed, never deleted.** `.loop-engineer.absorbed-<date>/`
  no longer matches `workspace_resolver`'s markers, so nearest-wins resolution stops
  finding it - which is the point. Leaving it in place would silently route every future
  session in that folder back to the dead workspace, the worst failure this migration
  has. The copy is kept as a plain backup of what was absorbed - nothing reads it, and it
  can be deleted once the absorb has been verified.
- **A conflicting decision stops and asks.** Everything else can be merged mechanically;
  two plans that resolved the same topic differently cannot, and guessing which one wins
  would quietly discard a real decision.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import scope_paths as sp

ROOT = Path(__file__).resolve().parent.parent

#: Written into the sub-product folder by the harness, or pure boundary bookkeeping.
#: None of it is authored, and none of it means anything once the boundary is gone.
GENERATED = (
    "plan/PARENT_CONTEXT.md",
    "plan/SUBPRODUCTS.md",
    "plan/SESSION_MANIFEST.md",
    "plan/BUILD_CONTEXT.md",
    "plan/SESSION_RECALL.md",
    ".loop/parent-sync.json",
    ".loop/finding-log.json",
    ".loop/workspace.json",
)

#: Plan files that become the scope's own, copied as-is.
PLAN_TREES = ("steps", "features")


def _now_stamp() -> str:
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# planning
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    """What absorbing one sub-product would do, computed before anything is written."""

    slug: str
    folder: Path
    child_ws: Path
    target: Path
    map_id: str | None = None
    name: str = ""
    code_dir: str | None = None
    task_ids: dict[str, str] = field(default_factory=dict)
    gate_ids: dict[str, str] = field(default_factory=dict)
    doubt_ids: dict[str, str] = field(default_factory=dict)
    decisions_merged: int = 0
    decision_conflicts: list[str] = field(default_factory=list)
    decision_keys: list[str] = field(default_factory=list)
    contracts: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)
    sessions: int = 0
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blockers


def child_workspace(folder: Path) -> Path | None:
    """The sub-product's data dir - nested `.loop-engineer/`, or a legacy flat layout."""
    folder = Path(folder).resolve()
    nested = folder / ".loop-engineer"
    if (nested / "plan").is_dir() or (nested / "memories").is_dir():
        return nested
    if (folder / "plan" / "main_plan.md").exists() and (folder / "memories").is_dir():
        return folder
    return None


ID_PREFIX = re.compile(r"^(?P<head>[A-Z]+)-(?P<rest>.+)$")


def _upper(slug: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", slug.upper()).strip("-")


def task_rename(task_id: str, slug: str) -> str:
    """`TASK-001` -> `AUTH-TASK-001`, and an already-namespaced id is left alone.

    Re-prefixing is the failure that matters here: `AUTH-TASK-001` becoming
    `AUTH-AUTH-TASK-001` on a second run would break every reference written by the
    first, so absorb has to be idempotent at the id level.
    """
    prefix = _upper(slug)
    if task_id.startswith(prefix + "-"):
        return task_id
    return f"{prefix}-{task_id}"


def gate_rename(gate_id: str, slug: str) -> str:
    prefix = _upper(slug)
    if not gate_id.startswith("G-"):
        return gate_id
    if gate_id.startswith(f"G-{prefix}-"):
        return gate_id
    return f"G-{prefix}-{gate_id[2:]}"


def doubt_rename(doubt_id: str, slug: str) -> str:
    prefix = _upper(slug)
    if doubt_id.startswith(f"DQ-{prefix}-"):
        return doubt_id
    return f"DQ-{prefix}-{doubt_id[3:]}" if doubt_id.startswith("DQ-") else doubt_id


DOUBT_ID = re.compile(r"\bDQ-[A-Z0-9-]*\d+\b")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def plan_absorb(
    main_ws: Path,
    folder: Path,
    *,
    map_id: str | None = None,
    merge: bool = False,
    slug: str | None = None,
) -> Plan:
    """Everything absorb would do, and every reason it must not."""
    from task_context import parse_tasks_file

    import scope_state

    folder = Path(folder).resolve()
    child = child_workspace(folder)
    resolved_slug = sp.slugify(slug or folder.name)
    plan = Plan(
        slug=resolved_slug,
        folder=folder,
        child_ws=child or folder,
        target=sp.scope_dir(main_ws, resolved_slug),
    )

    if not folder.is_dir():
        plan.blockers.append(f"no such folder: {folder}")
        return plan
    if child is None:
        plan.blockers.append(
            f"{folder} holds no loop workspace - nothing to absorb"
            " (a plain code folder needs `loop scope new`, not `absorb`)"
        )
        return plan
    if child.resolve() == Path(main_ws).resolve():
        plan.blockers.append("a workspace cannot absorb itself")
        return plan

    # role ------------------------------------------------------------------
    meta = {}
    meta_path = child / ".loop" / "workspace.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            meta = {}
    role = str(meta.get("role") or "standalone")
    if role == "main" and meta.get("children"):
        plan.blockers.append(
            "this workspace is itself a main product with sub-products of its own -"
            " absorb its children first"
        )

    # binding ---------------------------------------------------------------
    plan.map_id = map_id or _map_id_for(main_ws, folder.name, resolved_slug)
    if not plan.map_id:
        plan.blockers.append(
            f"no PRODUCT_MAP row binds `{folder.name}` - pass --map-id NN"
        )
    plan.name = _row_title(main_ws, plan.map_id) or folder.name

    # target ----------------------------------------------------------------
    if plan.target.exists() and not merge:
        plan.blockers.append(
            f"plan/products/{resolved_slug}/ already exists - pass --merge to fold into it"
        )

    # staged writes and open findings ---------------------------------------
    pending = child / ".loop" / "pending"
    staged = [p for p in pending.rglob("*.json")] if pending.is_dir() else []
    if staged:
        plan.blockers.append(
            f"{len(staged)} staged write(s) in {folder.name}/.loop/pending -"
            " approve or reject them first (`loop pending list`)"
        )

    # code dir --------------------------------------------------------------
    try:
        plan.code_dir = Path(
            folder.relative_to(sp.product_folder(main_ws))
        ).as_posix()
    except ValueError:
        plan.code_dir = folder.as_posix()
        plan.notes.append("sub-product folder is outside the main product - code_dir is absolute")

    # ids -------------------------------------------------------------------
    for task in parse_tasks_file(child / "TASKS.yml"):
        tid = str(task.get("id") or "").strip()
        if tid:
            plan.task_ids[tid] = task_rename(tid, resolved_slug)
    for gate in scope_state.parse_gates_file(child / "GATES.yml"):
        gid = str(gate.get("id"))
        plan.gate_ids[gid] = gate_rename(gid, resolved_slug)
    for match in DOUBT_ID.finditer(_read(child / "DOUBTS.md")):
        did = match.group(0)
        plan.doubt_ids[did] = doubt_rename(did, resolved_slug)

    # dangling references ---------------------------------------------------
    known = set(plan.task_ids)
    for task in parse_tasks_file(child / "TASKS.yml"):
        raw = task.get("blocked_by") or []
        if isinstance(raw, str):
            raw = [raw]
        for blocker in [str(b).strip() for b in raw if str(b).strip()]:
            if blocker.startswith("G-") or blocker in known:
                continue
            plan.dangling.append(f"{task.get('id')} blocked_by {blocker}")

    # decisions -------------------------------------------------------------
    plan.decision_conflicts, plan.decisions_merged = _decision_plan(main_ws, child)
    plan.decision_keys = _child_decision_keys(child)

    # contracts from declared integrations ----------------------------------
    plan.contracts = _integration_ids(child)

    # sessions --------------------------------------------------------------
    plan.sessions = _session_count(child / "state.db")

    # generated files -------------------------------------------------------
    plan.dropped = [rel for rel in GENERATED if (child / rel).exists()]

    return plan


def _map_id_for(main_ws: Path, folder_name: str, slug: str) -> str | None:
    """Bind by what the map declares. Slug-matching is a *reported* fallback only."""
    try:
        from ultraplan_harness import parse_product_map

        rows = parse_product_map(Path(main_ws))
    except Exception:
        return None
    for row in rows or []:
        for column in ("scope", "workspace"):
            declared = str(row.get(column, "")).strip().strip("`/")
            if declared and sp.slugify(Path(declared).name) == slug:
                return str(row.get("id"))
    for row in rows or []:
        if sp.slugify(str(row.get("title", ""))) == slug:
            return str(row.get("id"))
    return None


def _row_title(main_ws: Path, map_id: str | None) -> str:
    if not map_id:
        return ""
    try:
        from ultraplan_harness import parse_product_map

        for row in parse_product_map(Path(main_ws)) or []:
            if str(row.get("id")) == map_id:
                return str(row.get("title") or "")
    except Exception:
        return ""
    return ""


def _decision_plan(main_ws: Path, child: Path) -> tuple[list[str], int]:
    """Topics decided on both sides, and how many entries would merge cleanly."""
    try:
        import hierarchy_drift as drift

        # Only the *platform's* own decisions can conflict with an incoming sub-product.
        # Blocks a previous absorb merged in belong to another sub-product: comparing
        # against them would stop the second absorb over two sub-products having decided
        # their own separate business differently, which is not a conflict at all.
        parent = drift.decision_entries(
            drift.strip_absorbed(_read(Path(main_ws) / "DECISIONS.md")), skip_sections=("pending",)
        )
        mine = drift.decision_entries(_read(child / "DECISIONS.md"), skip_sections=("pending",))
    except Exception:
        return [], 0

    conflicts: list[str] = []
    for key, (label, value) in mine.items():
        if key not in parent:
            continue
        their_label, their_value = parent[key]
        if _norm(their_value) != _norm(value):
            conflicts.append(f"{label or key}: main says `{their_value}`, {child.parent.name} says `{value}`")
    return conflicts, len([k for k in mine if k not in parent])


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().lower().rstrip(".")


def _integration_ids(child: Path) -> list[str]:
    """Counterparties declared in `plan/INTEGRATIONS.yml`, as draft contract ids."""
    path = child / "plan" / "INTEGRATIONS.yml"
    if not path.is_file():
        return []
    out: list[str] = []
    for line in _read(path).splitlines():
        match = re.match(r"^\s*-?\s*counterparty:\s*(.+?)\s*$", line)
        if match:
            value = match.group(1).strip().strip("\"'")
            if value:
                out.append(value)
    return out


def _session_count(db: Path) -> int:
    if not db.exists():
        return 0
    try:
        conn = sqlite3.connect(db)
        try:
            return int(conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


# ---------------------------------------------------------------------------
# applying
# ---------------------------------------------------------------------------


def _rewrite(text: str, plan: Plan) -> str:
    """Rewrite every id this absorb renames, as whole words.

    One pass over the text with a single alternation, so a rewritten id can never be
    rewritten again by a later mapping.
    """
    mapping = {**plan.task_ids, **plan.gate_ids, **plan.doubt_ids}
    mapping = {old: new for old, new in mapping.items() if old != new}
    if not mapping:
        return text
    pattern = re.compile(r"(?<![A-Za-z0-9-])(" + "|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r")(?![A-Za-z0-9-])")
    return pattern.sub(lambda m: mapping[m.group(1)], text)


def _copy_rewritten(src: Path, dst: Path, plan: Plan) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() in {".md", ".yml", ".yaml", ".txt", ".json"}:
        dst.write_text(_rewrite(_read(src), plan), encoding="utf-8")
    else:
        shutil.copy2(src, dst)


def apply_absorb(main_ws: Path, plan: Plan, *, allow_conflicts: bool = False) -> dict:
    """Carry out a planned absorb. Refuses unless the plan is clean."""
    if not plan.ok:
        raise SystemExit("refusing: " + "; ".join(plan.blockers))
    if plan.decision_conflicts and not allow_conflicts:
        raise SystemExit(
            "refusing: the two plans decided the same topic differently -\n  "
            + "\n  ".join(plan.decision_conflicts)
            + "\nResolve it in DECISIONS.md first, or re-run with --accept-conflicts to"
            " keep both entries side by side."
        )

    main_ws = Path(main_ws)
    child = plan.child_ws
    target = plan.target
    report: dict = {"scope": plan.slug, "wrote": [], "dropped": [], "doubts": []}

    # 1. plan content -------------------------------------------------------
    target.mkdir(parents=True, exist_ok=True)

    main_plan = child / "plan" / "main_plan.md"
    if main_plan.is_file():
        prd = target / "prd.md"
        body = _rewrite(_read(main_plan), plan)
        existing = _read(prd)
        if "## From sub-product plan" not in existing:
            prd.write_text(
                (existing + "\n\n" if existing.strip() else "")
                + "## From sub-product plan\n\n"
                + body,
                encoding="utf-8",
            )
            report["wrote"].append(str(prd.relative_to(main_ws)))

    for name in PLAN_TREES:
        src = child / "plan" / name
        if not src.is_dir():
            continue
        for item in src.rglob("*"):
            if item.is_file():
                _copy_rewritten(item, target / name / item.relative_to(src), plan)
        report["wrote"].append(f"plan/products/{plan.slug}/{name}/")

    for src_name, dst_name in (
        ("TASKS.yml", "TASKS.yml"),
        ("GATES.yml", "GATES.yml"),
        ("DOUBTS.md", "DOUBTS.md"),
        ("CURRENT_STATE.md", "CURRENT_STATE.md"),
        ("HANDOFF.md", "HANDOFF.md"),
    ):
        src = child / src_name
        if src.is_file():
            _copy_rewritten(src, target / dst_name, plan)
            report["wrote"].append(f"plan/products/{plan.slug}/{dst_name}")

    # other authored plan files (PRD, architecture, the ultraplan pack) ------
    plan_dir = child / "plan"
    if plan_dir.is_dir():
        skip = {Path(rel).name for rel in GENERATED} | {"main_plan.md", "INTEGRATIONS.yml"}
        for item in plan_dir.glob("*"):
            if item.is_file() and item.name not in skip:
                _copy_rewritten(item, target / item.name, plan)

    # 2. dangling references become doubts, never silent drops ---------------
    if plan.dangling:
        doubts = target / "DOUBTS.md"
        lines = [_read(doubts).rstrip(), "", f"## Unresolved after absorb ({_now_stamp()})", ""]
        for item in plan.dangling:
            lines.append(f"- `{item}` - the blocking task was not found in this sub-product.")
        doubts.write_text("\n".join(lines).lstrip() + "\n", encoding="utf-8")
        report["doubts"] = list(plan.dangling)

    # 3. decisions and evidence merge into the shared files ------------------
    report["decisions"] = _merge_decisions(main_ws, child, plan)
    report["evidence"] = _merge_evidence(main_ws, child, plan)

    # 4. memory becomes a per-scope file ------------------------------------
    memory = child / "memories" / "MEMORY.md"
    if memory.is_file():
        dst = main_ws / "memories" / "scopes" / f"{plan.slug}.md"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(_rewrite(_read(memory), plan), encoding="utf-8")
        report["wrote"].append(str(dst.relative_to(main_ws)))

    # 5. sessions carry their scope into the shared index -------------------
    report["sessions"] = _merge_sessions(main_ws, child, plan.slug)

    # 6. the scope record ---------------------------------------------------
    # Written *before* contracts are seeded: seeding records what this scope now
    # consumes, and a scope that does not exist yet cannot be updated - the write
    # that followed would simply overwrite it with an empty `consumes`.
    scope = sp.Scope(
        slug=plan.slug,
        path=target,
        name=plan.name or plan.slug,
        map_id=plan.map_id,
        code_dir=plan.code_dir,
        code_layout="own-dir",
        type="sub-product",
        status="building",
        decision_keys=plan.decision_keys,
        absorbed_from=str(child),
    )
    sp.write_scope(main_ws, scope)
    report["wrote"].append(f"plan/products/{plan.slug}/scope.json")

    # 7. contracts seeded from declared integrations ------------------------
    report["contracts"] = _seed_contracts(main_ws, plan)

    # 8. the map row now points at the scope --------------------------------
    if _bind_map_row(main_ws, plan):
        report["wrote"].append("plan/PRODUCT_MAP.md")

    # 9. retire the child workspace last ------------------------------------
    report["dropped"] = list(plan.dropped)
    archived = _archive(child)
    report["archived"] = str(archived)
    report["unlinked"] = _unlink_child(main_ws, plan)
    sp.write_pointer(plan.folder, plan.slug)
    report["wrote"].append(str(Path(plan.folder) / sp.POINTER_FILE))

    return report



def _unlink_child(main_ws: Path, plan: Plan) -> bool:
    """Drop the absorbed sub-product from the main workspace's `children` list.

    Without this the hierarchy bridge keeps the entry, finds the folder present but its
    `.loop-engineer/` gone, and reports `missing-link` - an error-level finding, every
    session, forever. Measured on a real three-sub-product platform: three permanent
    errors telling the user to restore folders that were deliberately absorbed.

    The scope is now the record of that sub-product. The link is not.
    """
    try:
        from workspace_tree import unlink

        return bool(unlink(main_ws, plan.folder.name))
    except Exception:  # noqa: BLE001 - never fail an absorb over bookkeeping
        return False



def _child_decision_keys(child: Path) -> list[str]:
    """Decision topics the sub-product is bringing with it.

    Stored on the scope so the platform surface can exclude them for good. The marker
    written into `DECISIONS.md` is not enough on its own: `loop archive` compacts that
    file by rebuilding entries, and drops a bare HTML comment while doing it.
    """
    try:
        import hierarchy_drift as drift

        return sorted(drift.decision_entries(_read(child / "DECISIONS.md"), skip_sections=("pending",)))
    except Exception:  # noqa: BLE001
        return []


def _merge_decisions(main_ws: Path, child: Path, plan: Plan) -> int:
    src = child / "DECISIONS.md"
    if not src.is_file():
        return 0
    dst = Path(main_ws) / "DECISIONS.md"
    marker = f"<!-- absorbed:{plan.slug} -->"
    existing = _read(dst)
    if marker in existing:
        return 0
    block = [
        existing.rstrip(),
        "",
        marker,
        f"## Decisions from sub-product `{plan.slug}` (absorbed {_now_stamp()})",
        "",
        f"Every entry below is scoped to `{plan.slug}` unless it says otherwise.",
        "",
        _rewrite(_read(src), plan).strip(),
        "",
    ]
    dst.write_text("\n".join(block).lstrip() + "\n", encoding="utf-8")
    return 1


def _merge_evidence(main_ws: Path, child: Path, plan: Plan) -> int:
    src = child / "EVIDENCE_LOG.md"
    if not src.is_file():
        return 0
    dst = Path(main_ws) / "EVIDENCE_LOG.md"
    marker = f"<!-- absorbed:{plan.slug} -->"
    existing = _read(dst)
    if marker in existing:
        return 0
    dst.write_text(
        (existing.rstrip() + "\n\n" if existing.strip() else "")
        + f"{marker}\n## Evidence from `{plan.slug}` (absorbed {_now_stamp()})\n\n"
        + _read(src).strip()
        + "\n",
        encoding="utf-8",
    )
    return 1


def _merge_sessions(main_ws: Path, child: Path, slug: str) -> int:
    """Copy the child's sessions into the shared index, tagged with the scope.

    Ids are not preserved - they are reassigned by the shared table's autoincrement,
    and the FTS index is rebuilt from the insert trigger. Nothing references a session
    id across files, so remapping them costs nothing and avoids a collision.
    """
    src_db = child / "state.db"
    if not src_db.exists():
        return 0
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import session_store

    dst_db = Path(main_ws) / "state.db"
    try:
        src = sqlite3.connect(src_db)
        src.row_factory = sqlite3.Row
        rows = src.execute(
            "SELECT created_at, workspace, command, title, body, tags FROM sessions ORDER BY id"
        ).fetchall()
        src.close()
    except sqlite3.Error:
        return 0

    if not rows:
        return 0

    conn = session_store.connect(dst_db)
    try:
        existing = {
            (r["created_at"], r["title"])
            for r in conn.execute("SELECT created_at, title FROM sessions")
        }
        added = 0
        for row in rows:
            if (row["created_at"], row["title"]) in existing:
                continue
            conn.execute(
                "INSERT INTO sessions (created_at, workspace, command, title, body, tags, scope)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row["created_at"],
                    row["workspace"],
                    row["command"],
                    row["title"],
                    row["body"],
                    row["tags"],
                    slug,
                ),
            )
            added += 1
        conn.commit()
        return added
    finally:
        conn.close()


def _seed_contracts(main_ws: Path, plan: Plan) -> list[str]:
    """Declared integrations become draft contracts - unresolved ones stay loud.

    A counterparty that names no scope here becomes a contract with no provider, which
    the checker reports as `contract-unprovided`. That is the correct failure: the
    dependency was declared and cannot be satisfied yet.
    """
    if not plan.contracts:
        return []
    import contracts as ct

    scope = sp.find_scope(main_ws, plan.slug)
    consumes: list[str] = []
    written: list[str] = []
    for counterparty in plan.contracts:
        provider = sp.find_scope(main_ws, counterparty)
        provider_slug = provider.slug if provider else ""
        contract_id = f"{provider_slug or sp.slugify(counterparty)}.{plan.slug}-v1"
        path = ct.contracts_dir(main_ws) / f"{contract_id}.yml"
        if path.exists():
            continue
        ct.write_contract(
            main_ws,
            ct.Contract(
                id=contract_id,
                path=path,
                provider=provider_slug,
                status=ct.DRAFT,
                surface="",
                consumers=[ct.Consumer(scope=plan.slug, status="planned")],
            ),
        )
        consumes.append(contract_id)
        written.append(contract_id)

    if scope is not None and consumes:
        scope.consumes = sorted(set(scope.consumes) | set(consumes))
        sp.write_scope(main_ws, scope)

    # The provider's own `provides` is updated too. The contract file already names it
    # as provider, so leaving its scope.json silent would make every absorb emit a
    # `contract-undeclared` warning about bookkeeping rather than about the plan.
    # Whether the provider has *agreed* is carried by the contract's `draft` status and
    # the consumer's `planned` status - not by this list.
    for contract_id in written:
        provider_slug = contract_id.split(".", 1)[0]
        provider = sp.find_scope(main_ws, provider_slug)
        if provider is None or provider.slug == plan.slug:
            continue
        if contract_id not in provider.provides:
            provider.provides = sorted(set(provider.provides) | {contract_id})
            sp.write_scope(main_ws, provider)
    return written


def _bind_map_row(main_ws: Path, plan: Plan) -> bool:
    """Point the map row at the scope folder, adding a `Scope` column if needed."""
    path = Path(main_ws) / "plan" / "PRODUCT_MAP.md"
    if not path.is_file() or not plan.map_id:
        return False
    lines = _read(path).splitlines()
    out: list[str] = []
    changed = False
    header_cells: list[str] = []
    scope_index: int | None = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and not changed:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            lowered = [c.lower() for c in cells]
            if "id" in lowered and "title" in lowered:
                header_cells = cells
                scope_index = lowered.index("scope") if "scope" in lowered else None
                if scope_index is None:
                    cells.append("Scope")
                    scope_index = len(cells) - 1
                    out.append("| " + " | ".join(cells) + " |")
                    continue
            elif header_cells and re.match(r"^[-:\s|]+$", stripped.strip("|")):
                if scope_index is not None and len(cells) < len(header_cells) + 1:
                    cells.append("---")
                out.append("| " + " | ".join(cells) + " |")
                continue
            elif header_cells and cells and cells[0] == plan.map_id:
                while len(cells) <= (scope_index or 0):
                    cells.append("")
                cells[scope_index] = f"`plan/products/{plan.slug}`"
                out.append("| " + " | ".join(cells) + " |")
                changed = True
                continue
        out.append(line)

    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return changed


def _archive(child: Path) -> Path:
    """Rename the child workspace so resolution stops finding it.

    Renaming is load-bearing, not tidiness: `workspace_resolver._has_markers_at` looks
    for `memories/MEMORY.md` and friends at `<folder>/.loop-engineer`. Leave that path
    intact and every future session run inside the folder silently resolves to the dead
    workspace instead of the main one.
    """
    if child.name != ".loop-engineer":
        return child
    target = child.with_name(f".loop-engineer.absorbed-{_now_stamp()}")
    suffix = 2
    while target.exists():
        target = child.with_name(f".loop-engineer.absorbed-{_now_stamp()}-{suffix}")
        suffix += 1
    child.rename(target)
    return target


# ---------------------------------------------------------------------------
# bulk
# ---------------------------------------------------------------------------


def discover(main_ws: Path) -> list[Path]:
    """Sub-product folders under the main product that still hold their own workspace."""
    try:
        from workspace_tree import scan_children

        return list(scan_children(sp.product_folder(main_ws)))
    except Exception:
        folder = sp.product_folder(main_ws)
        return [p.parent for p in folder.glob("*/.loop-engineer") if p.is_dir()]


def order_folders(main_ws: Path, folders: list[Path]) -> list[Path]:
    """Absorb order: what others depend on first.

    Derived from the map's `Depends on`, so a sub-product whose tasks other
    sub-products block on is imported before them and every `blocked_by` resolves.
    """
    ids: dict[str, Path] = {}
    for folder in folders:
        row = _map_id_for(main_ws, folder.name, sp.slugify(folder.name))
        if row:
            ids[row] = folder

    deps = sp._map_dependencies(main_ws)
    ordered: list[Path] = []
    done: set[str] = set()
    remaining = dict(ids)
    while remaining:
        ready = sorted(
            rid for rid in remaining if not {d.zfill(2) for d in deps.get(rid, [])} & (set(ids) - done)
        )
        if not ready:
            break
        for rid in ready:
            ordered.append(remaining.pop(rid))
            done.add(rid)
    ordered.extend(remaining.values())
    ordered.extend(f for f in folders if f not in ordered)
    return ordered


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _describe(plan: Plan) -> str:
    lines = [f"# Absorb `{plan.folder.name}` as scope `{plan.slug}`", ""]
    if plan.blockers:
        lines.append("**Refused:**")
        lines.extend(f"- {b}" for b in plan.blockers)
        return "\n".join(lines)

    lines.extend(
        [
            f"- Map row: {plan.map_id or '(none)'} - {plan.name}",
            f"- Plan goes to: `plan/products/{plan.slug}/`",
            f"- Code dir: `{plan.code_dir}`",
            f"- Tasks renamed: {len(plan.task_ids)}",
            f"- Gates renamed: {len(plan.gate_ids)}",
            f"- Doubts renamed: {len(plan.doubt_ids)}",
            f"- Decisions merged into the shared file: {plan.decisions_merged}",
            f"- Sessions folded into state.db: {plan.sessions}",
        ]
    )
    if plan.contracts:
        lines.append(f"- Declared integrations to seed as draft contracts: {', '.join(plan.contracts)}")
    if plan.dropped:
        lines.append(f"- Dropped (generated): {', '.join(plan.dropped)}")
    if plan.dangling:
        lines.append(f"- Recorded as doubts: {len(plan.dangling)} unresolved reference(s)")
    if plan.decision_conflicts:
        lines.extend(["", "**Stops here - the same topic is decided both ways:**"])
        lines.extend(f"- {c}" for c in plan.decision_conflicts)
    if plan.notes:
        lines.extend(["", *[f"- {n}" for n in plan.notes]])
    return "\n".join(lines)


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="Absorb a sub-product workspace into the main product.")
    parser.add_argument("command", choices=["absorb", "discover"])
    parser.add_argument("target", nargs="?", help="Folder to absorb.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--map-id", default=None)
    parser.add_argument("--slug", default=None)
    parser.add_argument("--all", action="store_true", help="Absorb every sub-product workspace found.")
    parser.add_argument("--merge", action="store_true", help="Fold into an existing scope folder.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--accept-conflicts", action="store_true", help="Keep both sides of a decision conflict.")
    args = parser.parse_args()

    main_ws = resolve_workspace(args.workspace)

    if args.command == "discover":
        found = order_folders(main_ws, discover(main_ws))
        if not found:
            print("No sub-product workspaces under this main product.")
            return 0
        print("Sub-product workspaces, in absorb order (dependencies first):")
        for folder in found:
            print(f"  {folder.name}  ({folder})")
        return 0


    folders = order_folders(main_ws, discover(main_ws)) if args.all else [Path(args.target or ".")]
    if not folders:
        print("Nothing to absorb.")
        return 0

    failed = 0
    for folder in folders:
        plan = plan_absorb(main_ws, folder, map_id=args.map_id, merge=args.merge, slug=args.slug)
        print(_describe(plan))
        print()
        if not plan.ok:
            failed += 1
            if args.all:
                print("Stopping - a bulk absorb does not skip past a refusal.")
                break
            continue
        if args.dry_run:
            continue
        report = apply_absorb(main_ws, plan, allow_conflicts=args.accept_conflicts)
        print(f"Absorbed `{plan.slug}`. Archived workspace: {report['archived']}")
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
