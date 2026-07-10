"""Shared source-tree checks for production readiness scripts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".loop-upgrade-backup",
}

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".env",
    ".toml",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]"),
    re.compile(r"(?i)private[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
]

CI_FILES = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "cloudbuild.yaml",
    ".circleci/config.yml",
]

ENV_EXAMPLES = [
    ".env.example",
    ".env.sample",
    "env.example",
    "example.env",
]

PACKAGE_MANIFESTS = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
    "composer.json",
]

LOCK_FILES = [
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "go.sum",
]


@dataclass
class SourceTreeFindings:
    source_root: Path | None = None
    p0: list[str] = field(default_factory=list)
    p1: list[str] = field(default_factory=list)
    p2: list[str] = field(default_factory=list)
    technical: list[str] = field(default_factory=list)
    security: list[str] = field(default_factory=list)
    release: list[str] = field(default_factory=list)
    scanned_files: int = 0
    todo_count: int = 0
    fixme_count: int = 0
    secret_hits: list[str] = field(default_factory=list)


def find_source_root(workspace: Path) -> Path | None:
    candidates: list[Path] = []

    for marker in ("package.json", "pyproject.toml", "go.mod", "Cargo.toml", "src", "app", "apps"):
        for path in [workspace / marker, workspace / "product" / marker]:
            if path.exists():
                candidates.append(path.parent if path.is_file() else path)

    if candidates:
        return sorted(candidates, key=lambda p: len(str(p)))[0]

    if any((workspace / name).exists() for name in ("src", "app", "apps", "lib", "services")):
        return workspace

    return None


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def path_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def has_ci(root: Path) -> bool:
    for item in CI_FILES:
        if path_exists(root, item):
            return True
    return False


def has_env_example(root: Path) -> bool:
    return any(path_exists(root, name) for name in ENV_EXAMPLES)


def has_package_manifest(root: Path) -> bool:
    return any(path_exists(root, name) for name in PACKAGE_MANIFESTS)


def has_lock_file(root: Path) -> bool:
    return any(path_exists(root, name) for name in LOCK_FILES)


def has_test_folder(root: Path) -> bool:
    test_names = ("tests", "test", "__tests__", "spec")
    return any((root / name).exists() for name in test_names)


def has_migration_folder(root: Path) -> bool:
    migration_names = ("migrations", "db/migrations", "alembic", "prisma/migrations")
    return any((root / name).exists() for name in migration_names)


def scan_source_tree(workspace: Path) -> SourceTreeFindings:
    findings = SourceTreeFindings()
    root = find_source_root(workspace)
    findings.source_root = root

    if root is None:
        findings.p2.append("No obvious product source tree detected in workspace.")
        return findings

    rel_root = root
    try:
        rel_display = rel_root.relative_to(workspace).as_posix()
    except ValueError:
        rel_display = rel_root.as_posix()

    if not path_exists(root, "README.md"):
        findings.p1.append(f"Missing `README.md` in source root `{rel_display}`.")
        findings.technical.append("Add a README with setup, run, test, and deploy instructions.")

    if not has_test_folder(root):
        findings.p0.append(f"No test folder found under `{rel_display}`.")
        findings.technical.append("Add tests under `tests/`, `test/`, or `__tests__/`.")

    if not has_ci(root):
        findings.p1.append(f"No CI configuration found under `{rel_display}`.")
        findings.release.append("Add CI workflow for lint, test, and build.")

    if not has_env_example(root):
        findings.p1.append(f"No env example file found under `{rel_display}`.")
        findings.technical.append("Add `.env.example` documenting required environment variables.")

    if has_package_manifest(root) and not has_lock_file(root):
        findings.p1.append(f"Package manifest exists but no lock file found under `{rel_display}`.")
        findings.release.append("Commit a lock file for reproducible builds.")

    if not path_exists(root, "Dockerfile") and not path_exists(root, "docker-compose.yml"):
        findings.p2.append(f"No Dockerfile or docker-compose.yml under `{rel_display}`.")
        findings.release.append("Add container or deploy artifacts if production deploy expects them.")

    if any(path_exists(root, name) for name in PACKAGE_MANIFESTS) and not has_migration_folder(root):
        findings.p2.append(f"No migrations folder detected under `{rel_display}`.")
        findings.technical.append("Add database migrations if the product uses a database.")

    files = iter_text_files(root)
    findings.scanned_files = len(files)

    todo_pattern = re.compile(r"\bTODO\b")
    fixme_pattern = re.compile(r"\bFIXME\b")

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        todo_matches = len(todo_pattern.findall(text))
        fixme_matches = len(fixme_pattern.findall(text))
        findings.todo_count += todo_matches
        findings.fixme_count += fixme_matches

        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.secret_hits.append(rel)
                break

    if findings.todo_count:
        findings.p2.append(f"Found {findings.todo_count} TODO marker(s) in source tree.")
    if findings.fixme_count:
        findings.p1.append(f"Found {findings.fixme_count} FIXME marker(s) in source tree.")

    if findings.secret_hits:
        findings.p0.append("Possible hardcoded secret patterns detected in source files.")
        findings.security.append(
            "Review files with secret-like patterns and move credentials to environment variables or a secret manager."
        )
        for rel in findings.secret_hits[:10]:
            findings.security.append(f"Review `{rel}` for secret-like content.")

    return findings
