"""Deterministic guardrails for outreach content -- Engagement Hub
tools generate messages meant for a specific person, never a template
sendable unchanged to a hundred people. These checks run *after* the
AI generates output (wired in as each tool's `ToolDefinition.
postprocess`, see app/tools/definition.py) and annotate the result
with flags the frontend renders as warnings; they never silently
rewrite or block a message themselves (the hard character limits are
enforced separately, by the AI's own output schema -- see
`app/ai/gateway.py`'s JSON Schema validation, which already rejects
rather than truncates an over-length field).
"""

from __future__ import annotations

import re
from typing import Any

# Hard limits -- also declared as `Field(max_length=...)` on each
# outreach tool's own output schema, so the gateway's existing JSON
# Schema validation rejects (never truncates) an over-length message.
# Single source of truth for both the backend constraint and anything
# the frontend wants to show as a live character count.
CONNECTION_NOTE_MAX_CHARS = 300
INMAIL_SUBJECT_MAX_CHARS = 200
COMMENT_MAX_CHARS = 1250

# A soft, honest nudge -- never a block. Counted across every tool
# flagged `counts_as_outreach=True` (see app/tools/service.py), not
# per individual tool, since the concern is outreach volume overall.
OUTREACH_DAILY_SOFT_CAP = 15

_STOPWORDS = {
    "about",
    "after",
    "again",
    "along",
    "another",
    "around",
    "because",
    "before",
    "being",
    "below",
    "between",
    "could",
    "during",
    "every",
    "further",
    "having",
    "into",
    "itself",
    "much",
    "myself",
    "other",
    "over",
    "same",
    "should",
    "since",
    "some",
    "such",
    "than",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "under",
    "until",
    "very",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
    "yours",
    "have",
    "does",
    "will",
    "just",
    "like",
    "also",
    "been",
}

_WORD_RE = re.compile(r"[A-Za-z]{4,}")


def _significant_words(text: str) -> set[str]:
    return {w for w in _WORD_RE.findall(text.lower()) if w not in _STOPWORDS}


def personalisation_check(output_text: str, context: dict[str, str]) -> list[str]:
    """Flags a message that reads as generic -- nothing in it ties back
    to anything specific about the recipient or the shared context the
    tool was given. `context` is whatever free-text the user supplied
    describing the recipient (headline, how they know them, the post
    being replied to, etc.); an empty context means there was nothing
    to check against, so this passes silently rather than penalising a
    tool for input the user didn't provide."""
    context_words: set[str] = set()
    for value in context.values():
        if value:
            context_words |= _significant_words(value)
    if not context_words:
        return []

    output_words = _significant_words(output_text)
    if context_words & output_words:
        return []
    return [
        "This message doesn't reference anything specific about the recipient or "
        "shared context -- as written, it could be sent unchanged to anyone."
    ]


_FLATTERY_PATTERNS = [
    r"\byour (profile|work|content|posts?) (is|are) (amazing|impressive|incredible|outstanding)\b",
    r"\bi(?:'m| am) (?:so |really )?(?:impressed|inspired) by\b",
    r"\blove your (profile|content|work)\b",
    r"\byou'?re (?:so |such an? )?(?:amazing|incredible|inspiring|brilliant)\b",
]
_URGENCY_PATTERNS = [
    r"\bact now\b",
    r"\blimited time\b",
    r"\bdon'?t miss out\b",
    r"\bonly (?:today|this week)\b",
    r"\burgent(?:ly)?\b",
    r"\bhurry\b",
]
_UNDISCLOSED_PITCH_PATTERNS = [
    r"\bcheck out my\b",
    r"\bi'?d love to (?:show|tell) you about my (?:product|service|company|startup)\b",
    r"\bwe'?re offering\b",
]
_FAKE_FAMILIARITY_PATTERNS = [
    r"\bas we discussed\b",
    r"\bas mentioned (?:before|previously)\b",
    r"\bfollowing up on our (?:call|conversation|chat|meeting)\b",
    r"\bgreat (?:talking|chatting|meeting) (?:to|with) you\b",
    r"\bas i mentioned (?:to you )?(?:before|earlier)\b",
]
_MASS_MERGE_PLACEHOLDER_PATTERNS = [
    r"\{\{?\s*(?:first_?name|name|company)\s*\}?\}",
    r"\[\s*(?:first name|name|company)\s*\]",
    r"\bdear (?:sir|madam|sir or madam|connection|valued (?:customer|member))\b",
    r"\bto whom it may concern\b",
]

_SPAM_LABELS: list[tuple[str, list[str]]] = [
    ("flattery opener", _FLATTERY_PATTERNS),
    ("false urgency", _URGENCY_PATTERNS),
    ("undisclosed pitching", _UNDISCLOSED_PITCH_PATTERNS),
    ("fake familiarity", _FAKE_FAMILIARITY_PATTERNS),
    ("mass-merge placeholder", _MASS_MERGE_PLACEHOLDER_PATTERNS),
]


def spam_tone_check(output_text: str) -> list[str]:
    """Flags flattery openers, false urgency, undisclosed pitching, fake
    familiarity, and mass-merge placeholders left in by mistake."""
    lowered = output_text.lower()
    reasons: list[str] = []
    for label, patterns in _SPAM_LABELS:
        if any(re.search(pattern, lowered) for pattern in patterns):
            reasons.append(f"{label} detected")
    return reasons


def soft_cap_warning(runs_today: int) -> str | None:
    if runs_today <= OUTREACH_DAILY_SOFT_CAP:
        return None
    return (
        f"You've generated {runs_today} outreach messages today -- quality beats "
        "volume. Consider slowing down and personalising what you already have "
        "before generating more."
    )


def annotate_variant(
    variant: dict[str, Any], *, text_field: str, context: dict[str, str]
) -> dict[str, Any]:
    """Adds `personalisation_flags` / `spam_flags` to one variant dict,
    read from its own `text_field`. Used as the building block for a
    tool's `postprocess` hook (see each engagement tool definition)."""
    text = variant.get(text_field)
    if not isinstance(text, str):
        return variant
    return {
        **variant,
        "personalisation_flags": personalisation_check(text, context),
        "spam_flags": spam_tone_check(text),
    }


def make_variants_postprocessor(*, text_field: str, context_fields: list[str]) -> Any:
    """Builds a `ToolDefinition.postprocess` for a tool whose output is
    `{"variants": [...]}`, each carrying a `text_field` to check.
    `context_fields` names which of the tool's own *input* fields
    (already present in `raw_input` at postprocess time) describe the
    recipient/shared context to check personalisation against."""

    def _postprocess(output: dict[str, Any], raw_input: dict[str, Any]) -> dict[str, Any]:
        context = {field: str(raw_input.get(field, "")) for field in context_fields}
        variants = output.get("variants")
        if not isinstance(variants, list):
            return output
        return {
            **output,
            "variants": [
                (
                    annotate_variant(v, text_field=text_field, context=context)
                    if isinstance(v, dict)
                    else v
                )
                for v in variants
            ],
        }

    return _postprocess
