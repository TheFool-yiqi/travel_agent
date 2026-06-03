"""用户长期记忆工具（Route 1：Agent 可调用，不进入 step_config 预执行）。"""

from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from loguru import logger

from app.dependencies import get_user_memory_service
from app.graph.state import TravelState
from app.schemas.memory import UserMemory


def _require_user_id(state: TravelState) -> str:
    user_id = state.get("user_id")
    if not user_id:
        raise ValueError("缺少 user_id，无法访问用户记忆")
    return user_id


async def fetch_user_memory(user_id: str) -> UserMemory:
    """加载完整用户长期记忆。"""
    service = await get_user_memory_service()
    return await service.get_user_memory(user_id)


async def fetch_user_memory_text(user_id: str) -> str:
    """加载并格式化为 Agent 可读文本。"""
    service = await get_user_memory_service()
    return await service.format_memory_for_prompt(user_id)


async def save_travel_styles(user_id: str, styles: list[str]) -> str:
    """合并更新旅行风格。"""
    service = await get_user_memory_service()
    await service.update_travel_styles(user_id, styles)
    logger.info("更新旅行风格 user_id={} styles={}", user_id, styles)
    return f"已更新旅行风格：{', '.join(styles)}"


async def save_dietary_restrictions(user_id: str, restrictions: list[str]) -> str:
    """合并更新饮食禁忌。"""
    service = await get_user_memory_service()
    await service.update_dietary_restrictions(user_id, restrictions)
    logger.info("更新饮食禁忌 user_id={} restrictions={}", user_id, restrictions)
    return f"已更新饮食禁忌：{', '.join(restrictions)}"


async def save_food_preferences(user_id: str, preferences: list[str]) -> str:
    """合并更新饮食偏好。"""
    service = await get_user_memory_service()
    await service.update_food_preferences(user_id, preferences)
    logger.info("更新饮食偏好 user_id={} preferences={}", user_id, preferences)
    return f"已更新饮食偏好：{', '.join(preferences)}"


async def save_accommodation_preference(
    user_id: str,
    preferred_types: list[str] | None = None,
    avg_budget: float | None = None,
) -> str:
    """更新住宿偏好（类型与/或每晚预算）。"""
    service = await get_user_memory_service()
    await service.update_accommodation_preference(
        user_id,
        preferred_types=preferred_types,
        avg_budget=avg_budget,
    )
    parts: list[str] = []
    if preferred_types:
        parts.append(f"类型 {', '.join(preferred_types)}")
    if avg_budget is not None:
        parts.append(f"预算约 {avg_budget:.0f} 元/晚")
    logger.info(
        "更新住宿偏好 user_id={} preferred_types={} avg_budget={}",
        user_id,
        preferred_types,
        avg_budget,
    )
    detail = "、".join(parts) if parts else "无变更"
    return f"已更新住宿偏好：{detail}"


async def save_travel_record(
    user_id: str,
    destination: str,
    start_date: str,
    end_date: str,
    visited_attractions: list[str],
) -> str:
    """添加已完成旅行记录。"""
    service = await get_user_memory_service()
    await service.add_completed_trip(
        user_id,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        visited_attractions=visited_attractions,
    )
    logger.info(
        "添加旅行记录 user_id={} destination={} {}-{}",
        user_id,
        destination,
        start_date,
        end_date,
    )
    attractions = ", ".join(visited_attractions) if visited_attractions else "无"
    return (
        f"已记录旅行：{destination}（{start_date} 至 {end_date}），"
        f"景点：{attractions}"
    )


@tool
async def get_user_memory_tool(
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    获取当前用户的长期记忆（旅行风格、饮食偏好、历史行程等）。

    当需要确认用户历史偏好或去过的目的地/景点时调用。
    """
    user_id = _require_user_id(state)
    text = await fetch_user_memory_text(user_id)
    return text or "暂无用户长期记忆记录。"


@tool
async def update_travel_style_tool(
    styles: list[str],
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    更新用户旅行风格偏好（如文化探索、美食之旅、休闲度假）。

    Args:
        styles: 要合并加入的旅行风格标签列表
    """
    user_id = _require_user_id(state)
    return await save_travel_styles(user_id, styles)


@tool
async def update_dietary_restriction_tool(
    restrictions: list[str],
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    更新用户饮食禁忌（如素食、清真、海鲜过敏）。

    Args:
        restrictions: 要合并加入的饮食禁忌列表
    """
    user_id = _require_user_id(state)
    return await save_dietary_restrictions(user_id, restrictions)


@tool
async def update_food_preference_tool(
    preferences: list[str],
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    更新用户饮食偏好（如辣、清淡、当地特色）。

    Args:
        preferences: 要合并加入的饮食偏好列表
    """
    user_id = _require_user_id(state)
    return await save_food_preferences(user_id, preferences)


@tool
async def update_accommodation_preference_tool(
    preferred_types: list[str] | None = None,
    avg_budget: float | None = None,
    *,
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    更新用户住宿偏好。

    Args:
        preferred_types: 偏好住宿类型，如星级酒店、民宿
        avg_budget: 平均每晚预算（元）
    """
    user_id = _require_user_id(state)
    return await save_accommodation_preference(
        user_id,
        preferred_types=preferred_types,
        avg_budget=avg_budget,
    )


@tool
async def add_travel_record_tool(
    destination: str,
    start_date: str,
    end_date: str,
    visited_attractions: list[str],
    state: Annotated[TravelState, InjectedState],
) -> str:
    """
    添加一条已完成旅行记录。

    Args:
        destination: 目的地
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        visited_attractions: 本次游玩景点列表
    """
    user_id = _require_user_id(state)
    return await save_travel_record(
        user_id,
        destination,
        start_date,
        end_date,
        visited_attractions,
    )


MEMORY_TOOLS = [
    update_travel_style_tool,
    update_dietary_restriction_tool,
    update_food_preference_tool,
    update_accommodation_preference_tool,
    add_travel_record_tool,
]

ALL_MEMORY_TOOLS = [get_user_memory_tool, *MEMORY_TOOLS]

__all__ = [
    "fetch_user_memory",
    "fetch_user_memory_text",
    "save_travel_styles",
    "save_dietary_restrictions",
    "save_food_preferences",
    "save_accommodation_preference",
    "save_travel_record",
    "get_user_memory_tool",
    "update_travel_style_tool",
    "update_dietary_restriction_tool",
    "update_food_preference_tool",
    "update_accommodation_preference_tool",
    "add_travel_record_tool",
    "MEMORY_TOOLS",
    "ALL_MEMORY_TOOLS",
]
