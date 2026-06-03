"""approval_router 路由与关键词检测测试。"""

import pytest

from app.graph.routers.approval_router import (
    route_after_approval,
    route_after_itinerary,
    user_wants_approval,
    user_wants_revision,
)


def test_user_wants_approval_keywords() -> None:
    assert user_wants_approval("确认行程")
    assert user_wants_approval("OK 可以")
    assert not user_wants_approval("我想改一下")


def test_user_wants_revision_keywords() -> None:
    assert user_wants_revision("修改第二天")
    assert user_wants_revision("change hotel")
    assert not user_wants_revision("确认")


def test_route_after_itinerary() -> None:
    state = {"itinerary": [{"day_number": 1}], "current_step": "approval_node"}
    assert route_after_itinerary(state) == "approval_node"
    assert route_after_itinerary({"current_step": "approval_node"}) != "approval_node"


def test_route_after_approval() -> None:
    assert route_after_approval({"current_step": "final_response"}) == "final_response"
    assert route_after_approval({"current_step": "revise_itinerary"}) == "revise_itinerary"


def test_revision_priority_over_approval_in_mixed_phrase() -> None:
    assert user_wants_revision("确认但改酒店")
    assert user_wants_approval("确认但改酒店")


@pytest.mark.asyncio
async def test_approval_node_revision_before_approval() -> None:
    from langchain_core.messages import HumanMessage

    from app.graph.nodes.approval_node import approval_node

    state = {
        "itinerary": [{"day_number": 1}],
        "messages": [HumanMessage(content="确认但改酒店")],
    }
    result = await approval_node(state)
    assert result["current_step"] == "revise_itinerary"


@pytest.mark.asyncio
async def test_approval_node_skips_stale_revision_after_rebuild() -> None:
    from langchain_core.messages import HumanMessage

    from app.graph.nodes.approval_node import approval_node

    revision = "我想修改行程，请根据我的偏好重新调整。"
    state = {
        "itinerary": [{"day_number": 1}],
        "approval_status": "pending",
        "consumed_revision_note": revision[:200],
        "messages": [HumanMessage(content=revision)],
    }
    result = await approval_node(state)
    assert result["current_step"] == "approval_node"
    assert result["approval_status"] == "pending"
    assert "行程与预算已生成" in result["messages"][0].content
