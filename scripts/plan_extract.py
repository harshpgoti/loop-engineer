"""Extract sub-product / agent modules from free-text product ideas."""

from __future__ import annotations

import re


MODULE_SUFFIXES = (
    "agent",
    "portal",
    "dashboard",
    "platform",
    "service",
    "api",
    "app",
    "module",
    "copilot",
    "assistant",
    "bot",
    "engine",
    "hub",
    "workspace",
    "console",
)

AGENT_WORDS = ("agent", "copilot", "assistant", "bot", "automation")
PRODUCT_WORDS = ("portal", "dashboard", "app", "console", "workspace", "ui", "frontend")
SERVICE_WORDS = ("api", "service", "backend", "engine", "pipeline", "worker")


def clean_title(value: str) -> str:
    text = value.strip().strip("-•*").strip()
    text = re.sub(r"^(a|an|the)\s+", "", text, flags=re.I)
    text = re.sub(r"[.:;]+$", "", text).strip()
    return text


def infer_module_type(title: str) -> str:
    lower = title.lower()
    if any(w in lower for w in AGENT_WORDS):
        return "agent"
    if any(w in lower for w in SERVICE_WORDS):
        return "service"
    if any(w in lower for w in PRODUCT_WORDS):
        return "product"
    return "module"


def looks_like_module(title: str) -> bool:
    if len(title) < 4 or len(title) > 120:
        return False
    lower = title.lower()
    if any(w in lower for w in MODULE_SUFFIXES):
        return True
    # Title-case short phrase (Support Triage, Billing)
    words = title.split()
    return 2 <= len(words) <= 8


def strip_leading_fluff(title: str) -> str:
    text = title
    patterns = (
        r"^(?:a|an|the)\s+",
        r"^[\w\s-]{0,40}\bplatform\s+with\s+",
        r"^[\w\s-]{0,40}\bsuite\s+(?:of|with)\s+",
        r"^[\w\s-]{0,40}\becosystem\s+with\s+",
    )
    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.I).strip()
    return text


def extract_module_phrase(chunk: str) -> str | None:
    chunk = clean_title(chunk)
    if not chunk:
        return None
    suffix = r"(agent|portal|dashboard|api|service|app|platform|copilot|assistant|bot|module|engine|hub|console|workspace)"
    # Prefer trailing module phrase: "... patient intake agent"
    end_match = re.search(rf"([\w][\w\s-]{{1,40}}\s+{suffix})\s*$", chunk, flags=re.I)
    if end_match:
        return clean_title(strip_leading_fluff(end_match.group(1)))
    chunk = strip_leading_fluff(chunk)
    if looks_like_module(chunk):
        return chunk
    return None


def extract_modules(text: str) -> list[tuple[str, str]]:
    """Return deduplicated (title, type) modules from idea text."""
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        phrase = extract_module_phrase(raw)
        if not phrase:
            return
        key = phrase.lower()
        if key in seen:
            return
        seen.add(key)
        found.append((phrase, infer_module_type(phrase)))

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for pattern in (
            r"^[-*•]\s+(.+)$",
            r"^\d+[.)]\s+(.+)$",
        ):
            match = re.match(pattern, line)
            if match:
                add(match.group(1))
                break

    if len(found) < 2:
        chunks = re.split(r",|\band\b|\n", text, flags=re.I)
        for chunk in chunks:
            add(chunk)
        if len(found) < 2:
            for match in re.finditer(
                r"([\w][\w\s-]{1,40}\s+(?:agent|portal|dashboard|api|service|app|platform|copilot|assistant|bot|module|engine|hub|console))",
                text,
                flags=re.I,
            ):
                add(match.group(1))

    return found[:12]
