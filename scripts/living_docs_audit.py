#!/usr/bin/env python3
"""Living-docs drift detection.

Walks a workspace for the doc surface (CLAUDE.md, AGENTS.md, docs/adr/*.md,
docs/*.md, README.md, docs/CONTRIBUTING.md, docs/api/*.md, docs/runbook/*.md) and
runs the deterministic drift checks described in
`skills/living-docs-governance/SKILL.md`. Emits a Markdown drift report and
(optionally) high-severity findings as TODO entries for the chain to file.

This is the runtime half of the living-docs-governance skill.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Finding:
    doc: str
    line: int
    category: str
    severity: str
    expected: str
    actual: str
    remediation: str

    def to_dict(self) -> dict:
        return {
            "doc": self.doc,
            "line": self.line,
            "category": self.category,
            "severity": self.severity,
            "expected": self.expected,
            "actual": self.actual,
            "remediation": self.remediation,
        }


@dataclass
class DriftReport:
    findings: list[Finding] = field(default_factory=list)
    docs_scanned: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)
        if finding.severity == "high":
            self.high_count += 1
        elif finding.severity == "medium":
            self.medium_count += 1
        else:
            self.low_count += 1

    def to_dict(self) -> dict:
        return {
            "docs_scanned": self.docs_scanned,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "findings": [f.to_dict() for f in self.findings],
        }


DOC_SURFACE = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "docs/CONTRIBUTING.md",
    "docs/INSTALL.md",
    "docs/adr",
    "docs",
    "docs/api",
    "docs/runbook",
]

# Common English words that match the slash-command regex but are not commands.
# Anything in this set is skipped by the outdated-command check.
COMMAND_STOP_WORDS = {
    "and", "or", "is", "by", "for", "in", "of", "to", "the", "this", "you",
    "your", "we", "run", "use", "see", "not", "but", "from", "with", "at",
    "as", "if", "be", "a", "an", "i", "they", "he", "she", "it", "are", "was",
    "were", "have", "has", "do", "does", "did", "can", "could", "would",
    "should", "may", "might", "must", "shall", "will", "just", "only",
    "also", "then", "than", "so", "because", "while", "when", "where",
    "what", "which", "who", "whom", "whose", "that", "these", "those",
    "skill", "skills", "command", "commands", "loop", "agent", "product",
    "products", "code", "test", "tests", "lint", "commit", "deploy",
    "build", "data", "memory", "files", "docs", "state", "phase", "phases",
    "step", "steps", "plan", "plans", "task", "tasks", "feature", "features",
    "name", "names", "file", "files", "all", "each", "every", "any", "some",
    "no", "yes", "true", "false", "else", "on", "up", "out", "off", "down",
    "back", "over", "under", "again", "still", "yet", "ever", "never",
    "always", "often", "sometimes", "here", "there", "now", "then", "today",
    "tomorrow", "yesterday", "compact", "review", "release", "ship", "merge",
    "open", "save", "load", "edit", "read", "write", "draft", "final",
}

# The regex below matches a slash command followed by whitespace, end-of-string,
# or terminal punctuation. The pattern avoids matching URL paths or file paths
# like /data/ or /tmp/foo.
BARE_COMMAND_TERMINATORS = (
    r"\s"        # whitespace
    r"|\Z"        # end of string
    r"|,"         # comma
    r"|;"         # semicolon
    r"|\."        # period
    r"|:"         # colon
    r"|\)"        # close paren
    r"|]"         # close bracket
    r"|\??"       # question mark
    r"|\\"        # backslash
    r"|`"         # backtick
    r"|'"         # single quote
    r"|\""        # double quote
)


def _walk_doc_surface(workspace: Path) -> list[Path]:
    files: list[Path] = []
    for surface in DOC_SURFACE:
        path = workspace / surface
        if not path.exists():
            continue
        if path.is_file() and path.suffix == ".md":
            files.append(path)
        elif path.is_dir():
            for p in path.rglob("*.md"):
                files.append(p)
    return sorted(set(files))


def _check_outdated_command(text: str, workspace: Path) -> Iterable[Finding]:
    """Detect doc references to slash commands that do not exist in the LE
    app's commands/ or the workspace's scripts/.

    Conservative: matches `` `/cmd` `` (backtick-quoted) or `/cmd` at the
    start of a token (preceded by start-of-line, whitespace, or sentence
    punctuation). URL paths like `plan/foo.md` and inline references like
    `Product/architecture decisions` are skipped.
    """
    skill_commands = {p.stem for p in (ROOT / "commands").glob("*.md")}
    # Pattern 1: backtick-quoted /cmd - definitely a command.
    # Pattern 2: /cmd at the start of a token. The character before the
    # slash must be start-of-string, whitespace, or one of `:;,()[]`
    # (sentence or list punctuation). This excludes "Product/architecture"
    # (preceded by a letter) and "/data/foo" (preceded by a slash).
    patterns = [
        r"`/([a-z][a-z0-9-]+)`",
        r"(?:^|[\s:;,()\[\]])/([a-z][a-z0-9-]+)(?=$|[\s,;\)])",
    ]
    seen: set[tuple[int, str]] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            cmd = match.group(1)
            if cmd in COMMAND_STOP_WORDS:
                continue
            if len(cmd) < 3:
                continue
            if cmd in skill_commands:
                continue
            key = (match.start(), cmd)
            if key in seen:
                continue
            seen.add(key)
            line_no = text[: match.start()].count("\n") + 1
            yield Finding(
                doc="<inline>",
                line=line_no,
                category="outdated-command",
                severity="high",
                expected=f"command /{cmd} exists in commands/ or workspace scripts/",
                actual=f"command /{cmd} is referenced but does not exist",
                remediation=f"Either create commands/{cmd}.md in the LE app, or update the doc to remove the /{cmd} reference",
            )


def _check_dead_link(text: str, workspace: Path) -> Iterable[Finding]:
    """Detect markdown links to local paths that do not exist."""
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        path = match.group(2)
        if "://" in path:
            continue
        if path.startswith("#"):
            continue
        clean = path.split("#", 1)[0].split("?", 1)[0]
        if not clean:
            continue
        target = workspace / clean
        if not target.exists():
            line_no = text[: match.start()].count("\n") + 1
            yield Finding(
                doc="<inline>",
                line=line_no,
                category="dead-link",
                severity="low",
                expected=f"path {clean} exists",
                actual=f"link to {clean} points at non-existent file",
                remediation=f"Either create {clean} or fix the link",
            )


def _check_wrong_version_pin(text: str) -> Iterable[Finding]:
    """Heuristic: flag a `version: X` in a fenced code block where X is older
    than the current year minus 3."""
    year = time.gmtime().tm_year
    cutoff = year - 3
    for match in re.finditer(
        r"(?:^|\s)version\s*[:=]\s*[\"']?(\d{4}|\d+\.\d+(?:\.\d+)?)", text, re.MULTILINE
    ):
        version = match.group(1)
        if version.isdigit() and len(version) == 4 and int(version) < cutoff:
            line_no = text[: match.start()].count("\n") + 1
            yield Finding(
                doc="<inline>",
                line=line_no,
                category="wrong-version-pin",
                severity="medium",
                expected=f"version {year}+ or a non-year-shaped version",
                actual=f"version pin is {version} (more than 3 years old)",
                remediation="Update the version pin to current",
            )


def _check_stale_generated_table(text: str) -> Iterable[Finding]:
    """Heuristic: a doc that contains 'GENERATED' or 'auto-generated' and a
    date is stale if the date is more than 30 days old."""
    pattern = re.compile(
        r"(generated|auto-?generated)[: ]+\s*(\d{4}-\d{2}-\d{2})",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        date_str = match.group(2)
        try:
            ts = time.strptime(date_str, "%Y-%m-%d")
            age_days = (time.time() - time.mktime(ts)) / 86400
        except ValueError:
            continue
        if age_days > 30:
            line_no = text[: match.start()].count("\n") + 1
            yield Finding(
                doc="<inline>",
                line=line_no,
                category="stale-generated-table",
                severity="high",
                expected="regenerated within 30 days",
                actual=f"marked generated {date_str} ({int(age_days)} days old)",
                remediation="Re-run the generator and commit the new output",
            )


def audit(workspace: Path) -> DriftReport:
    report = DriftReport()
    files = _walk_doc_surface(workspace)
    report.docs_scanned = len(files)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for finding in _check_outdated_command(text, workspace):
            finding.doc = str(path.relative_to(workspace)).replace("\\", "/")
            report.add(finding)
        for finding in _check_dead_link(text, workspace):
            finding.doc = str(path.relative_to(workspace)).replace("\\", "/")
            report.add(finding)
        for finding in _check_wrong_version_pin(text):
            finding.doc = str(path.relative_to(workspace)).replace("\\", "/")
            report.add(finding)
        for finding in _check_stale_generated_table(text):
            finding.doc = str(path.relative_to(workspace)).replace("\\", "/")
            report.add(finding)
    return report


def render_markdown(report: DriftReport, *, workspace: Path) -> str:
    lines = [
        "# Living-Docs Drift Report",
        "",
        f"Workspace: `{workspace}`",
        f"Docs scanned: **{report.docs_scanned}**",
        f"Findings: **{len(report.findings)}** (high: {report.high_count}, medium: {report.medium_count}, low: {report.low_count})",
        "",
    ]
    if not report.findings:
        lines.append("No drift detected.")
    else:
        lines.append("| Doc | Line | Category | Severity | Remediation |")
        lines.append("|---|---|---|---|---|")
        for finding in report.findings:
            lines.append(
                f"| `{finding.doc}` | {finding.line} | {finding.category} | {finding.severity} | {finding.remediation} |"
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path, default=None, help="Write the report to this file")
    args = parser.parse_args(argv)
    workspace = args.workspace.resolve()
    report = audit(workspace)
    if args.json:
        output = json.dumps(report.to_dict(), indent=2)
    else:
        output = render_markdown(report, workspace=workspace)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output)
    return 0 if not report.findings else 1


if __name__ == "__main__":
    raise SystemExit(main())