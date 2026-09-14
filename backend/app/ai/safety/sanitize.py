"""Step 2 of the gateway pipeline: make user-supplied context safe to
hand to a template.

Three things happen to every value, in order: length capping (a runaway
field can't blow the token budget or bury a real instruction under noise),
neutralising known prompt-injection shapes (fake role turns, "ignore
previous instructions", hidden/invisible-Unicode directives), and wrapping
the result in a clearly delimited block. The delimiters matter as much as
the neutralisation: a template only ever does `{{ field }}` (see
app/ai/prompts/render.py's restricted environment), so the model sees
"here is a fenced block of untrusted user content" rather than text that
blends into the instructions around it.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

DEFAULT_MAX_FIELD_LENGTH = 8000

_REDACTED = "[redacted: possible prompt injection]"

# Fake role turns and system-prompt-shaped lines a user might paste in to
# try to reassign the model's instructions mid-context.
_FAKE_TURN_RE = re.compile(r"^\s*(system|assistant|developer)\s*:\s*", re.IGNORECASE | re.MULTILINE)
_INSTRUCTION_OVERRIDE_RE = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+|any\s+)?"
    r"(the\s+|your\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?)",
    re.IGNORECASE,
)
_ROLE_REASSIGNMENT_RE = re.compile(
    r"\byou\s+are\s+now\s+(a|an|the)\b|\bact\s+as\s+(a|an|the)\b.{0,40}\binstead\b",
    re.IGNORECASE,
)
_FAKE_SPECIAL_TOKEN_RE = re.compile(r"<\|.*?\|>|\[/?(?:system|inst|s)\]", re.IGNORECASE)
_CODE_FENCE_DIRECTIVE_RE = re.compile(r"```\s*(system|prompt)\b", re.IGNORECASE)

_INJECTION_PATTERNS = [
    _FAKE_TURN_RE,
    _INSTRUCTION_OVERRIDE_RE,
    _ROLE_REASSIGNMENT_RE,
    _FAKE_SPECIAL_TOKEN_RE,
    _CODE_FENCE_DIRECTIVE_RE,
]

# Zero-width and bidi-control characters are the usual vector for
# "markdown-hidden directives" (text invisible when rendered but present
# in the raw string the model reads), plus HTML/markdown comments. Written
# as explicit \uXXXX escapes, never literal characters, so the source file
# never carries invisible bytes that a diff or editor can't show.
_HIDDEN_CHARS_RE = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def _neutralize(text: str) -> str:
    cleaned = _HTML_COMMENT_RE.sub(_REDACTED, text)
    cleaned = _HIDDEN_CHARS_RE.sub("", cleaned)
    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub(_REDACTED, cleaned)
    return cleaned


def _delimiter_tag(field_name: str) -> str:
    return re.sub(r"[^A-Z0-9_]", "_", field_name.upper())


def sanitize_field(
    value: Any, *, field_name: str, max_length: int = DEFAULT_MAX_FIELD_LENGTH
) -> str:
    """Sanitizes one context value and wraps it in a delimited block. The
    prompt template references it as a plain `{{ field_name }}` — the
    delimiters are already part of the returned string, not something the
    template has to add itself."""
    text = value if isinstance(value, str) else str(value)
    truncated = text[:max_length]
    neutralized = _neutralize(truncated)
    tag = _delimiter_tag(field_name)
    return f"<<<{tag}_START>>>\n{neutralized}\n<<<{tag}_END>>>"


def sanitize_context(
    context: Mapping[str, Any], *, max_length: int = DEFAULT_MAX_FIELD_LENGTH
) -> dict[str, str]:
    return {
        key: sanitize_field(value, field_name=key, max_length=max_length)
        for key, value in context.items()
    }
