"""Cross-scope interfaces: one provider, many consumers, checked deterministically.

The federated design expressed "portal needs something from auth" as a `contract-gap`
*finding* - a complaint that two plans, in two workspaces, disagreed. Its first
version scanned ~120KB of the sub-product's prose for the counterparty's name and
matched only on `PARENT_CONTEXT.md`, a file the harness had written into that folder
containing the parent's dependency titles verbatim: the check was reading back its own
output and could not fail.

Here the same information is a **registry** in the one workspace: `plan/contracts/<id>.yml`
naming a provider scope and its consumers. Nothing is inferred from prose.

Parsed without a yaml dependency, on purpose. These checks gate work - a missing
optional package must not silently turn them into "no findings".
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import scope_paths as sp


CONTRACTS_DIR = "plan/contracts"
LOCK_FILE = ".loop/contract-locks.json"

DRAFT = "draft"
AGREED = "agreed"
IMPLEMENTED = "implemented"
DEPRECATED = "deprecated"
STATUSES = (DRAFT, AGREED, IMPLEMENTED, DEPRECATED)

#: Statuses at which the surface is a promise other scopes are building against.
FROZEN = (AGREED, IMPLEMENTED)

ACTIVE_TASK_STATUSES = {"in_progress", "in-progress", "active", "doing"}


def contracts_dir(workspace: Path) -> Path:
    return Path(workspace) / "plan" / "contracts"


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------


@dataclass
class Consumer:
    scope: str
    status: str = "planned"  # planned | agreed | declined
    rationale: str = ""


@dataclass
class Contract:
    id: str
    path: Path
    provider: str = ""
    status: str = DRAFT
    surface: str = ""
    supersedes: str | None = None
    consumers: list[Consumer] = field(default_factory=list)

    @property
    def frozen(self) -> bool:
        return self.status in FROZEN

    def consumer(self, scope: str) -> Consumer | None:
        for item in self.consumers:
            if item.scope == scope:
                return item
        return None

    def to_yaml(self) -> str:
        lines = [f"id: {self.id}", f"provider: {self.provider}", f"status: {self.status}"]
        if self.surface:
            lines.append(f'surface: "{self.surface}"')
        if self.supersedes:
            lines.append(f"supersedes: {self.supersedes}")
        lines.append("consumers:")
        if not self.consumers:
            lines[-1] = "consumers: []"
        for item in self.consumers:
            lines.append(f"  - scope: {item.scope}")
            lines.append(f"    status: {item.status}")
            if item.rationale:
                lines.append(f'    rationale: "{item.rationale}"')
        return "\n".join(lines) + "\n"


_SCALAR = re.compile(r"^(?P<key>[a-z_]+):\s*(?P<value>.*)$")
_ITEM = re.compile(r"^\s*-\s*(?P<key>[a-z_]+):\s*(?P<value>.*)$")
_SUBFIELD = re.compile(r"^\s+(?P<key>[a-z_]+):\s*(?P<value>.*)$")


def _clean(value: str) -> str:
    return value.strip().strip('"').strip("'")


def parse_contract(path: Path) -> Contract | None:
    """Read one contract file. Shallow by design: scalars plus one list of mappings."""
    path = Path(path)
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return None

    contract = Contract(id=path.stem, path=path)
    in_consumers = False
    current: Consumer | None = None

    for raw in lines:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        item = _ITEM.match(raw)
        if item and in_consumers:
            current = Consumer(scope=_clean(item.group("value")))
            if item.group("key") != "scope":
                setattr(current, item.group("key"), _clean(item.group("value")))
                current.scope = ""
            contract.consumers.append(current)
            continue

        if in_consumers and current is not None:
            sub = _SUBFIELD.match(raw)
            if sub and not raw.lstrip().startswith("-"):
                key, value = sub.group("key"), _clean(sub.group("value"))
                if key in {"scope", "status", "rationale"}:
                    setattr(current, key, value)
                    continue

        scalar = _SCALAR.match(raw)
        if not scalar:
            continue
        key, value = scalar.group("key"), _clean(scalar.group("value"))
        if key == "consumers":
            in_consumers = True
            current = None
            continue
        in_consumers = False
        if key == "id" and value:
            contract.id = value
        elif key == "provider":
            contract.provider = value
        elif key == "status":
            contract.status = value or DRAFT
        elif key == "surface":
            contract.surface = value
        elif key == "supersedes":
            contract.supersedes = value or None

    contract.consumers = [c for c in contract.consumers if c.scope]
    return contract


def list_contracts(workspace: Path) -> list[Contract]:
    root = contracts_dir(workspace)
    if not root.is_dir():
        return []
    out: list[Contract] = []
    for path in sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml")):
        parsed = parse_contract(path)
        if parsed is not None:
            out.append(parsed)
    return out


def write_contract(workspace: Path, contract: Contract) -> Path:
    root = contracts_dir(workspace)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{contract.id}.yml"
    path.write_text(contract.to_yaml(), encoding="utf-8")
    contract.path = path
    return path


# ---------------------------------------------------------------------------
# the surface lock - what makes a breaking change detectable
# ---------------------------------------------------------------------------


def _lock_path(workspace: Path) -> Path:
    return Path(workspace) / ".loop" / "contract-locks.json"


def read_locks(workspace: Path) -> dict:
    path = _lock_path(workspace)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def lock_surfaces(workspace: Path, contracts: list[Contract] | None = None) -> dict:
    """Record the surface of every frozen contract, so a later edit is visible.

    Without this a breaking change is undetectable from the files alone: the edited
    surface simply *is* the surface. The lock is the only history the check needs,
    and it is written the moment a contract reaches `agreed`.
    """
    contracts = contracts if contracts is not None else list_contracts(workspace)
    locks = read_locks(workspace)
    for contract in contracts:
        if contract.frozen and contract.id not in locks:
            locks[contract.id] = {"surface": contract.surface, "status": contract.status}
    path = _lock_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(locks, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return locks


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    kind: str
    level: str  # error | warn | info
    scope: str
    message: str
    fix: str = ""

    def line(self) -> str:
        return f"[{self.level}] {self.kind} ({self.scope}): {self.message}"


def check(workspace: Path, *, tasks: list[dict] | None = None) -> list[Finding]:
    """Every contract finding, deterministically, from declarations only."""
    workspace = Path(workspace)
    scopes = sp.list_scopes(workspace)
    by_slug = {s.slug: s for s in scopes}
    contracts = list_contracts(workspace)
    by_id = {c.id: c for c in contracts}
    locks = read_locks(workspace)

    if tasks is None:
        import scope_state

        tasks = scope_state.load_tasks(workspace)

    findings: list[Finding] = []

    provided: dict[str, str] = {}
    for contract in contracts:
        if contract.provider:
            provided[contract.id] = contract.provider
    for scope in scopes:
        for contract_id in scope.provides:
            provided.setdefault(contract_id, scope.slug)

    # 1. consumed but nobody provides it -------------------------------------
    # Checked from both ends. The consumer side catches a scope depending on
    # something no file declares; this side catches a contract file that exists but
    # names no reachable provider - the shape a seeded-from-integrations draft has,
    # and one no consumer's `consumes` list would reveal on its own.
    reported: set[tuple[str, str]] = set()
    for contract in contracts:
        if contract.provider and contract.provider in by_slug:
            continue
        for consumer in contract.consumers or [Consumer(scope=contract.id)]:
            if consumer.status == "declined":
                continue
            key = (consumer.scope, contract.id)
            reported.add(key)
            findings.append(
                Finding(
                    kind="contract-unprovided",
                    level="error",
                    scope=consumer.scope,
                    message=(
                        f"`{contract.id}` names provider `{contract.provider or '(none)'}`,"
                        " which is not a scope in this workspace"
                    ),
                    fix="set `provider:` to an existing scope slug",
                )
            )

    for scope in scopes:
        for contract_id in scope.consumes:
            contract = by_id.get(contract_id)
            if contract is None:
                findings.append(
                    Finding(
                        kind="contract-unprovided",
                        level="error",
                        scope=scope.slug,
                        message=f"consumes `{contract_id}`, which no contract file declares",
                        fix=f"write plan/contracts/{contract_id}.yml naming its provider scope",
                    )
                )
                continue
            if (not contract.provider or contract.provider not in by_slug) and (
                scope.slug,
                contract_id,
            ) not in reported:
                findings.append(
                    Finding(
                        kind="contract-unprovided",
                        level="error",
                        scope=scope.slug,
                        message=(
                            f"`{contract_id}` names provider `{contract.provider or '(none)'}`,"
                            " which is not a scope in this workspace"
                        ),
                        fix="set `provider:` to an existing scope slug",
                    )
                )

    # 2. a consumer building against a surface that is still a draft ----------
    active_by_scope: dict[str, list[str]] = {}
    for task in tasks:
        if str(task.get("status", "")).lower().replace(" ", "_") in ACTIVE_TASK_STATUSES:
            active_by_scope.setdefault(str(task.get("scope")), []).append(str(task.get("id")))

    for contract in contracts:
        if contract.status != DRAFT:
            continue
        for consumer in contract.consumers:
            if consumer.status == "declined":
                continue
            for task_id in active_by_scope.get(consumer.scope, []):
                findings.append(
                    Finding(
                        kind="contract-unimplemented",
                        level="error",
                        scope=consumer.scope,
                        message=(
                            f"{task_id} is in progress against `{contract.id}`,"
                            f" which is still a draft in `{contract.provider}`"
                        ),
                        fix=f"agree `{contract.id}` with {contract.provider} before building on it",
                    )
                )
                break

    # 3. a frozen surface edited without a new version ------------------------
    for contract in contracts:
        locked = locks.get(contract.id)
        if not locked or not contract.frozen:
            continue
        if locked.get("surface") and locked["surface"] != contract.surface:
            findings.append(
                Finding(
                    kind="contract-breaking",
                    level="error",
                    scope=contract.provider,
                    message=(
                        f"`{contract.id}` is {contract.status} but its surface changed"
                        f" from `{locked['surface']}` to `{contract.surface}`"
                    ),
                    fix="publish a new version id and let consumers migrate, or revert the edit",
                )
            )

    # 4. a consumer still pointing at a superseded version --------------------
    superseded = {c.supersedes: c for c in contracts if c.supersedes}
    for old_id, replacement in superseded.items():
        for scope in scopes:
            if old_id in scope.consumes and replacement.id not in scope.consumes:
                findings.append(
                    Finding(
                        kind="consumer-unnotified",
                        level="warn",
                        scope=scope.slug,
                        message=(
                            f"still consumes `{old_id}`, superseded by `{replacement.id}`"
                        ),
                        fix=f"move to `{replacement.id}` or record why not",
                    )
                )

    # 5. declarations that disagree with each other ---------------------------
    for contract in contracts:
        provider = by_slug.get(contract.provider)
        if provider is not None and contract.id not in provider.provides:
            findings.append(
                Finding(
                    kind="contract-undeclared",
                    level="warn",
                    scope=contract.provider,
                    message=f"provides `{contract.id}` by contract file, but its scope.json does not say so",
                    fix=f'add "{contract.id}" to provides in plan/products/{contract.provider}/scope.json',
                )
            )
        for consumer in contract.consumers:
            if consumer.scope not in by_slug:
                findings.append(
                    Finding(
                        kind="contract-unknown-consumer",
                        level="warn",
                        scope=contract.provider or contract.id,
                        message=f"`{contract.id}` lists consumer `{consumer.scope}`, which is not a scope here",
                        fix="fix the scope slug, or remove the consumer",
                    )
                )

    return findings


def impact_of(workspace: Path, contract_id: str) -> dict:
    """Who is affected by a change to this contract - the input to section 5.1's question.

    A cross-scope change asks the user before it writes, and the question is only
    useful if it names the real impact site: the provider scope, its file, and every
    consumer that is not declined.
    """
    contract = next((c for c in list_contracts(workspace) if c.id == contract_id), None)
    if contract is None:
        return {"contract": contract_id, "known": False, "consumers": [], "provider": None}
    return {
        "contract": contract_id,
        "known": True,
        "provider": contract.provider,
        "provider_plan": f"plan/products/{contract.provider}",
        "contract_file": str(contract.path),
        "status": contract.status,
        "consumers": [c.scope for c in contract.consumers if c.status != "declined"],
    }
