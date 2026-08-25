#!/usr/bin/env python3
"""What this product has actually created in a cloud account, and why.

A deployment plan says what *should* exist. Nothing recorded what *does* - so the
account fills with resources nobody can attribute, and the expensive half of that is
**dev**: a temporary environment is provisioned to try something, the trying ends, and
the resources stay because no one remembers which ones were the experiment.

So every resource this loop creates is written down at the moment it is created, with
the thing it serves and the environment it belongs to. Two questions have to be
answerable without opening a cloud console:

- *What is this resource for?* - attribution, per environment and per product scope.
- *What can I safely delete?* - every `dev` resource whose reason is finished.

Parsed by column name from a markdown table, the same way `PRODUCT_MAP.md` is: it stays
readable and diffable in the plan, and extra columns are safe to add.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path


INVENTORY_FILE = "plan/CLOUD_INVENTORY.md"

ENVIRONMENTS = ("dev", "staging", "prod")

STATUS_ACTIVE = "active"
STATUS_DELETED = "deleted"
STATUS_FAILED = "failed"
STATUSES = (STATUS_ACTIVE, STATUS_DELETED, STATUS_FAILED)

#: Columns the parser understands. Order here is the order written.
COLUMNS = (
    "ID",
    "Env",
    "Provider",
    "Service",
    "Resource",
    "Purpose",
    "Scope",
    "Region",
    "Created",
    "Status",
    "Teardown",
)

HEADER = (
    "# Cloud Inventory\n"
    "\n"
    "Every cloud resource this product created, what it serves, and how to remove it.\n"
    "Written by the deploy phase at the moment a resource is created - never reconstructed\n"
    "from memory afterwards.\n"
    "\n"
    "**`dev` rows are temporary by default.** They are what `teardown` lists first: an\n"
    "environment created to try something, still costing money after the trying ended.\n"
    "\n"
)


def inventory_path(workspace: Path) -> Path:
    return Path(workspace) / "plan" / "CLOUD_INVENTORY.md"


@dataclass
class Resource:
    """One cloud resource, as the inventory table records it."""

    id: str = ""
    env: str = "dev"
    provider: str = ""
    service: str = ""
    resource: str = ""
    purpose: str = ""
    scope: str = ""
    region: str = ""
    created: str = ""
    status: str = STATUS_ACTIVE
    teardown: str = ""

    @property
    def temporary(self) -> bool:
        return self.env == "dev"

    @property
    def live(self) -> bool:
        return self.status == STATUS_ACTIVE

    def age_days(self, today: date | None = None) -> int | None:
        try:
            created = datetime.fromisoformat(self.created).date()
        except (TypeError, ValueError):
            return None
        return ((today or date.today()) - created).days

    def row(self) -> str:
        cells = [
            self.id,
            self.env,
            self.provider,
            self.service,
            f"`{self.resource}`" if self.resource else "",
            self.purpose,
            self.scope or "-",
            self.region,
            self.created,
            self.status,
            self.teardown,
        ]
        return "| " + " | ".join(cells) + " |"


def _clean(cell: str) -> str:
    return cell.strip().strip("`").strip()


def parse(workspace: Path) -> list[Resource]:
    """Read the inventory table. Tolerant: a malformed row is skipped, never fatal."""
    path = inventory_path(workspace)
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []

    header: list[str] | None = None
    out: list[Resource] = []
    for raw in lines:
        line = raw.strip()
        if not line.startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        lowered = [c.lower() for c in cells]
        if header is None:
            if "id" in lowered and "resource" in lowered:
                header = lowered
            continue
        if re.match(r"^[-:\s|]+$", line.strip("|")):
            continue
        row = dict(zip(header, cells))
        if not row.get("id"):
            continue
        out.append(
            Resource(
                id=_clean(row.get("id", "")),
                env=_clean(row.get("env", "")).lower() or "dev",
                provider=_clean(row.get("provider", "")),
                service=_clean(row.get("service", "")),
                resource=_clean(row.get("resource", "")),
                purpose=_clean(row.get("purpose", "")),
                scope=_clean(row.get("scope", "")).lstrip("-") or "",
                region=_clean(row.get("region", "")),
                created=_clean(row.get("created", "")),
                status=_clean(row.get("status", "")).lower() or STATUS_ACTIVE,
                teardown=_clean(row.get("teardown", "")),
            )
        )
    return out


def next_id(existing: list[Resource]) -> str:
    nums = [int(m.group(1)) for r in existing if (m := re.match(r"^R-(\d+)$", r.id))]
    return f"R-{max(nums, default=0) + 1:03d}"


def write(workspace: Path, resources: list[Resource]) -> Path:
    """Rewrite the whole table, grouped by environment.

    Grouping is not cosmetic: the question this file exists to answer - *what in dev can
    I delete* - is asked one environment at a time.
    """
    path = inventory_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [HEADER.rstrip(), ""]
    for env in ENVIRONMENTS + ("other",):
        rows = [r for r in resources if (r.env if r.env in ENVIRONMENTS else "other") == env]
        if not rows:
            continue
        lines.append(f"## {env}")
        lines.append("")
        lines.append("| " + " | ".join(COLUMNS) + " |")
        lines.append("|" + "|".join(["---"] * len(COLUMNS)) + "|")
        for r in sorted(rows, key=lambda x: x.id):
            lines.append(r.row())
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def add(
    workspace: Path,
    *,
    env: str,
    provider: str,
    service: str,
    resource: str,
    purpose: str,
    scope: str = "",
    region: str = "",
    teardown: str = "",
    created: str | None = None,
) -> Resource:
    """Record one created resource. Idempotent on (env, provider, resource).

    Idempotence matters because a deploy is re-run: a retried step must update the row
    it already wrote rather than appending a second one, or the inventory stops being a
    count of what exists.
    """
    existing = parse(workspace)
    for item in existing:
        if (item.env, item.provider.lower(), item.resource) == (env, provider.lower(), resource):
            item.service = service or item.service
            item.purpose = purpose or item.purpose
            item.scope = scope or item.scope
            item.region = region or item.region
            item.teardown = teardown or item.teardown
            item.status = STATUS_ACTIVE
            write(workspace, existing)
            return item

    record = Resource(
        id=next_id(existing),
        env=env,
        provider=provider,
        service=service,
        resource=resource,
        purpose=purpose,
        scope=scope,
        region=region,
        created=created or date.today().isoformat(),
        status=STATUS_ACTIVE,
        teardown=teardown,
    )
    existing.append(record)
    write(workspace, existing)
    return record


def mark(workspace: Path, resource_id: str, status: str) -> Resource | None:
    """Mark a resource deleted or failed. Rows are never removed - a deleted resource
    that existed is part of the account's history, and knowing it was torn down is the
    whole point."""
    if status not in STATUSES:
        raise ValueError(f"status must be one of {', '.join(STATUSES)}")
    resources = parse(workspace)
    for item in resources:
        if item.id.lower() == resource_id.lower():
            item.status = status
            write(workspace, resources)
            return item
    return None


# ---------------------------------------------------------------------------
# the questions this file exists to answer
# ---------------------------------------------------------------------------


@dataclass
class Teardown:
    resource: Resource
    reason: str


def teardown_candidates(workspace: Path, *, stale_days: int = 7, today: date | None = None) -> list[Teardown]:
    """Live `dev` resources that have outlived the reason they were created.

    Deliberately conservative: `prod` and `staging` never appear, and a `dev` row is
    only called stale on its age, which is a fact, rather than on a guess about whether
    anyone still wants it.
    """
    out: list[Teardown] = []
    for item in parse(workspace):
        if not item.live or not item.temporary:
            continue
        age = item.age_days(today)
        if age is None:
            out.append(Teardown(item, "dev resource with no creation date recorded"))
        elif age >= stale_days:
            out.append(Teardown(item, f"dev resource, {age} days old"))
        else:
            out.append(Teardown(item, f"dev resource, {age} days old - still recent"))
    return out


def unattributed(workspace: Path) -> list[Resource]:
    """Live resources with no purpose recorded - the rows that make an account unreadable."""
    return [r for r in parse(workspace) if r.live and not r.purpose]


def by_scope(workspace: Path) -> dict[str, list[Resource]]:
    grouped: dict[str, list[Resource]] = {}
    for item in parse(workspace):
        grouped.setdefault(item.scope or "(platform)", []).append(item)
    return grouped


def summary(workspace: Path) -> dict:
    resources = parse(workspace)
    live = [r for r in resources if r.live]
    return {
        "total": len(resources),
        "live": len(live),
        "by_env": {env: len([r for r in live if r.env == env]) for env in ENVIRONMENTS},
        "unattributed": len(unattributed(workspace)),
        "teardown": len([t for t in teardown_candidates(workspace) if "still recent" not in t.reason]),
    }


# ---------------------------------------------------------------------------
# CLI (internal runtime - agents call this, users never type it)
# ---------------------------------------------------------------------------


def _print_table(resources: list[Resource]) -> None:
    if not resources:
        print("No cloud resources recorded.")
        return
    width = max(len(r.service or r.provider) for r in resources) + 2
    for r in resources:
        flag = "" if r.live else f" [{r.status}]"
        scope = f" ({r.scope})" if r.scope else ""
        print(f"  {r.id}  {r.env:<8} {(r.service or r.provider):<{width}} {r.resource}{scope}{flag}")
        if r.purpose:
            print(f"        {r.purpose}")


def main() -> int:
    from workspace_utils import console_utf8, resolve_workspace

    console_utf8()
    parser = argparse.ArgumentParser(description="Cloud resources this product created.")
    parser.add_argument("--workspace", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="Everything recorded, by environment.")
    p.add_argument("--env", default=None, choices=list(ENVIRONMENTS))

    p = sub.add_parser("add", help="Record a resource that was just created.")
    p.add_argument("--env", required=True, choices=list(ENVIRONMENTS))
    p.add_argument("--provider", required=True)
    p.add_argument("--service", required=True)
    p.add_argument("--resource", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--scope", default="")
    p.add_argument("--region", default="")
    p.add_argument("--teardown", default="", help="The command that removes it.")

    p = sub.add_parser("mark", help="Mark a resource deleted or failed.")
    p.add_argument("id")
    p.add_argument("status", choices=list(STATUSES))

    p = sub.add_parser("teardown", help="Dev resources that have outlived their reason.")
    p.add_argument("--stale-days", type=int, default=7)

    sub.add_parser("orphans", help="Live resources with no purpose recorded.")
    sub.add_parser("summary", help="Counts per environment, and what needs attention.")

    args = parser.parse_args()
    workspace = resolve_workspace(args.workspace)

    if args.command == "list":
        items = parse(workspace)
        if args.env:
            items = [r for r in items if r.env == args.env]
        _print_table(items)
        return 0

    if args.command == "add":
        record = add(
            workspace,
            env=args.env,
            provider=args.provider,
            service=args.service,
            resource=args.resource,
            purpose=args.purpose,
            scope=args.scope,
            region=args.region,
            teardown=args.teardown,
        )
        print(f"Recorded {record.id}: {record.service} `{record.resource}` in {record.env}")
        return 0

    if args.command == "mark":
        record = mark(workspace, args.id, args.status)
        print(f"{record.id} -> {record.status}" if record else f"No resource {args.id}")
        return 0 if record else 1

    if args.command == "teardown":
        rows = [t for t in teardown_candidates(workspace, stale_days=args.stale_days) if "still recent" not in t.reason]
        if not rows:
            print("Nothing in dev has outlived its reason.")
            return 0
        print("Dev resources that look finished:\n")
        for item in rows:
            print(f"  {item.resource.id}  {item.resource.service} `{item.resource.resource}` - {item.reason}")
            print(f"        purpose: {item.resource.purpose or '(none recorded)'}")
            if item.resource.teardown:
                print(f"        remove:  {item.resource.teardown}")
        print("\nAsk the user before removing anything - deletion is irreversible.")
        return 0

    if args.command == "orphans":
        rows = unattributed(workspace)
        if not rows:
            print("Every live resource has a purpose recorded.")
            return 0
        print("Live resources with no purpose - nobody can say what these are for:\n")
        _print_table(rows)
        return 1

    if args.command == "summary":
        data = summary(workspace)
        print(
            f"{data['live']} live resource(s): "
            + ", ".join(f"{n} {env}" for env, n in data["by_env"].items() if n)
        )
        if data["unattributed"]:
            print(f"  {data['unattributed']} with no purpose recorded")
        if data["teardown"]:
            print(f"  {data['teardown']} dev resource(s) look finished")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
