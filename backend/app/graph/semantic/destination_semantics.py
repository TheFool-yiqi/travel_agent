"""目的地槽位语义处理（兼容层，委托 semantic_pipeline）。"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage

from app.graph.semantic.semantic_pipeline import apply_semantic_frame, build_semantic_frame


def apply_destination_semantics(
    merged_fields: dict[str, Any],
    messages: list[BaseMessage],
    state: dict[str, Any],
) -> tuple[dict[str, Any], str | None, dict[str, Any] | None]:
    frame = build_semantic_frame(messages, merged_fields, state)
    return apply_semantic_frame(merged_fields, state, frame)
