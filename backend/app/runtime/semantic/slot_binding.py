"""Slot binding adapter for collect semantic pre-pass."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage

from app.graph.semantic.frame import SemanticFrame
from app.graph.semantic.slot_tracker import (
    apply_slot_updates,
    bind_utterance_to_slots,
    compute_missing_slots,
    last_human_text,
)

__all__ = [
    "apply_slot_updates",
    "bind_utterance_to_slots",
    "compute_missing_slots",
    "last_human_text",
]


def bind_utterance(
    normalized_text: str,
    trip_spec: dict[str, Any],
    state: dict[str, Any],
    *,
    corrections: list[Any] | None = None,
    dialogue_text: str = "",
) -> SemanticFrame:
    """Bind normalized text to trip-spec slots."""
    return bind_utterance_to_slots(
        normalized_text,
        trip_spec,
        state,
        corrections=corrections or [],
        dialogue_text=dialogue_text,
    )


def apply_slot_bindings(
    trip_spec: dict[str, Any],
    state: dict[str, Any],
    frame: SemanticFrame,
) -> dict[str, Any]:
    """Apply semantic frame slot updates to trip_spec."""
    return apply_slot_updates(trip_spec, frame, state)


def dialogue_text_from_messages(messages: list[BaseMessage]) -> str:
    """Build a compact dialogue string from user messages."""
    from langchain_core.messages import HumanMessage

    parts: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            parts.append(content.strip())
    return " ".join(part for part in parts if part)
