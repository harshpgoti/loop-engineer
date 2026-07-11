"""Scan a folder of another tool's arbitrary data/memory files and route each
file into the right Loop Engineer home by content classification.

Rules first, AI second (AGENTS.md rule 4): classification is a deterministic
filename + content-signal scorer - no LLM call. Routing:

  user profile / preferences        -> appended to memories/USER.md
  behavior rules / persona / prompt -> appended to memories/SOUL.md
  project memory / notes / logs     -> appended to memories/MEMORY.md
  procedures / how-tos / runbooks   -> skills/imported/<slug>.md (frontmatter added)
  plans / roadmaps / PRDs / specs   -> plan/imported/<name> (for /plan-loop to absorb)
  secrets / keys                    -> never copied; warned
  binary / huge / unclassifiable    -> skipped or staged in .loop/import-review/

Appends carry an "Imported from <relpath>" marker so re-running the scan is
idempotent - already-imported files are skipped.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

MAX_FILE_BYTES = 1_000_000

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".pdf", ".zip", ".gz", ".tar", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib", ".bin", ".pyc",
    ".db", ".sqlite", ".sqlite3", ".parquet",
    ".mp3", ".mp4", ".wav", ".mov", ".avi",
    ".woff", ".woff2", ".ttf", ".eot",
}

SECRET_FILENAMES = ("secrets", "credentials", ".env")
SECRET_EXTENSIONS = {".pem", ".key", ".pfx", ".p12"}
SECRET_CONTENT = re.compile(
    r"api[_-]?key\s*[=:]\s*\S|sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
)

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".loop-engineer", ".loop"}

# (category, filename hints, content signals). Filename hit = 3 points (once);
# each distinct content signal = 1 point. Highest total >= 2 wins.
CATEGORY_SIGNALS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "user",
        ("user", "profile", "aboutme", "about-me", "about_me", "preferences", "prefs"),
        ("my name is", "call me", "i prefer", "preferences", "timezone", "communication style",
         "risk tolerance", "about me"),
    ),
    (
        "soul",
        ("soul", "rules", "persona", "behavior", "behaviour", "system-prompt", "system_prompt",
         "prompt", "instructions", "tone", "cursorrules", "guidelines", "style-guide"),
        ("you are ", "always respond", "never ", "do not ", "act as", "your role",
         "respond in", "be concise", "when answering"),
    ),
    (
        "memory",
        ("memory", "memories", "notes", "journal", "log", "history", "progress",
         "context", "session", "changelog", "diary", "scratch"),
        ("what we did", "next step", "progress", "yesterday", "today we", "completed",
         "in progress", "follow up", "we learned", "remember that", "so far"),
    ),
    (
        "skill",
        ("skill", "howto", "how-to", "how_to", "runbook", "procedure", "recipe",
         "workflow", "snippet", "cheatsheet"),
        ("## steps", "step 1", "when to use", "usage:", "how to ", "run the following"),
    ),
    (
        "plan",
        ("plan", "roadmap", "prd", "spec", "backlog", "milestones", "requirements",
         "architecture", "design-doc"),
        ("roadmap", "milestone", "mvp", "user stor", "acceptance criteria", "sprint",
         "phase 1", "requirement", "target user", "problem statement", "feature list"),
    ),
)

TIE_BREAK = ("user", "soul", "skill", "plan", "memory")

# Exact-name files the classic importer already handles - skipped when the
# scanner runs alongside it (loop setup --source --scan).
KNOWN_EXACT_NAMES = {"MEMORY.md", "USER.md", "SOUL.md", "AGENTS.md"}


def is_probably_binary(path: Path, raw: bytes) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    return b"\x00" in raw[:4096]


def looks_secret(path: Path, text: str) -> bool:
    name = path.name.lower()
    if any(part in name for part in SECRET_FILENAMES) or path.suffix.lower() in SECRET_EXTENSIONS:
        return True
    return bool(SECRET_CONTENT.search(text))


def has_skill_frontmatter(text: str) -> bool:
    if not text.lstrip().startswith("---"):
        return False
    head = text.lstrip()[3:].split("---", 1)[0]
    return "name:" in head and "description:" in head


def classify(path: Path, text: str) -> tuple[str, str]:
    """Return (category, reason). Categories: user, soul, memory, skill, plan, unknown."""
    if has_skill_frontmatter(text):
        return "skill", "skill frontmatter (name + description)"

    stem = path.stem.lower()
    lower = text.lower()
    scores: dict[str, int] = {}
    reasons: dict[str, list[str]] = {}
    for category, name_hints, content_signals in CATEGORY_SIGNALS:
        score = 0
        why: list[str] = []
        for hint in name_hints:
            if hint in stem:
                score += 3
                why.append(f"filename ~ {hint!r}")
                break
        for signal in content_signals:
            if signal in lower:
                score += 1
                why.append(f"content ~ {signal!r}")
        scores[category] = score
        reasons[category] = why

    best = max(TIE_BREAK, key=lambda c: (scores[c], -TIE_BREAK.index(c)))
    if scores[best] < 2:
        return "unknown", "no strong filename/content signals"
    return best, "; ".join(reasons[best][:3])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "imported"


def _append_with_marker(target: Path, rel: str, content: str) -> bool:
    """Append content under an import marker. Returns False if already imported."""
    marker = f"## Imported from `{rel}`"
    existing = target.read_text(encoding="utf-8", errors="ignore") if target.exists() else ""
    if marker in existing:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    block = f"\n\n{marker} ({date.today().isoformat()})\n\n{content.strip()}\n"
    target.write_text(existing.rstrip() + block if existing else block.lstrip(), encoding="utf-8")
    return True


def _write_skill(workspace: Path, rel: str, path: Path, text: str, dry_run: bool) -> str:
    dest = workspace / "skills" / "imported" / f"{_slugify(path.stem)}.md"
    if dest.exists():
        return f"skipped skill (exists): {rel} -> {dest.relative_to(workspace).as_posix()}"
    if dry_run:
        return f"would import skill: {rel} -> {dest.relative_to(workspace).as_posix()}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not has_skill_frontmatter(text):
        first_line = next((l.strip().lstrip("# ") for l in text.splitlines() if l.strip()), path.stem)
        text = f"---\nname: {_slugify(path.stem)}\ndescription: Imported from {rel} - {first_line[:120]}\n---\n\n{text}"
    dest.write_text(text, encoding="utf-8")
    return f"imported skill: {rel} -> {dest.relative_to(workspace).as_posix()}"


def _stage_copy(workspace: Path, subdir: str, rel: str, path: Path, dry_run: bool) -> str:
    dest = workspace / subdir / path.name
    rel_dest = f"{subdir}/{path.name}"
    if dest.exists():
        return f"skipped (exists): {rel} -> {rel_dest}"
    if dry_run:
        return f"would stage: {rel} -> {rel_dest}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return f"staged: {rel} -> {rel_dest}"


def iter_source_files(source: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def run_scan_import(
    workspace: Path,
    source: Path,
    *,
    dry_run: bool = False,
    exclude_known: bool = False,
) -> list[str]:
    """Classify every file under `source` and route it. Returns summary lines."""
    results: list[str] = []
    memory_targets = {
        "memory": workspace / "memories" / "MEMORY.md",
        "user": workspace / "memories" / "USER.md",
        "soul": workspace / "memories" / "SOUL.md",
    }

    for path in iter_source_files(source):
        rel = path.relative_to(source).as_posix()
        if exclude_known and (path.name in KNOWN_EXACT_NAMES or rel.startswith("skills/")):
            continue

        raw = path.read_bytes()[: MAX_FILE_BYTES + 1]
        if len(raw) > MAX_FILE_BYTES:
            results.append(f"skipped (too large): {rel}")
            continue
        if is_probably_binary(path, raw):
            results.append(f"skipped (binary): {rel}")
            continue
        text = raw.decode("utf-8", errors="ignore")

        if looks_secret(path, text):
            results.append(f"NOT copied (looks like secrets - re-enter keys via `loop model set-key`): {rel}")
            continue

        category, reason = classify(path, text)
        if category in memory_targets:
            target = memory_targets[category]
            rel_target = target.relative_to(workspace).as_posix()
            if dry_run:
                results.append(f"would append: {rel} -> {rel_target} [{category}: {reason}]")
            elif _append_with_marker(target, rel, text):
                results.append(f"appended: {rel} -> {rel_target} [{category}: {reason}]")
            else:
                results.append(f"skipped (already imported): {rel} -> {rel_target}")
        elif category == "skill":
            results.append(_write_skill(workspace, rel, path, text, dry_run) + f" [{reason}]")
        elif category == "plan":
            results.append(
                _stage_copy(workspace, "plan/imported", rel, path, dry_run)
                + f" [plan: {reason} - absorb via /plan-loop]"
            )
        else:
            results.append(
                _stage_copy(workspace, ".loop/import-review", rel, path, dry_run)
                + " [unclassified - review manually]"
            )

    if not results:
        results.append(f"no importable files found under {source}")
    return results
