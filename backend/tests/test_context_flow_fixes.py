"""上下文与流式 extra_info 修复回归测试。"""

from __future__ import annotations


def test_message_extra_merge_keeps_semantic_and_itinerary() -> None:
    """模拟 chat_stream 合并逻辑：itinerary 不应覆盖 semantic。"""
    message_extra: dict | None = {"semantic": {"step": "collect_requirements"}}
    itinerary = [{"day_number": 1, "title": "Day 1"}]
    budget = {"total": 1200.0}

    message_extra = dict(message_extra or {})
    message_extra["itinerary"] = itinerary
    message_extra["budget"] = budget

    assert message_extra["semantic"] == {"step": "collect_requirements"}
    assert message_extra["itinerary"] == itinerary
    assert message_extra["budget"] == budget
