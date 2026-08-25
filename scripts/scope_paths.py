"""Product scopes: one workspace, many sub-products.

A **scope** is a sub-product planned and built inside the main product's single
`.loop-engineer/` workspace, at `plan/products/<slug>/`. It replaces the federated
model where each sub-product owned a workspace of its own and the two ends had to be
kept in sync across a boundary (`docs/proposals/unified-workspace.md`).

Three things this module is deliberately strict about, because each was a real failure
in the federated design:

- **The folder name is not the binding key.** `scope.json` carries `map_id`, written
  once at creation. `workspace_tree.map_id_for()` binds a *workspace* by slug-equality
  of folder name to row title, which is why retitling a row silently unbound it and
  left the row "unbuilt while looking built".
- **Ambiguity never resolves.** Two scopes matching a command's text stops and asks.
  Picking the first is the mis-binding that `map_id_for`'s substring fallback was
  removed for.
- **A remembered scope is re-confirmed after a break.** Sticky selection is what keeps
  the user from retyping the name all day; unbounded stickiness is how a session
  silently builds the wrong sub-product tomorrow.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCOPES_DIR = "plan/products"
SCOPE_META = "scope.json"
ACTIVE_SCOPE_FILE = ".loop/active-scope.json"
POINTER_FILE = ".loop-scope"

#: How long a remembered scope keeps being used without asking. Past this, or in a
#: different session, the command re-confirms before continuing on it.
STICKY_HOURS = 12

CODE_LAYOUTS = ("own-dir", "shared", "external")

PLATFORM = "platform"


def slugify(value: str) -> str:
    """Same rule as `plan_paths.slugify`, duplicated to keep this module importable
    on its own (the absorber runs it before the plan modules are needed)."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(value).strip().lower()).strip("-")
    return slug


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# the scope record
# ---------------------------------------------------------------------------


@dataclass
class Scope:
    """One sub-product's plan folder, as `scope.json` describes it."""

    slug: str
    path: Path
    name: str = ""
    map_id: str | None = None
    aliases: list[str] = field(default_factory=list)
    code_dir: str | None = None
    code_layout: str = "own-dir"
    type: str = "sub-product"
    status: str = "planned"
    provides: list[str] = field(default_factory=list)
    consumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    absorbed_from: str | None = None

    @property
    def title(self) -> str:
        return self.name or self.slug

    def code_path(self, workspace: Path) -> Path | None:
        """Absolute code directory, resolved against the *product* folder.

        The workspace is `<product>/.loop-engineer`, and `code_dir` is written
        relative to the product folder - `services/auth`, not
        `../services/auth` - because that is what the user sees and types.
        """
        if not self.code_dir:
            return None
        raw = Path(self.code_dir)
        if raw.is_absolute():
            return raw
        return (product_folder(workspace) / raw).resolve()

    def to_json(self) -> dict:
        data = {
            "slug": self.slug,
            "map_id": self.map_id,
            "name": self.name,
            "aliases": self.aliases,
            "code_dir": self.code_dir,
            "code_layout": self.code_layout,
            "type": self.type,
            "status": self.status,
            "provides": self.provides,
            "consumes": self.consumes,
            "depends_on": self.depends_on,
        }
        if self.absorbed_from:
            data["absorbed_from"] = self.absorbed_from
        return {k: v for k, v in data.items() if v not in (None, [], "")}

    # what a scope owns on disk -------------------------------------------------

    @property
    def tasks_file(self) -> Path:
        return self.path / "TASKS.yml"

    @property
    def gates_file(self) -> Path:
        return self.path / "GATES.yml"

    @property
    def doubts_file(self) -> Path:
        return self.path / "DOUBTS.md"

    @property
    def features_dir(self) -> Path:
        return self.path / "features"

    @property
    def steps_dir(self) -> Path:
        return self.path / "steps"


def product_folder(workspace: Path) -> Path:
    """The folder the workspace describes - the parent of `.loop-engineer/`."""
    resolved = Path(workspace).resolve()
    if resolved.name == ".loop-engineer":
        return resolved.parent
    return resolved


# ---------------------------------------------------------------------------
# read / write
# ---------------------------------------------------------------------------


def scopes_dir(workspace: Path) -> Path:
    return Path(workspace) / "plan" / "products"


def scope_dir(workspace: Path, slug: str) -> Path:
    return scopes_dir(workspace) / slug


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return []


def read_scope(folder: Path) -> Scope | None:
    """Tolerant read - a malformed `scope.json` must never break a session.

    A folder under `plan/products/` with no readable `scope.json` is still a scope
    (its slug is the folder name); it just carries no binding or code dir. Refusing
    to see it would hide work rather than protect anything.
    """
    folder = Path(folder)
    if not folder.is_dir():
        return None
    data: dict = {}
    meta = folder / SCOPE_META
    if meta.exists():
        try:
            loaded = json.loads(meta.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            data = {}
    return Scope(
        slug=str(data.get("slug") or folder.name),
        path=folder,
        name=str(data.get("name") or ""),
        map_id=(str(data["map_id"]) if data.get("map_id") not in (None, "") else None),
        aliases=_as_list(data.get("aliases")),
        code_dir=(str(data["code_dir"]) if data.get("code_dir") else None),
        code_layout=str(data.get("code_layout") or "own-dir"),
        type=str(data.get("type") or "sub-product"),
        status=str(data.get("status") or "planned"),
        provides=_as_list(data.get("provides")),
        consumes=_as_list(data.get("consumes")),
        depends_on=_as_list(data.get("depends_on")),
        absorbed_from=(str(data["absorbed_from"]) if data.get("absorbed_from") else None),
    )


def list_scopes(workspace: Path) -> list[Scope]:
    root = scopes_dir(workspace)
    if not root.is_dir():
        return []
    found: list[Scope] = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        scope = read_scope(child)
        if scope is not None:
            found.append(scope)
    return found


def write_scope(workspace: Path, scope: Scope) -> Path:
    scope.path.mkdir(parents=True, exist_ok=True)
    meta = scope.path / SCOPE_META
    meta.write_text(json.dumps(scope.to_json(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return meta


def create_scope(
    workspace: Path,
    slug: str,
    *,
    name: str = "",
    map_id: str | None = None,
    code_dir: str | None = None,
    code_layout: str = "own-dir",
    type: str = "sub-product",
    aliases: list[str] | None = None,
) -> Scope:
    slug = slugify(slug)
    if not slug:
        raise ValueError("a scope needs a slug")
    scope = Scope(
        slug=slug,
        path=scope_dir(workspace, slug),
        name=name or slug,
        map_id=map_id,
        aliases=aliases or [],
        code_dir=code_dir,
        code_layout=code_layout,
        type=type,
    )
    for sub in ("steps", "features"):
        (scope.path / sub).mkdir(parents=True, exist_ok=True)
    write_scope(workspace, scope)
    return scope


def workspace_mode(workspace: Path) -> str:
    """`unified` once this workspace plans sub-products as scopes, else `federated`.

    Read from `.loop/workspace.json` when it says, and inferred from the presence of
    `plan/products/` otherwise. Inferring matters: an absorb makes a workspace unified
    whether or not anyone remembered to set a flag, and a federated workspace that has
    never seen a scope must keep behaving exactly as it did.
    """
    meta = Path(workspace) / ".loop" / "workspace.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            mode = str((data or {}).get("mode") or "")
            if mode in {"unified", "federated"}:
                return mode
        except (json.JSONDecodeError, OSError):
            pass
    return "unified" if list_scopes(workspace) else "federated"


def set_workspace_mode(workspace: Path, mode: str) -> None:
    if mode not in {"unified", "federated"}:
        raise ValueError(f"unknown mode: {mode}")
    meta = Path(workspace) / ".loop" / "workspace.json"
    meta.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8")) or {}
        except (json.JSONDecodeError, OSError):
            data = {}
    data["mode"] = mode
    meta.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# addressing: slug, map id, name, alias, code dir
# ---------------------------------------------------------------------------


def find_scope(workspace: Path, token: str) -> Scope | None:
    """Resolve one explicit token. Exact only - this is the `--scope` path."""
    if not token:
        return None
    token = str(token).strip()
    scopes = list_scopes(workspace)
    wanted = slugify(token)

    for scope in scopes:
        if scope.slug == wanted:
            return scope
    for scope in scopes:
        if scope.map_id and scope.map_id == token.zfill(2):
            return scope
    for scope in scopes:
        if slugify(scope.name) == wanted:
            return scope
    for scope in scopes:
        if any(slugify(alias) == wanted for alias in scope.aliases):
            return scope
    # A path into the scope's code dir, so `--scope services/auth` works. Both the
    # whole path and its last segment count - the user types whichever they can see.
    for scope in scopes:
        if not scope.code_dir:
            continue
        declared = Path(scope.code_dir.replace("\\", "/"))
        given = Path(token.replace("\\", "/"))
        if slugify(str(declared)) == slugify(str(given)) or slugify(declared.name) == slugify(given.name):
            return scope
    return None


@dataclass
class Match:
    """What the command text resolved to. `scope` is set only when unambiguous."""

    scope: Scope | None = None
    candidates: list[Scope] = field(default_factory=list)
    how: str = "none"  # slug | map-id | name | alias | prefix | none | ambiguous

    @property
    def ok(self) -> bool:
        return self.scope is not None

    @property
    def ambiguous(self) -> bool:
        return self.scope is None and len(self.candidates) > 1


_WORD = re.compile(r"[a-z0-9]+")


def _words(text: str) -> list[str]:
    return _WORD.findall(str(text).lower())


def match_text(workspace: Path, text: str, *, min_prefix: int = 3) -> Match:
    """Find the scope a command's text names, deterministically.

    Rules first, no model call (`AGENTS.md` non-negotiable #4). Tried in order, and
    the first *tier* that matches decides - a later, weaker tier never overrides a
    stronger one, and more than one hit inside a tier is ambiguous rather than a
    coin flip:

    1. exact slug or two-digit map id as a whole word
    2. full name or alias appearing as a whole phrase
    3. a unique slug prefix of at least `min_prefix` characters

    `/plan-loop start working on auth product` -> tier 1 on `auth`.
    """
    scopes = list_scopes(workspace)
    if not scopes or not text:
        return Match()

    words = _words(text)
    if not words:
        return Match()
    word_set = set(words)
    joined = " ".join(words)

    tier1 = [s for s in scopes if s.slug in word_set or (s.map_id and s.map_id in word_set)]
    if tier1:
        return Match(scope=tier1[0] if len(tier1) == 1 else None, candidates=tier1, how="slug")

    def phrase_hit(scope: Scope) -> bool:
        for candidate in [scope.name, *scope.aliases]:
            phrase = " ".join(_words(candidate))
            if not phrase:
                continue
            if re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", joined):
                return True
        return False

    tier2 = [s for s in scopes if phrase_hit(s)]
    if tier2:
        return Match(scope=tier2[0] if len(tier2) == 1 else None, candidates=tier2, how="name")

    tier3: list[Scope] = []
    for word in words:
        if len(word) < min_prefix:
            continue
        hits = [s for s in scopes if s.slug.startswith(word) and s not in tier3]
        if len(hits) == 1:
            tier3.extend(hits)
        elif len(hits) > 1:
            return Match(candidates=hits, how="prefix")
    if len(tier3) == 1:
        return Match(scope=tier3[0], candidates=tier3, how="prefix")
    if len(tier3) > 1:
        return Match(candidates=tier3, how="prefix")

    return Match()


# ---------------------------------------------------------------------------
# the remembered (active) scope
# ---------------------------------------------------------------------------


def active_file(workspace: Path) -> Path:
    return Path(workspace) / ".loop" / "active-scope.json"


def read_active(workspace: Path) -> dict | None:
    path = active_file(workspace)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict) or not data.get("slug"):
        return None
    return data


def set_active(workspace: Path, slug: str, *, session: str | int | None = None) -> Path:
    path = active_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": slug,
        "set_at": _now().isoformat(),
        "set_by_session": str(session) if session is not None else None,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def clear_active(workspace: Path) -> None:
    path = active_file(workspace)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def _stale(record: dict, session: str | int | None, hours: int = STICKY_HOURS) -> bool:
    """Stale = a different session, or older than the window. Deterministic, not a feel.

    One session's work continues without friction; coming back tomorrow always gets a
    checkpoint before the remembered scope absorbs work meant for another one.
    """
    if session is not None:
        stored = record.get("set_by_session")
        if stored is not None and str(stored) != str(session):
            return True
    raw = record.get("set_at")
    if not raw:
        return True
    try:
        when = datetime.fromisoformat(str(raw))
    except ValueError:
        return True
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return _now() - when > timedelta(hours=hours)


# ---------------------------------------------------------------------------
# the `.loop-scope` convenience pointer
# ---------------------------------------------------------------------------


def write_pointer(folder: Path, slug: str) -> Path:
    path = Path(folder) / POINTER_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(slug + "\n", encoding="utf-8")
    return path


def pointer_slug(start: Path | None = None, *, stop_at: Path | None = None) -> str | None:
    """Walk up from `start` for a `.loop-scope` file. Convenience only - nothing
    in the design depends on these existing, since the decided model is that every
    command runs from the main folder."""
    current = (start or Path.cwd()).resolve()
    stop = stop_at.resolve() if stop_at else None
    for path in [current, *current.parents]:
        pointer = path / POINTER_FILE
        if pointer.is_file():
            try:
                value = pointer.read_text(encoding="utf-8").strip()
            except OSError:
                return None
            return value or None
        if stop is not None and path == stop:
            break
    return None


# ---------------------------------------------------------------------------
# resolution - what every command calls
# ---------------------------------------------------------------------------


@dataclass
class Resolution:
    """The answer to "which sub-product is this command about?"."""

    scope: Scope | None = None
    source: str = "none"  # flag | text | pointer | remembered | none
    needs_confirm: bool = False
    candidates: list[Scope] = field(default_factory=list)
    reason: str = ""

    @property
    def slug(self) -> str:
        return self.scope.slug if self.scope else PLATFORM

    @property
    def is_platform(self) -> bool:
        return self.scope is None


def resolve(
    workspace: Path,
    *,
    explicit: str | None = None,
    text: str | None = None,
    session: str | int | None = None,
    cwd: Path | None = None,
) -> Resolution:
    """Resolve the active scope for one command.

    Order (section 3.1 of the proposal): explicit flag, then the command's own text,
    then a `.loop-scope` pointer, then the remembered scope - and nothing else. When
    none of them answer, the caller must **ask**; this never falls back to platform
    silently, because a forgotten word would then become edits to shared CI, schema
    or design-system code.
    """
    scopes = list_scopes(workspace)
    if not scopes:
        return Resolution(source="none", reason="This workspace has no sub-product scopes.")

    if explicit:
        found = find_scope(workspace, explicit)
        if found is None:
            return Resolution(
                source="flag",
                candidates=scopes,
                reason=f"No scope named `{explicit}`.",
            )
        return Resolution(scope=found, source="flag")

    if text:
        match = match_text(workspace, text)
        if match.ok:
            return Resolution(scope=match.scope, source="text")
        if match.ambiguous:
            names = ", ".join(s.slug for s in match.candidates)
            return Resolution(
                source="text",
                candidates=match.candidates,
                reason=f"That names more than one sub-product ({names}) - say which.",
            )

    pointed = pointer_slug(cwd, stop_at=product_folder(workspace)) if cwd else None
    if pointed:
        found = find_scope(workspace, pointed)
        if found is not None:
            return Resolution(scope=found, source="pointer")

    record = read_active(workspace)
    if record:
        found = find_scope(workspace, str(record.get("slug")))
        if found is not None:
            stale = _stale(record, session)
            return Resolution(
                scope=found,
                source="remembered",
                needs_confirm=stale,
                reason=(
                    f"Last scope was `{found.slug}`, set {_age(record)}."
                    " Continue there, or switch?"
                    if stale
                    else ""
                ),
            )

    return Resolution(
        source="none",
        candidates=scopes,
        reason="No sub-product named and none remembered - ask which one.",
    )


def _age(record: dict) -> str:
    raw = record.get("set_at")
    try:
        when = datetime.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return "at an unknown time"
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    delta = _now() - when
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)} minutes ago"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() // 3600)} hours ago"
    return f"{delta.days} days ago"


# ---------------------------------------------------------------------------
# the federated bridge: does this workspace still have a boundary to serve?
# ---------------------------------------------------------------------------


def external_scopes(workspace: Path) -> list[Scope]:
    """Scopes whose code and plan live in another repo, and so keep their own workspace."""
    out: list[Scope] = []
    for folder in (scopes_dir(workspace).iterdir() if scopes_dir(workspace).is_dir() else []):
        if not folder.is_dir():
            continue
        meta = folder / SCOPE_META
        if not meta.exists():
            continue
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and (data.get("external") or data.get("code_layout") == "external"):
            scope = read_scope(folder)
            if scope is not None:
                out.append(scope)
    return out


def bridge_state(workspace: Path) -> dict:
    """Whether the cross-workspace hierarchy bridge has anything to do here.

    The bridge - `PARENT_CONTEXT.md`, the parent watermark, derived findings,
    `SUBPRODUCTS.md` - exists to keep two *workspaces* agreeing. It is worth running
    exactly when a second workspace is still involved:

    - a **parent**, when this workspace is a sub-product
    - a **child workspace** that still holds its own loop data: either a sub-product in
      another repo (`external`), or one that has not been absorbed yet
    - never for a scope, which lives in this workspace and has no boundary at all

    Returned rather than asserted, so callers can say *why* they skipped it. A workspace
    that has absorbed everything gets `needed: False` and stops paying for a sync that
    can only ever find nothing.
    """
    mode = workspace_mode(workspace)
    boundaries: list[str] = []
    parent = None
    try:
        from workspace_tree import resolve_children, resolve_parent

        for child in resolve_children(workspace):
            if not child.get("missing"):
                boundaries.append(str(child.get("name")))
        found = resolve_parent(workspace)
        parent = str(found["name"]) if found else None
    except Exception:  # noqa: BLE001 - hierarchy is optional; never break a session
        pass

    external = [s.slug for s in external_scopes(workspace)]
    needed = bool(boundaries or parent or external)

    if needed:
        reason = "a second workspace is still involved"
    elif mode == "unified":
        reason = (
            "unified workspace - every sub-product is a scope in `plan/products/`,"
            " so there is no boundary to sync"
        )
    else:
        reason = "standalone workspace - no parent and no sub-product workspaces"

    return {
        "mode": mode,
        "needed": needed,
        "reason": reason,
        "boundaries": boundaries,
        "external": external,
        "parent": parent,
    }


# ---------------------------------------------------------------------------
# dependency order
# ---------------------------------------------------------------------------


def dependency_order(workspace: Path, scopes: list[Scope] | None = None) -> tuple[list[Scope], list[list[str]]]:
    """Scopes sorted so that what others depend on comes first.

    Edges come from three declared sources, never from prose: `depends_on` in
    `scope.json`, the provider of every id in `consumes`, and the `Depends on`
    column of `PRODUCT_MAP.md` mapped through `map_id`.

    Returns `(ordered, cycles)`. A cycle is reported rather than broken: two
    sub-products depending on each other is a planning problem, and silently cutting
    an arbitrary edge hides it.
    """
    scopes = list(scopes if scopes is not None else list_scopes(workspace))
    by_slug = {s.slug: s for s in scopes}
    by_map = {s.map_id: s for s in scopes if s.map_id}

    provider_of: dict[str, str] = {}
    for scope in scopes:
        for contract_id in scope.provides:
            provider_of[contract_id] = scope.slug

    deps: dict[str, set[str]] = {s.slug: set() for s in scopes}

    def add(slug: str, target: str | None) -> None:
        if target and target in by_slug and target != slug:
            deps[slug].add(target)

    for scope in scopes:
        for raw in scope.depends_on:
            token = str(raw).strip()
            add(scope.slug, by_map[token.zfill(2)].slug if token.zfill(2) in by_map else slugify(token))
        for contract_id in scope.consumes:
            add(scope.slug, provider_of.get(contract_id))

    for row_id, row_deps in _map_dependencies(workspace).items():
        scope = by_map.get(row_id)
        if scope is None:
            continue
        for dep in row_deps:
            target = by_map.get(dep.zfill(2))
            if target is not None:
                add(scope.slug, target.slug)

    ordered: list[Scope] = []
    done: set[str] = set()
    remaining = {s.slug for s in scopes}
    while remaining:
        ready = sorted(slug for slug in remaining if not (deps[slug] - done))
        if not ready:
            break
        for slug in ready:
            ordered.append(by_slug[slug])
            done.add(slug)
            remaining.discard(slug)

    cycles = _cycles({slug: deps[slug] for slug in remaining}) if remaining else []
    return ordered, cycles


def _map_dependencies(workspace: Path) -> dict[str, list[str]]:
    """`Depends on` per row id, read through the existing map parser when available."""
    try:
        from ultraplan_harness import parse_product_map

        rows = parse_product_map(Path(workspace))
    except Exception:
        return {}
    out: dict[str, list[str]] = {}
    for row in rows or []:
        row_id = str(row.get("id") or "").strip()
        if not row_id:
            continue
        raw = str(row.get("depends") or "").replace(";", ",")
        deps = [d.strip() for d in raw.split(",") if d.strip() and d.strip() not in {"-", "—"}]
        if deps:
            out[row_id] = deps
    return out


def _cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Every dependency loop left after the topological pass, each reported once."""
    found: list[list[str]] = []
    seen: set[str] = set()

    def walk(node: str, trail: list[str]) -> None:
        if node in trail:
            cycle = trail[trail.index(node):] + [node]
            key = tuple(sorted(set(cycle)))
            if key not in seen_keys:
                seen_keys.add(key)
                found.append(cycle)
            return
        if node in seen:
            return
        for nxt in sorted(graph.get(node, set())):
            if nxt in graph:
                walk(nxt, trail + [node])
        seen.add(node)

    seen_keys: set[tuple] = set()
    for start in sorted(graph):
        walk(start, [])
    return found
