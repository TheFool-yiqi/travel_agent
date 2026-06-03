"""语义理解流水线：规范化 → 槽位绑定 → SemanticFrame。"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from app.graph.semantic.frame import SemanticFrame
from app.graph.semantic.normalizer import normalize_text
from app.graph.semantic.slot_tracker import (
    apply_slot_updates,
    bind_utterance_to_slots,
    last_human_text,
)
from app.schemas.travel import RequirementExtraction


def build_semantic_frame(
    messages: list[BaseMessage],
    fields: dict[str, Any],
    state: dict[str, Any],
) -> SemanticFrame:
    """从最新用户消息构建语义帧。"""
    raw = last_human_text(messages)
    if not raw:
        return SemanticFrame()

    dialogue_parts: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            dialogue_parts.append(content.strip())
    dialogue_text = " ".join(dialogue_parts)

    normalized, corrections = normalize_text(raw)
    return bind_utterance_to_slots(
        normalized,
        fields,
        state,
        corrections=corrections,
        dialogue_text=dialogue_text,
    )


def apply_semantic_frame(
    fields: dict[str, Any],
    state: dict[str, Any],
    frame: SemanticFrame,
) -> tuple[dict[str, Any], str | None, dict[str, Any] | None]:
    """应用语义帧到 fields。

    Returns:
        updated_fields, reply_override, pending_clarification_update
        pending: None=不变, {}=清除, dict=设置
    """
    if not frame.normalized_text and not frame.slot_updates and not frame.reply_override:
        return fields, None, None

    updated = apply_slot_updates(fields, frame, state)
    pending_update: dict[str, Any] | None = None

    if frame.pending_clarification_cleared:
        pending_update = {}
    elif frame.pending_clarification:
        pending_update = frame.pending_clarification

    return updated, frame.reply_override, pending_update


def semantic_frame_to_extraction(frame: SemanticFrame) -> RequirementExtraction:
    """将语义帧中的 slot_updates 转为 RequirementExtraction（规则抽取替代）。"""
    data = dict(frame.slot_updates)
    return RequirementExtraction(**{k: v for k, v in data.items() if v is not None})


def semantic_rule_extract_from_messages(
    messages: list[BaseMessage],
    fields: dict[str, Any],
    state: dict[str, Any],
) -> tuple[RequirementExtraction, SemanticFrame]:
    """规则语义抽取，替代原 _heuristic_extract_from_messages 的城市/日期/天数部分。"""
    frame = build_semantic_frame(messages, fields, state)
    extraction = semantic_frame_to_extraction(frame)

    # 扫描历史消息中的节日/日期/天数（非当前 step 的并行提取）
    from app.graph.semantic.slot_tracker import _extract_rule_slots  # noqa: PLC0415
    from langchain_core.messages import HumanMessage  # noqa: PLC0415

    merged = extraction.model_dump()
    for message in messages:
        if not isinstance(message, HumanMessage):
            continue
        content = message.content if isinstance(message.content, str) else str(message.content)
        normalized, _ = normalize_text(content.strip())
        partial = _extract_rule_slots(normalized, "departure_date")
        for key, value in partial.items():
            if value is not None and merged.get(key) is None:
                merged[key] = value

    return RequirementExtraction(**merged), frame
