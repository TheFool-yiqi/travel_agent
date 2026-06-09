"""Semantic frame lifecycle adapter for collect."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage

from app.graph.semantic.frame import SemanticFrame
from app.graph.semantic.semantic_pipeline import (
    apply_semantic_frame,
    build_semantic_frame,
    semantic_frame_to_extraction,
    semantic_rule_extract_from_messages,
)
from app.runtime.semantic.normalizer import normalize_text
from app.runtime.semantic.slot_binding import dialogue_text_from_messages
from app.schemas.travel import RequirementExtraction


class CollectSemanticLayer:
    """Runtime facade over graph semantic rules; graph imports remain unchanged."""

    normalize_text = staticmethod(normalize_text)

    @staticmethod
    def build_frame(
        messages: list[BaseMessage],
        trip_spec: dict[str, Any],
        state: dict[str, Any],
    ) -> SemanticFrame:
        return build_semantic_frame(messages, trip_spec, state)

    @staticmethod
    def apply_frame(
        trip_spec: dict[str, Any],
        state: dict[str, Any],
        frame: SemanticFrame,
    ) -> tuple[dict[str, Any], str | None, dict[str, Any] | None]:
        return apply_semantic_frame(trip_spec, state, frame)

    @staticmethod
    def frame_to_extraction(frame: SemanticFrame) -> RequirementExtraction:
        return semantic_frame_to_extraction(frame)

    @staticmethod
    def rule_extract(
        messages: list[BaseMessage],
        trip_spec: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[RequirementExtraction, SemanticFrame]:
        """Run deterministic semantic extraction before any LLM call."""
        return semantic_rule_extract_from_messages(messages, trip_spec, state)

    @staticmethod
    def dialogue_text(messages: list[BaseMessage]) -> str:
        return dialogue_text_from_messages(messages)
