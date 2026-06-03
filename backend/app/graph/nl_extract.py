"""从对话中抽取规划步骤选择（Route 1 NL 解析）。"""

from __future__ import annotations

import re

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from app.ai.llm import get_chat_model
from app.schemas.travel import (
    VALID_ACCOMMODATION,
    VALID_ACTIVITY,
    VALID_FOOD,
    VALID_TRANSPORT,
    PlanningSelectionExtraction,
)
from app.settings import settings

_SELECTION_SYSTEM = """你是旅行规划选择抽取器。从最近对话中提取用户已明确的选择。
规则：
- selected_destination：用户确认的目的地城市/地区名（中文或英文均可）
- selected_transport：仅当用户明确选择时填 flight / train / driving
- selected_accommodation_types：从 star_hotel, economy_hotel, hostel, youth_hostel 中选（可多选）
- selected_food_types：从 specialty, chain, local 中选（可多选）
- selected_activity_types：从 culture, nature, food_tour, shopping, family_fun 中选（可多选）
- 仅提取用户侧明确表达；助手推荐但未确认则留空
"""

_TRANSPORT_ALIASES: dict[str, str] = {
    "航班": "flight",
    "飞机": "flight",
    "flight": "flight",
    "高铁": "train",
    "火车": "train",
    "train": "train",
    "自驾": "driving",
    "开车": "driving",
    "driving": "driving",
}

_ACCOMMODATION_ALIASES: dict[str, str] = {
    "星级": "star_hotel",
    "豪华": "star_hotel",
    "star_hotel": "star_hotel",
    "经济": "economy_hotel",
    "economy_hotel": "economy_hotel",
    "民宿": "hostel",
    "hostel": "hostel",
    "青年旅社": "youth_hostel",
    "youth_hostel": "youth_hostel",
}

_ACTIVITY_ALIASES: dict[str, str] = {
    "文化": "culture",
    "博物馆": "culture",
    "culture": "culture",
    "自然": "nature",
    "户外": "nature",
    "nature": "nature",
    "美食之旅": "food_tour",
    "吃喝": "food_tour",
    "food_tour": "food_tour",
    "购物": "shopping",
    "shopping": "shopping",
    "亲子": "family_fun",
    "带娃": "family_fun",
    "family_fun": "family_fun",
}

_FOOD_ALIASES: dict[str, str] = {
    "特色": "specialty",
    "specialty": "specialty",
    "连锁": "chain",
    "chain": "chain",
    "本地": "local",
    "小吃": "local",
    "local": "local",
}


def dialogue_text(messages: list[BaseMessage], *, last_n: int = 12) -> str:
    lines: list[str] = []
    for message in messages[-last_n:]:
        if isinstance(message, SystemMessage):
            continue
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            lines.append(f"用户: {content}")
        elif isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            lines.append(f"助手: {content}")
    return "\n".join(lines) if lines else "（暂无对话）"


def _rule_based_selection(text: str) -> PlanningSelectionExtraction:
    """规则兜底：匹配常见中文/英文关键词。"""
    lower = text.lower()
    transport: str | None = None
    for key, value in _TRANSPORT_ALIASES.items():
        if key in lower or key in text:
            transport = value
            break

    accommodations: list[str] = []
    for key, value in _ACCOMMODATION_ALIASES.items():
        if key in text or key in lower:
            if value not in accommodations:
                accommodations.append(value)

    foods: list[str] = []
    for key, value in _FOOD_ALIASES.items():
        if key in text or key in lower:
            if value not in foods:
                foods.append(value)

    activities: list[str] = []
    for key, value in _ACTIVITY_ALIASES.items():
        if key in text or key in lower:
            if value not in activities:
                activities.append(value)

    destination: str | None = None
    dest_match = re.search(
        r"(?:去|到|选|想去|目的地[是为：:]\s*)([\u4e00-\u9fffA-Za-z]{2,10})",
        text,
    )
    if dest_match:
        destination = dest_match.group(1).strip()

    return PlanningSelectionExtraction(
        selected_destination=destination,
        selected_transport=transport if transport in VALID_TRANSPORT else None,  # type: ignore[arg-type]
        selected_accommodation_types=[
            a for a in accommodations if a in VALID_ACCOMMODATION  # type: ignore[misc]
        ],
        selected_food_types=[f for f in foods if f in VALID_FOOD],  # type: ignore[misc]
        selected_activity_types=[
            a for a in activities if a in VALID_ACTIVITY  # type: ignore[misc]
        ],
    )


async def extract_planning_selections(
    messages: list[BaseMessage],
) -> PlanningSelectionExtraction:
    dialogue = dialogue_text(messages)
    rules = _rule_based_selection(dialogue)

    if not settings.mimo_api_key:
        return rules

    try:
        structured_llm = get_chat_model().bind(temperature=0).with_structured_output(
            PlanningSelectionExtraction,
        )
        llm_result: PlanningSelectionExtraction = await structured_llm.ainvoke(
            [
                SystemMessage(content=_SELECTION_SYSTEM),
                HumanMessage(content=f"对话记录：\n{dialogue}"),
            ],
        )
        return PlanningSelectionExtraction(
            selected_destination=llm_result.selected_destination or rules.selected_destination,
            selected_transport=llm_result.selected_transport or rules.selected_transport,
            selected_accommodation_types=llm_result.selected_accommodation_types
            or rules.selected_accommodation_types,
            selected_food_types=llm_result.selected_food_types or rules.selected_food_types,
            selected_activity_types=llm_result.selected_activity_types
            or rules.selected_activity_types,
        )
    except Exception as exc:
        logger.warning("规划选择抽取失败，使用规则兜底: {}", exc)
        return rules
