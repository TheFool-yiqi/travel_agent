"""冒烟测试 — 主路径 / 修订路径 / 异常路径自动化断言。"""

from __future__ import annotations

import pytest

from app.graph.routers.approval_router import user_wants_approval, user_wants_revision
from app.graph.templates.collect_guidance import next_guidance_step
from app.graph.validators.requirements import sanitize_budget, sanitize_travel_styles
from app.tools.holiday_calendar import extract_whole_holiday_travel_days


pytestmark = pytest.mark.smoke


@pytest.mark.smoke_main
def test_guidance_after_departure_city_keeps_destination() -> None:
    fields = {"destination": "成都", "departure_city": "上海"}
    assert next_guidance_step(fields) == "departure_date"


@pytest.mark.smoke_main
def test_guidance_step_order_empty_to_budget() -> None:
    """需求收集引导顺序：目的地 → … → 预算。"""
    fields: dict = {}
    assert next_guidance_step(fields) == "destination"
    fields["destination"] = "北京"
    assert next_guidance_step(fields) == "departure_city"
    fields["departure_city"] = "上海"
    assert next_guidance_step(fields) == "departure_date"
    fields["departure_date"] = "2026-06-19"
    assert next_guidance_step(fields) == "travel_days"
    fields["travel_days"] = 3
    assert next_guidance_step(fields) == "party"
    fields["adult_count"] = 1
    fields["children_count"] = 0
    fields["party_confirmed"] = True
    assert next_guidance_step(fields) == "budget"
    fields["budget_min"] = 800
    fields["budget_max"] = 2000
    assert next_guidance_step(fields) == "done"


@pytest.mark.smoke_revision
def test_approval_keywords() -> None:
    assert user_wants_approval("确认行程")
    assert user_wants_approval("OK 可以")
    assert not user_wants_approval("我想改一下")


@pytest.mark.smoke_revision
def test_revision_keywords() -> None:
    assert user_wants_revision("修改第二天")
    assert user_wants_revision("change hotel")
    assert not user_wants_revision("确认")


@pytest.mark.smoke_exception
def test_whole_holiday_duration_for_dragon_boat() -> None:
    fields = {"departure_date": "2026-06-19"}
    assert extract_whole_holiday_travel_days("整个假期", fields) == 3


@pytest.mark.smoke_exception
def test_budget_not_inferred_without_user_input() -> None:
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "destination": "成都",
        "budget_min": 2000,
        "budget_max": 5000,
        "budget_tier": "一般党",
    }
    dialogue = "\n".join(
        [
            "用户: 成都",
            "用户: 上海",
            "用户: 2026-06-19",
            "用户: 3天",
        ],
    )
    sanitized = sanitize_budget(fields, dialogue_text=dialogue)
    assert "budget_min" not in sanitized
    assert "budget_tier" not in sanitized


@pytest.mark.smoke_exception
def test_travel_style_not_inferred_without_user_input() -> None:
    fields = {
        "destination": "北京",
        "travel_styles": ["culture"],
    }
    dialogue = "用户: 穷游党\n助手: 好的"
    sanitized = sanitize_travel_styles(fields, dialogue_text=dialogue)
    assert sanitized.get("travel_styles") in (None, [])


@pytest.mark.smoke_exception
def test_xizang_not_resolved_to_xian() -> None:
    from app.graph.semantic.destination_resolver import resolve_destination_input

    result = resolve_destination_input("西藏")
    assert result.action == "accept"
    assert result.city == "西藏"
    assert result.city != "西安"


@pytest.mark.smoke_exception
def test_tiantang_not_auto_tianjin() -> None:
    from app.graph.semantic.destination_resolver import resolve_destination_input
    from app.graph.semantic.slot_tracker import bind_utterance_to_slots

    result = resolve_destination_input("天堂")
    assert result.action == "clarify"
    assert "destination" not in bind_utterance_to_slots("天堂", {}, {}).slot_updates


@pytest.mark.smoke_exception
def test_departure_destination_collision_sanitized() -> None:
    from app.graph.semantic.frame import SemanticFrame
    from app.graph.semantic.slot_sanitizer import sanitize_departure_city_collision

    fields = {"destination": "成都", "departure_city": "成都"}
    frame = SemanticFrame(
        slot_updates={"destination": "成都"},
        pending_clarification_cleared=True,
        guidance_step="destination",
    )
    state = {
        "pending_clarification": {
            "slot": "destination",
            "candidate": "成都",
            "original": "程度",
        },
    }
    cleaned = sanitize_departure_city_collision(fields, state, frame)
    assert "departure_city" not in cleaned
    assert cleaned.get("destination") == "成都"


@pytest.mark.smoke_main
def test_multi_slot_cross_turn_preserves_destination() -> None:
    """FLOW-09 / TC-FLOW-042: 成都→上海→日期跨轮不丢 destination。"""
    from app.graph.nodes.collect_requirements import merge_extraction
    from app.schemas.travel import RequirementExtraction

    state: dict = {}
    state = merge_extraction(state, RequirementExtraction(destination="成都"))
    assert state.get("destination") == "成都"
    state = merge_extraction(state, RequirementExtraction(departure_city="上海"))
    assert state.get("destination") == "成都"
    assert state.get("departure_city") == "上海"
    state = merge_extraction(state, RequirementExtraction(departure_date="2026-07-01"))
    assert state.get("departure_date") == "2026-07-01"
    assert state.get("destination") == "成都"
