"""plan_destination 节点：目的地推荐 vs 确认语义。"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.nodes.plan_destination import plan_destination
from app.schemas.travel import PlanningSelectionExtraction


@pytest.mark.asyncio
async def test_plan_destination_does_not_skip_on_collect_only_destination() -> None:
    """收集阶段的 destination 意向不应跳过「推荐 3 个目的地」流程。"""
    state = {
        "user_requirement": {"destination": "成都", "travel_days": 3},
        "destination": "成都",
        "messages": [HumanMessage(content="我想去成都，3天")],
    }
    with patch(
        "app.graph.nodes.plan_destination.extract_planning_selections",
        new_callable=AsyncMock,
        return_value=PlanningSelectionExtraction(selected_destination="成都"),
    ), patch(
        "app.graph.nodes.plan_destination.build_step_instruction",
        return_value="instruction",
    ), patch(
        "app.graph.nodes.plan_destination.invoke_step_llm",
        new_callable=AsyncMock,
        return_value="推荐三个目的地：1. 成都 2. 重庆 3. 西安",
    ):
        result = await plan_destination(state)

    assert result["current_step"] == "plan_destination"
    assert "selected_destination" not in result


@pytest.mark.asyncio
async def test_plan_destination_confirms_after_recommendation() -> None:
    state = {
        "user_requirement": {"destination": "成都", "travel_days": 3},
        "messages": [
            HumanMessage(content="我想去成都"),
            AIMessage(content="为您推荐三个目的地：1. 成都 2. 重庆 3. 西安"),
            HumanMessage(content="选第一个"),
        ],
    }
    with patch(
        "app.graph.nodes.plan_destination.extract_planning_selections",
        new_callable=AsyncMock,
        return_value=PlanningSelectionExtraction(selected_destination="成都"),
    ):
        result = await plan_destination(state)
    assert result["current_step"] == "plan_transport"
    assert result["selected_destination"] == "成都"
