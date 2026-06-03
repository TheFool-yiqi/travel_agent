"""revise_itinerary 节点测试。"""

from __future__ import annotations

import pytest
from langchain_core.messages import HumanMessage

from app.graph.nodes.revise_itinerary import revise_itinerary


@pytest.mark.asyncio
async def test_revise_clears_itinerary_and_budget() -> None:
    state = {
        "messages": [HumanMessage(content="修改第二天住经济型酒店")],
        "itinerary": [{"day_number": 1}, {"day_number": 2}],
        "budget": {"total": 3000},
        "approval_status": "pending",
    }
    result = await revise_itinerary(state)
    assert result["itinerary"] == []
    assert result["budget"] == {}
    assert result["approval_status"] is None
    assert result["current_step"] == "build_itinerary"


@pytest.mark.asyncio
async def test_revise_reply_mentions_regeneration() -> None:
    state = {
        "messages": [HumanMessage(content="change hotel")],
        "itinerary": [{"day_number": 1}],
    }
    result = await revise_itinerary(state)
    assert "重新生成" in result["messages"][0].content
