"""P2 user_confirmed gating tests."""

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.graph.nodes.collect_requirements import (
    can_advance_to_planning,
    collect_requirements,
    is_requirement_complete,
)


def test_can_advance_requires_confirmation() -> None:
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "budget_min": 1000,
        "budget_max": 3000,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
    }
    assert is_requirement_complete(fields)
    assert not can_advance_to_planning(fields, user_confirmed=False)
    assert can_advance_to_planning(fields, user_confirmed=True)


@pytest.mark.asyncio
async def test_collect_requirements_waits_for_confirmation() -> None:
    state = {
        "messages": [HumanMessage(content="确认")],
        "destination": "北京",
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "budget_min": 1000,
        "budget_max": 3000,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
    }
    with patch(
        "app.graph.nodes.collect_requirements.extract_requirements_from_dialogue",
        new_callable=AsyncMock,
        return_value=__import__(
            "app.schemas.travel", fromlist=["RequirementExtraction"]
        ).RequirementExtraction(user_confirmed=True),
    ), patch(
        "app.graph.nodes.collect_requirements._generate_collect_reply",
        new_callable=AsyncMock,
        return_value="好的，进入下一步。",
    ):
        result = await collect_requirements(state)

    assert result["requirements_complete"] is True
    assert result["current_step"] == "plan_destination"
    assert result.get("user_confirmed") is True
