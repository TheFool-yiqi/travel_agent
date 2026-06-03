"""collect_requirements extraction and greeting tests."""

from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage

from app.graph.greeting import build_greeting_reply, is_greeting_only_text
from app.graph.nodes.collect_requirements import (
    _heuristic_extract,
    _is_greeting_only,
    _merge_extractions,
    collect_requirements,
    merge_extraction,
)
from app.schemas.travel import RequirementExtraction


def test_greeting_only_detects_nihao() -> None:
    assert is_greeting_only_text("你好") is True
    assert is_greeting_only_text("nihao") is True
    assert _is_greeting_only([HumanMessage(content="你好")]) is True


def test_greeting_only_rejects_trip_message() -> None:
    assert is_greeting_only_text("我想去成都玩三天") is False
    assert _is_greeting_only([HumanMessage(content="我想去成都玩三天")]) is False


def test_heuristic_extract_holiday_and_days() -> None:
    holiday = _heuristic_extract("端午节期间出发")
    assert holiday.departure_date == "2026-06-19"

    labor = _heuristic_extract("五一小长假")
    assert labor.departure_date == "2026-05-01"

    days = _heuristic_extract("想玩3天")
    assert days.travel_days == 3


def test_heuristic_extract_destination_phrase() -> None:
    dest = _heuristic_extract("想去成都玩")
    assert dest.destination == "成都"


def test_merge_extraction_keeps_state_city() -> None:
    state = {"departure_city": "上海"}
    extracted = RequirementExtraction(departure_date="2026-06-19")
    merged = merge_extraction(state, extracted)
    assert merged["departure_city"] == "上海"
    assert merged["departure_date"] == "2026-06-19"


def test_merge_extractions_prefers_llm_values() -> None:
    heuristic = RequirementExtraction(departure_city="上海")
    llm = RequirementExtraction(departure_date="2026-06-20")
    merged = _merge_extractions(llm, heuristic)
    assert merged.departure_city == "上海"
    assert merged.departure_date == "2026-06-20"


@pytest.mark.asyncio
async def test_collect_requirements_greeting_skips_llm() -> None:
    state = {"messages": [HumanMessage(content="你好")]}
    with patch(
        "app.graph.nodes.collect_requirements.invoke_step_llm",
        new_callable=AsyncMock,
    ) as mock_llm:
        result = await collect_requirements(state)
        mock_llm.assert_not_called()
    assert result["messages"][0].content == build_greeting_reply()
    assert result["current_step"] == "collect_requirements"


@pytest.mark.asyncio
async def test_collect_requirements_extract_before_reply() -> None:
    state = {"messages": [HumanMessage(content="上海")]}
    call_order: list[str] = []

    async def fake_extract(_messages):
        call_order.append("extract")
        return RequirementExtraction(departure_city="上海")

    async def fake_reply(_state, merged_fields, **kwargs):
        call_order.append("reply")
        assert merged_fields.get("destination") == "上海"
        return "上海是个不错的选择！您从哪个城市出发？"

    with (
        patch(
            "app.graph.nodes.collect_requirements.extract_requirements_from_dialogue",
            side_effect=fake_extract,
        ),
        patch(
            "app.graph.nodes.collect_requirements._generate_collect_reply",
            side_effect=fake_reply,
        ),
    ):
        result = await collect_requirements(state)

    assert call_order == ["extract", "reply"]
    assert "上海" in result["messages"][0].content


@pytest.mark.asyncio
async def test_collect_shanghai_skips_llm_for_departure_city_followup() -> None:
    state = {"messages": [HumanMessage(content="上海")]}
    with (
        patch(
            "app.graph.nodes.collect_requirements.extract_requirements_from_dialogue",
            new_callable=AsyncMock,
            return_value=RequirementExtraction(departure_city="上海"),
        ),
        patch(
            "app.graph.nodes.collect_requirements.invoke_step_llm",
            new_callable=AsyncMock,
        ) as mock_llm,
    ):
        result = await collect_requirements(state)
        mock_llm.assert_not_called()

    content = result["messages"][0].content
    assert result.get("destination") == "上海"
    assert "出发" in content
    assert "**" not in content


@pytest.mark.asyncio
async def test_collect_chengdu_typo_clarifies() -> None:
    state = {"messages": [HumanMessage(content="程度")]}
    with patch(
        "app.graph.nodes.collect_requirements.extract_requirements_from_dialogue",
        new_callable=AsyncMock,
        return_value=RequirementExtraction(),
    ):
        result = await collect_requirements(state)

    content = result["messages"][0].content
    assert "成都" in content
    assert result.get("pending_clarification", {}).get("candidate") == "成都"
