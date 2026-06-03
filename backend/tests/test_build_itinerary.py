"""build_itinerary 单元测试（纯函数，不调用 LLM）"""

import pytest

from app.graph.nodes.build_itinerary import (
    budget_warning,
    build_itinerary,
    day_plan_to_dict,
    format_itinerary_message,
)
from app.schemas.travel import BudgetBreakdown, DayPlan, ItineraryBuildResult


def test_day_plan_to_dict():
    day = DayPlan(
        day_number=1,
        theme="抵达日",
        morning="入住酒店",
        afternoon="宽窄巷子",
        evening="火锅",
        meals=["午餐", "晚餐"],
        accommodation="春熙路附近",
        plan_b="室内博物馆",
    )
    result = day_plan_to_dict(day)
    assert result["day_number"] == 1
    assert len(result["activities"]) == 3
    assert result["plan_b"] == "室内博物馆"


def test_format_itinerary_message():
    result = ItineraryBuildResult(
        summary="成都 3 日美食文化之旅",
        days=[
            DayPlan(
                day_number=1,
                theme="抵达",
                morning="到达",
                afternoon="游览",
                evening="晚餐",
            ),
        ],
        budget=BudgetBreakdown(
            transport=1000,
            accommodation=1500,
            food=800,
            attractions=500,
            misc=200,
            total=4000,
        ),
    )
    text = format_itinerary_message(result)
    assert "成都 3 日" in text
    assert "4000" in text
    assert "Day 1" in text


def test_budget_warning_over_limit() -> None:
    state = {"user_requirement": {"budget_max": 3000}}
    warning = budget_warning(state, {"total": 5000})
    assert warning is not None
    assert "5000" in warning


def test_budget_warning_within_limit() -> None:
    state = {"user_requirement": {"budget_max": 8000}}
    assert budget_warning(state, {"total": 5000}) is None


@pytest.mark.asyncio
async def test_build_itinerary_skips_llm_after_revision() -> None:
    state = {
        "user_requirement": {
            "travel_days": 3,
            "adult_count": 1,
            "children_count": 0,
        },
        "selected_destination": "北京",
        "selected_transport": "train",
        "selected_accommodation_types": ["economy_hotel"],
        "selected_food_types": ["local"],
        "selected_activity_types": ["culture"],
        "consumed_revision_note": "我想修改行程",
        "report": "修订说明：我想修改行程",
    }
    result = await build_itinerary(state)
    assert result["current_step"] == "approval_node"
    assert len(result["itinerary"]) == 3
    assert "已按您的修订意见重新生成行程" in result["messages"][0].content
