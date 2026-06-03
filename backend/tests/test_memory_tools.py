"""用户记忆 tools/ 层单元测试（Route 1 入口）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import app.tools.memory_tools as memory_module
from app.schemas.memory import (
    AccommodationPreference,
    TravelHistory,
    TravelRecord,
    UserMemory,
    UserProfile,
)
from app.tools.memory_tools import (
    ALL_MEMORY_TOOLS,
    MEMORY_TOOLS,
    add_travel_record_tool,
    fetch_user_memory,
    fetch_user_memory_text,
    get_user_memory_tool,
    save_accommodation_preference,
    save_dietary_restrictions,
    save_food_preferences,
    save_travel_record,
    save_travel_styles,
    update_travel_style_tool,
)


@pytest.fixture
def mock_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    service = MagicMock()
    service.get_user_memory = AsyncMock(
        return_value=UserMemory(
            user_id="user-1",
            profile=UserProfile(travel_styles=["文化探索"]),
            history=TravelHistory(
                completed_trips=[
                    TravelRecord(
                        destination="西安",
                        start_date="2025-08-01",
                        end_date="2025-08-05",
                        visited_attractions=["兵马俑"],
                    )
                ],
                accommodation_preference=AccommodationPreference(
                    preferred_types=["民宿"],
                    avg_budget_per_night=300.0,
                ),
            ),
        )
    )
    service.format_memory_for_prompt = AsyncMock(
        return_value="**用户历史偏好**：\n- 旅行风格：文化探索"
    )
    service.update_travel_styles = AsyncMock()
    service.update_dietary_restrictions = AsyncMock()
    service.update_food_preferences = AsyncMock()
    service.update_accommodation_preference = AsyncMock()
    service.add_completed_trip = AsyncMock()

    async def _get_service() -> MagicMock:
        return service

    monkeypatch.setattr(memory_module, "get_user_memory_service", _get_service)
    return service


@pytest.mark.asyncio
async def test_fetch_user_memory_delegates_to_service(
    mock_service: MagicMock,
) -> None:
    memory = await fetch_user_memory("user-1")

    mock_service.get_user_memory.assert_awaited_once_with("user-1")
    assert memory.user_id == "user-1"
    assert memory.profile.travel_styles == ["文化探索"]


@pytest.mark.asyncio
async def test_fetch_user_memory_text_delegates_to_service(
    mock_service: MagicMock,
) -> None:
    text = await fetch_user_memory_text("user-1")

    mock_service.format_memory_for_prompt.assert_awaited_once_with("user-1")
    assert "文化探索" in text


@pytest.mark.asyncio
async def test_save_travel_styles(mock_service: MagicMock) -> None:
    result = await save_travel_styles("user-1", ["美食之旅", "户外"])

    mock_service.update_travel_styles.assert_awaited_once_with(
        "user-1",
        ["美食之旅", "户外"],
    )
    assert "美食之旅" in result


@pytest.mark.asyncio
async def test_save_dietary_restrictions(mock_service: MagicMock) -> None:
    result = await save_dietary_restrictions("user-1", ["素食"])

    mock_service.update_dietary_restrictions.assert_awaited_once_with("user-1", ["素食"])
    assert "素食" in result


@pytest.mark.asyncio
async def test_save_food_preferences(mock_service: MagicMock) -> None:
    result = await save_food_preferences("user-1", ["辣", "当地特色"])

    mock_service.update_food_preferences.assert_awaited_once_with(
        "user-1",
        ["辣", "当地特色"],
    )
    assert "辣" in result


@pytest.mark.asyncio
async def test_save_accommodation_preference(mock_service: MagicMock) -> None:
    result = await save_accommodation_preference(
        "user-1",
        preferred_types=["星级酒店"],
        avg_budget=500.0,
    )

    mock_service.update_accommodation_preference.assert_awaited_once_with(
        "user-1",
        preferred_types=["星级酒店"],
        avg_budget=500.0,
    )
    assert "星级酒店" in result
    assert "500" in result


@pytest.mark.asyncio
async def test_save_travel_record(mock_service: MagicMock) -> None:
    result = await save_travel_record(
        "user-1",
        destination="成都",
        start_date="2026-05-01",
        end_date="2026-05-04",
        visited_attractions=["宽窄巷子", "锦里"],
    )

    mock_service.add_completed_trip.assert_awaited_once_with(
        "user-1",
        destination="成都",
        start_date="2026-05-01",
        end_date="2026-05-04",
        visited_attractions=["宽窄巷子", "锦里"],
    )
    assert "成都" in result
    assert "宽窄巷子" in result


def test_memory_tool_exports() -> None:
    update_names = {tool.name for tool in MEMORY_TOOLS}
    all_names = {tool.name for tool in ALL_MEMORY_TOOLS}

    assert update_names == {
        "update_travel_style_tool",
        "update_dietary_restriction_tool",
        "update_food_preference_tool",
        "update_accommodation_preference_tool",
        "add_travel_record_tool",
    }
    assert all_names == update_names | {"get_user_memory_tool"}
    assert get_user_memory_tool not in MEMORY_TOOLS


@pytest.mark.asyncio
async def test_get_user_memory_tool_uses_injected_state(
    mock_service: MagicMock,
) -> None:
    result = await get_user_memory_tool.coroutine(state={"user_id": "user-1"})

    assert "文化探索" in result
    mock_service.format_memory_for_prompt.assert_awaited_once_with("user-1")


@pytest.mark.asyncio
async def test_get_user_memory_tool_empty_memory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = MagicMock()
    service.format_memory_for_prompt = AsyncMock(return_value="")

    async def _get_service() -> MagicMock:
        return service

    monkeypatch.setattr(memory_module, "get_user_memory_service", _get_service)

    result = await get_user_memory_tool.coroutine(state={"user_id": "user-1"})
    assert result == "暂无用户长期记忆记录。"


@pytest.mark.asyncio
async def test_update_travel_style_tool_uses_injected_state(
    mock_service: MagicMock,
) -> None:
    result = await update_travel_style_tool.coroutine(
        styles=["休闲度假"],
        state={"user_id": "user-1"},
    )

    assert "休闲度假" in result
    mock_service.update_travel_styles.assert_awaited_once_with(
        "user-1",
        ["休闲度假"],
    )


@pytest.mark.asyncio
async def test_tool_missing_user_id_raises() -> None:
    with pytest.raises(ValueError, match="user_id"):
        await get_user_memory_tool.coroutine(state={})


@pytest.mark.asyncio
async def test_add_travel_record_tool_uses_injected_state(
    mock_service: MagicMock,
) -> None:
    result = await add_travel_record_tool.coroutine(
        destination="杭州",
        start_date="2026-04-01",
        end_date="2026-04-03",
        visited_attractions=["西湖"],
        state={"user_id": "user-1"},
    )

    assert "杭州" in result
    mock_service.add_completed_trip.assert_awaited_once()
