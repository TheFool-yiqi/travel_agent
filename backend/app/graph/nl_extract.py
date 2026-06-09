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

_ORDINAL_RE = re.compile(r"选(?:第)?[一二三1-3个]|第[一二三1-3]")

_DELEGATION_CONFIRM_RE = re.compile(r"听你的|就按|按你推荐|你推荐|就这个|就这样")

_VAGUE_CONFIRM_ONLY_RE = re.compile(
    r"^(?:可以|好的|都行|你看着办|没问题|ok|OK)[。！!？?~～]*$"
)

_DEST_RECOMMENDATION_RE = re.compile(
    r"(?:3\s*个|三个).{0,8}目的地|目的地.{0,8}推荐|推荐.{0,8}目的地"
)

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

_COMFORT_ALIASES: dict[str, tuple[str, ...]] = {
    "便宜": ("economy_hotel", "train"),
    "实惠": ("economy_hotel", "train"),
    "省钱": ("economy_hotel", "train"),
    "舒适": ("star_hotel", "flight"),
    "舒服": ("star_hotel", "flight"),
    "豪华": ("star_hotel", "flight"),
}


def _last_user_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content.strip()
            return str(content).strip()
    return ""


def _last_turn_has_destination_recommendation(messages: list[BaseMessage]) -> bool:
    seen_user = False
    for message in reversed(messages):
        if isinstance(message, HumanMessage) and not seen_user:
            seen_user = True
            continue
        if seen_user and isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            return bool(_DEST_RECOMMENDATION_RE.search(content))
    return False


def _normalize_user_utterance(text: str) -> str:
    return text.replace("。", "").replace("！", "").replace("!", "").strip()


def _is_vague_confirm_only(user_text: str) -> bool:
    return bool(_VAGUE_CONFIRM_ONLY_RE.match(_normalize_user_utterance(user_text)))


def _assistant_text_for_recommendations(messages: list[BaseMessage]) -> str:
    parts: list[str] = []
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            parts.insert(0, content)
            if _DEST_RECOMMENDATION_RE.search(content):
                break
    return "\n".join(parts)


def _recommended_cities_from_text(text: str) -> list[str]:
    cities: list[str] = []
    for line in text.splitlines():
        content = line.removeprefix("助手:").strip() if line.startswith("助手:") else line
        for match in re.finditer(
            r"(?<![0-9])(?:[1-3①②③]|第[一二三])[\.、．:\s]+([\u4e00-\u9fff]{2,8})",
            content,
        ):
            city = match.group(1).rstrip("市城")
            if city not in cities:
                cities.append(city)
        for match in re.finditer(r"\*\*([\u4e00-\u9fff]{2,8})\*\*", content):
            city = match.group(1).rstrip("市城")
            if city not in cities:
                cities.append(city)
    return cities


def _resolve_ordinal_or_delegation_city(
    user_text: str,
    recommended: list[str],
) -> str | None:
    if not recommended:
        return None

    ordinal_map = {"一": 0, "二": 1, "三": 2, "1": 0, "2": 1, "3": 2}
    ordinal_match = re.search(r"第([一二三1-3])", user_text)
    if ordinal_match and _ORDINAL_RE.search(user_text):
        idx = ordinal_map.get(ordinal_match.group(1), 0)
        if idx < len(recommended):
            return recommended[idx]

    if _DELEGATION_CONFIRM_RE.search(user_text):
        return recommended[0]

    return None


def _explicit_destination_in_user_text(user_text: str, destination: str) -> bool:
    if destination not in user_text:
        return False
    patterns = (
        rf"(?<![想])去{re.escape(destination)}",
        rf"选{re.escape(destination)}",
        rf"目的地[是为：:\s]*{re.escape(destination)}",
    )
    return any(re.search(pattern, user_text) for pattern in patterns)


def resolve_confirmed_destination(
    messages: list[BaseMessage],
    *,
    selected_destination: str | None,
    extracted_destination: str | None,
) -> str | None:
    """仅在规划阶段确认后写入 selected_destination，避免收集阶段的意向被当成终选。"""
    if selected_destination:
        return selected_destination

    user_text = _last_user_text(messages)
    if not user_text or _is_vague_confirm_only(user_text):
        return None

    recommended = _recommended_cities_from_text(_assistant_text_for_recommendations(messages))

    bound = _resolve_ordinal_or_delegation_city(user_text, recommended)
    if bound:
        return bound

    if extracted_destination and _explicit_destination_in_user_text(user_text, extracted_destination):
        return extracted_destination

    if extracted_destination:
        normalized = _normalize_user_utterance(user_text)
        if normalized in (
            extracted_destination,
            f"去{extracted_destination}",
            f"选{extracted_destination}",
        ):
            return extracted_destination

    if (
        extracted_destination
        and _last_turn_has_destination_recommendation(messages)
        and extracted_destination in user_text
        and not _is_vague_confirm_only(user_text)
    ):
        return extracted_destination

    return None


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


def _rule_based_selection(
    user_text: str,
    *,
    assistant_text: str = "",
) -> PlanningSelectionExtraction:
    """规则兜底：交通/住宿/餐饮/活动仅匹配最近用户输入；序号目的地可读助手推荐列表。"""
    lower = user_text.lower()
    transport: str | None = None
    for key, value in _TRANSPORT_ALIASES.items():
        if key in lower or key in user_text:
            transport = value
            break

    if transport is None:
        for key, values in _COMFORT_ALIASES.items():
            if key in user_text:
                transport = values[1]
                break

    accommodations: list[str] = []
    for key, value in _ACCOMMODATION_ALIASES.items():
        if key in user_text or key in lower:
            if value not in accommodations:
                accommodations.append(value)

    if not accommodations:
        for key, values in _COMFORT_ALIASES.items():
            if key in user_text and values[0] not in accommodations:
                accommodations.append(values[0])

    foods: list[str] = []
    for key, value in _FOOD_ALIASES.items():
        if key in user_text or key in lower:
            if value not in foods:
                foods.append(value)

    activities: list[str] = []
    for key, value in _ACTIVITY_ALIASES.items():
        if key in user_text or key in lower:
            if value not in activities:
                activities.append(value)

    destination: str | None = None
    dest_match = re.search(
        r"(?:去|到|选|想去|目的地[是为：:]\s*)([\u4e00-\u9fffA-Za-z]{2,10})",
        user_text,
    )
    if dest_match:
        destination = dest_match.group(1).strip()

    if _ORDINAL_RE.search(user_text):
        ordinal_map = {"一": 0, "二": 1, "三": 2, "1": 0, "2": 1, "3": 2}
        ordinal_match = re.search(r"第([一二三1-3])", user_text)
        if ordinal_match:
            idx = ordinal_map.get(ordinal_match.group(1), 0)
            recommended = _recommended_cities_from_text(assistant_text)
            if recommended and idx < len(recommended):
                destination = recommended[idx]

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
    user_text = _last_user_text(messages)
    assistant_text = _assistant_text_for_recommendations(messages)
    rules = _rule_based_selection(user_text, assistant_text=assistant_text)

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
