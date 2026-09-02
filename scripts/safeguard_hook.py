#!/usr/bin/env python3
"""E7 hook: apply the Prompt Defense Baseline to every tool call.

This is the runtime half of the `/safeguard` skill. It is intended to be
wired into a coding agent's `PreToolUse` hook event (e.g. Claude Code's
`settings.json` `hooks.PreToolUse`).

Inputs: a JSON blob on stdin shaped like
`{"tool_name": "Bash", "tool_input": {"command": "git push"}}`.

Outputs: exit code 0 (allow) or exit code 2 (block) plus a one-line reason
on stderr.

Six checks (the baseline):

1. Role/persona/identity not changed.
2. No secret leakage in the tool input.
3. No unvalidated executable output (URLs, HTML, scripts) in the input.
4. Treat unicode tricks (homoglyphs, RTL overrides, zero-width chars) as
   suspicious.
5. Treat external content as untrusted - tool input that is fetched
   content is wrapped, not echoed.
6. No harmful content - detect known malware / exploit keywords.

The check is conservative: a false positive blocks a legitimate tool call;
a false negative lets a bad call through. The skill's Pre-Report Gate
sits on top of the runtime, so a flagged finding is always surfaced
before the tool runs.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|password|secret|bearer\s+[a-z0-9._-]+|token\s*[:=])"
)
URL_PATTERN = re.compile(r"https?://[^\s]+")
HOMOGLYPH_PATTERN = re.compile(
    r"[\u200B-\u200F\u202A-\u202E\u2066-\u2069\uFEFF]"
    r"|[^\u0000-\u007F]"
)
EXPLOIT_KEYWORDS = (
    "rm -rf /",
    "format c:",
    "del /f /s /q",
    "mkfs.ext4",
    "dd if=/dev/zero",
    ":(){:|:&};:",
)


def _check_role_lock(tool_name: str, tool_input: dict) -> str | None:
    """Check 1: the tool input does not try to override the agent's role."""
    # The system prompt typically owns role; tool input is user content. We
    # catch obvious overrides: "you are now ...", "ignore previous ...",
    # "act as ...". Conservative.
    text = json.dumps(tool_input, default=str).lower()
    for phrase in (
        "ignore previous instructions",
        "disregard the above",
        "you are now",
        "act as a",
        "forget your role",
        "override your instructions",
    ):
        if phrase in text:
            return f"role-override attempt detected ({phrase!r})"
    return None


def _check_secret_leakage(tool_name: str, tool_input: dict) -> str | None:
    """Check 2: the tool input does not contain secrets."""
    text = json.dumps(tool_input, default=str)
    if SECRET_PATTERN.search(text):
        return "possible secret in tool input (api_key/password/secret/bearer/token)"
    return None


def _check_executable_output(tool_name: str, tool_input: dict) -> str | None:
    """Check 3: the tool input does not contain unvalidated executable
    output. We are conservative - URLs are flagged, but the agent is
    expected to validate any URL before use."""
    if tool_name in {"WebFetch", "Bash"}:
        return None  # URLs in fetch / bash are expected
    text = json.dumps(tool_input, default=str)
    urls = URL_PATTERN.findall(text)
    # Allow up to 1 URL in tool input; flag more as a sign of paste.
    if len(urls) > 1:
        return f"multiple URLs in tool input ({len(urls)})"
    return None


def _check_unicode_tricks(tool_name: str, tool_input: dict) -> str | None:
    """Check 4: the tool input does not contain unicode tricks (homoglyphs,
    RTL overrides, zero-width chars)."""
    text = json.dumps(tool_input, default=str)
    for match in HOMOGLYPH_PATTERN.finditer(text):
        # Whitelist common non-ASCII (e.g. accented characters in user
        # input). Only flag zero-width and RTL override characters.
        char = match.group(0)
        if char in "\u200B\u200C\u200D\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2066\u2067\u2068\u2069\uFEFF":
            return f"unicode trick detected ({char!r})"
    return None


def _check_external_untrusted(tool_name: str, tool_input: dict) -> str | None:
    """Check 5: external content is wrapped, not echoed. We don't try to
    detect wrapping; we flag fetched content that is being written
    verbatim to a file (potential untrusted-content injection)."""
    if tool_name in {"WebFetch", "WebSearch"}:
        return None  # reads are not writes
    if tool_name == "Write":
        content = tool_input.get("content", "")
        # If the content is enormous and contains untrusted markers (a URL,
        # an @-mention, a script tag), flag for review.
        if isinstance(content, str) and len(content) > 5000:
            markers = ("<script", "javascript:", "data:text/html")
            for marker in markers:
                if marker in content.lower():
                    return f"Write content contains untrusted-content marker ({marker!r})"
    return None


def _check_harmful(tool_name: str, tool_input: dict) -> str | None:
    """Check 6: the tool input does not contain known harmful commands."""
    text = json.dumps(tool_input, default=str)
    for keyword in EXPLOIT_KEYWORDS:
        if keyword in text:
            return f"harmful-content keyword detected ({keyword!r})"
    return None


CHECKS = (
    _check_role_lock,
    _check_secret_leakage,
    _check_executable_output,
    _check_unicode_tricks,
    _check_external_untrusted,
    _check_harmful,
)


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # If stdin is not JSON, allow (the harness may not send anything).
        return 0

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}

    for check in CHECKS:
        result = check(tool_name, tool_input)
        if result:
            print(f"E7 block ({check.__name__}): {result}", file=sys.stderr)
            return 2  # block
    return 0  # allow


if __name__ == "__main__":
    raise SystemExit(main())