"""Caps how much of a long conversation's history reaches a prompt.
Deterministic and free rather than a rolling AI-generated summary: an
extra gateway call every single turn just to compress history would cost
real money and latency on every message once a conversation runs long,
which is exactly the growth this function exists to bound. The most
recent turns are kept verbatim (a model reasons far better over the
actual words than over a summary of them); anything older collapses into
one compact digest line naming how many turns and what the earliest ones
were about, so the model still knows a longer history exists without
paying to re-read all of it.
"""

from __future__ import annotations

from app.models.message import Message

_VERBATIM_TURNS = 20
_DIGEST_TOPIC_COUNT = 3
_TOPIC_PREVIEW_LENGTH = 80


def _digest(older: list[Message]) -> str:
    topics = [
        " ".join(message.content.split())[:_TOPIC_PREVIEW_LENGTH]
        for message in older
        if message.role == "user"
    ][:_DIGEST_TOPIC_COUNT]
    topic_text = "; ".join(topics) if topics else "general discussion"
    return f"[{len(older)} earlier message(s) summarized -- earliest topics: {topic_text}]"


def conversation_history_text(
    messages: list[Message], *, assistant_label: str = "Assistant"
) -> str:
    """`assistant_label` lets a distinct surface keep its own voice in the
    transcript it re-sends to itself (the absorbed Growth Coach passes
    "Coach") without duplicating this function's truncation/digest logic."""
    if not messages:
        return "(no messages yet)"

    speaker_labels = {
        "user": "User",
        "assistant": assistant_label,
        "tool": "Tool result",
        "system": "System",
    }
    older, recent = messages[:-_VERBATIM_TURNS], messages[-_VERBATIM_TURNS:]
    lines = [_digest(older)] if older else []
    for message in recent:
        speaker = speaker_labels.get(message.role, message.role)
        lines.append(f"{speaker}: {message.content}")
    return "\n".join(lines)
