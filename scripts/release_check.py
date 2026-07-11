#!/usr/bin/env python3
"""Run a focused pre-production release readiness check."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from source_tree_scan import scan_source_tree
from workspace_utils import ROOT, resolve_workspace


def read_text(path: Path, max_chars: int = 4000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n_...truncated_"


def extract_line(text: str, prefix: str, default: str = "TBD") -> str:
    for line in text.splitlines():
        if line.strip().lower().startswith(prefix.lower()):
            return line.split(":", 1)[-1].strip().strip("* ")
    return default


def bullet(items: list[str]) -> str:
    if not items:
        return "- None."
    return "\n".join(f"- {item}" for item in items)


def load_template() -> str:
    return (ROOT / "templates" / "release_check.template.md").read_text(encoding="utf-8")


def render(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def analyze(workspace: Path) -> str:
    from memory_paths import main_plan_file

    main_plan = read_text(main_plan_file(workspace))
    gates = read_text(workspace / "GATES.yml")
    prod_gap = read_text(workspace / "plan" / "PROD-GAP.md")
    test_plan = read_text(workspace / "docs" / "TEST_PLAN.md")
    current_state = read_text(workspace / "CURRENT_STATE.md")

    findings = scan_source_tree(workspace)

    blockers: list[str] = []
    warnings: list[str] = []
    passed: list[str] = []

    if "Status: **UNINITIALIZED**" in main_plan:
        blockers.append("Product plan is uninitialized.")
    else:
        passed.append("Product plan is initialized.")

    if test_plan:
        passed.append("`docs/TEST_PLAN.md` exists.")
    else:
        warnings.append("Missing `docs/TEST_PLAN.md`.")

    if findings.source_root and findings.scanned_files:
        passed.append(f"Scanned {findings.scanned_files} source files under `{findings.source_root}`.")
    else:
        warnings.append("No product source tree detected for release checks.")

    blockers.extend(findings.p0)
    warnings.extend(findings.p1)
    warnings.extend(findings.p2)

    if "G-RELEASE-01" in gates and "pass" not in gates.lower():
        blockers.append("Release gate `G-RELEASE-01` is not marked passed.")
    if "G-SECURITY-01" in gates and "pass" not in gates.lower():
        warnings.append("Security gate `G-SECURITY-01` is not marked passed.")

    if "## P0 Gaps" in prod_gap and "- None" not in prod_gap:
        warnings.append("Review P0 gaps in `plan/PROD-GAP.md` before release.")

    for label, items in (
        ("Tests", [item for item in findings.technical if "test" in item.lower()]),
        ("CI", [item for item in findings.release if "CI" in item or "workflow" in item.lower()]),
        ("Env", [item for item in findings.technical if "env" in item.lower()]),
        ("Secrets", findings.security),
        ("Docs", [item for item in findings.technical if "README" in item]),
        ("Deploy", [item for item in findings.release if "container" in item.lower() or "deploy" in item.lower()]),
        ("Rollback", [item for item in findings.release if "rollback" in item.lower()]),
        ("Monitoring", [item for item in findings.release if "monitor" in item.lower()]),
    ):
        if not items and label in {"Tests", "CI", "Env", "Docs"}:
            warnings.append(f"{label} check needs attention.")
        elif items:
            warnings.extend(items)

    ready = not blockers
    status = "READY" if ready and not warnings else "NOT READY" if blockers else "READY WITH WARNINGS"

    return render(
        load_template(),
        {
            "UPDATED_DATE": date.today().isoformat(),
            "PRODUCT_NAME": extract_line(main_plan, "- **Name", "Uninitialized"),
            "PHASE": extract_line(current_state, "**Phase", "Unknown"),
            "RELEASE_STATUS": status,
            "BLOCKERS": bullet(blockers),
            "WARNINGS": bullet(warnings),
            "PASSED": bullet(passed),
            "PROD_GAP_EXCERPT": prod_gap or "_No plan/PROD-GAP.md yet. Run `/prod-gap`._",
            "NEXT_COMMAND": "/prod-gap" if blockers else "/product-develop",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write RELEASE_CHECK.md for a product workspace.")
    parser.add_argument("--workspace", default=None, help="Product workspace path.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    output = workspace / "RELEASE_CHECK.md"
    output.write_text(analyze(workspace), encoding="utf-8")

    log_path = workspace / ".ai" / "SESSION_LOG.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            "\n"
            f"## {date.today().isoformat()} - Release check\n\n"
            f"- Updated `{output.name}`.\n"
        )

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
