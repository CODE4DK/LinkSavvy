"""Step 7 of the gateway pipeline: a deterministic check on what the model
actually said, independent of what the prompt asked for.

This exists because a prompt injection that survives sanitization, or a
model that simply drifts, could otherwise produce output that tells a
user to automate LinkedIn (violating CLAUDE.md's hard compliance rule),
impersonate someone, or fabricate credentials/experience/metrics on their
behalf. It's pattern-based rather than a second model call: deterministic,
free, and auditable.
"""

from __future__ import annotations

import re
from typing import Literal

from app.errors import ApiError, ErrorCode

PolicyCategory = Literal["automation", "impersonation", "fabrication"]

_AUTOMATION_PATTERNS = [
    re.compile(r"auto[\s-]?(like|comment|connect|message|post|follow)", re.IGNORECASE),
    re.compile(
        r"\b(use|write|run)\s+(a|an)\s+(bot|script|selenium|puppeteer|playwright|macro)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bautomatically\s+(like|comment|connect|message|post|follow|apply)\b", re.IGNORECASE
    ),
    re.compile(r"\bheadless browser\b.{0,40}\blinkedin\b", re.IGNORECASE | re.DOTALL),
]

_IMPERSONATION_PATTERNS = [
    re.compile(r"\bpretend (to be|you are)\b", re.IGNORECASE),
    re.compile(r"\bpose as\b", re.IGNORECASE),
    re.compile(r"\bimpersonat\w*\b", re.IGNORECASE),
    re.compile(r"\bclaim(ing)? to be someone else\b", re.IGNORECASE),
]

_FABRICATION_PATTERNS = [
    re.compile(
        r"\bfake\s+(a\s+|an\s+)?(certificat\w*|degree|credential|experience)\b", re.IGNORECASE
    ),
    re.compile(r"\bmake up\s+(a|an|some)?\s*(metric|number|statistic|result)s?\b", re.IGNORECASE),
    re.compile(
        r"\binvent\s+(a|an)\s+(job title|employer|company|role|achievement)\b", re.IGNORECASE
    ),
    re.compile(r"\bfabricat\w*\b", re.IGNORECASE),
    re.compile(r"\bexaggerate\s+your\s+(results|metrics|numbers|achievements)\b", re.IGNORECASE),
]

_PATTERNS_BY_CATEGORY: dict[PolicyCategory, list[re.Pattern[str]]] = {
    "automation": _AUTOMATION_PATTERNS,
    "impersonation": _IMPERSONATION_PATTERNS,
    "fabrication": _FABRICATION_PATTERNS,
}


class OutputPolicyViolation(ApiError):
    def __init__(self, *, category: PolicyCategory, matched: str) -> None:
        self.category = category
        self.matched = matched
        super().__init__(
            ErrorCode.AI_POLICY_BLOCKED,
            f"generated output was blocked by the {category} policy",
            details={"category": category},
        )


def check_output_policy(text: str) -> None:
    """Raises `OutputPolicyViolation` on the first match. Never logs or
    echoes back the matched span in a way that would leak user content —
    only the category and the (fixed, non-secret) pattern name."""
    for category, patterns in _PATTERNS_BY_CATEGORY.items():
        for pattern in patterns:
            if pattern.search(text):
                raise OutputPolicyViolation(category=category, matched=pattern.pattern)
