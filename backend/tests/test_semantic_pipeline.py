"""语义流水线测试（P1.4）"""

from langchain_core.messages import HumanMessage

from app.graph.semantic.semantic_pipeline import (
    apply_semantic_frame,
    build_semantic_frame,
    semantic_rule_extract_from_messages,
)


def test_build_semantic_frame_typo():
    messages = [HumanMessage(content="程度")]
    frame = build_semantic_frame(messages, {}, {})
    assert frame.pending_clarification is not None
    assert frame.guidance_step == "destination"


def test_apply_semantic_frame_sets_destination():
    messages = [HumanMessage(content="成都")]
    frame = build_semantic_frame(messages, {}, {})
    fields, reply, pending = apply_semantic_frame({}, {}, frame)
    assert fields.get("destination") == "成都"
    assert reply is None
    assert pending is None


def test_semantic_rule_extract_replaces_heuristic_city():
    messages = [HumanMessage(content="成都")]
    extraction, frame = semantic_rule_extract_from_messages(messages, {}, {})
    assert extraction.destination == "成都"
    assert frame.slot_updates.get("destination") == "成都"
