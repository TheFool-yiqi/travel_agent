"""口语化表达 → 结构化槽位（人数/预算/交通/时间/天数）。"""

from __future__ import annotations

import re
from typing import Any

from app.graph.templates.budget_tiers import apply_budget_tier_to_fields, apply_party_from_dialogue
from app.graph.templates.collect_guidance import GuidanceStep
from app.tools.datetime_tools import parse_relative_date
from app.tools.holiday_calendar import extract_whole_holiday_travel_days

# 口语 → 规范短语（便于后续规则/LLM 理解）
_COLLOQUIAL_PHRASE_MAP: tuple[tuple[str, str], ...] = (
    (r"下礼拜", "下周"),
    (r"这礼拜", "本周"),
    (r"礼拜", "周"),
    (r"过俩天|过两天", "后天"),
    (r"带俩娃|带两娃", "2个儿童"),
    (r"一家三口", "2成人1儿童"),
    (r"老两口", "2位成人"),
    (r"坐高铁|坐动车|乘高铁", "高铁出行"),
    (r"飞过去|坐飞机|乘飞机", "飞机出行"),
    (r"开车去|自驾", "自驾出行"),
    (r"学生党|打工人", "穷游党"),
    (r"随便玩玩", "一般党"),
    (r"三四天|三四个天", "3-4天"),
    (r"玩个(\d+)来天", r"玩\1天"),
)

_COMPILED_PHRASE_MAP = tuple(
    (re.compile(pattern), replacement) for pattern, replacement in _COLLOQUIAL_PHRASE_MAP
)

_TRANSPORT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"高铁|动车|火车"), "交通偏好：高铁/火车"),
    (re.compile(r"飞机|航班|坐飞机|飞过去"), "交通偏好：飞机"),
    (re.compile(r"自驾|开车去"), "交通偏好：自驾"),
)

_BUDGET_TOTAL = re.compile(r"(总共|一共|合计|总计)\s*(\d+(?:\.\d+)?)\s*(?:元|块|万)?")
_BUDGET_PER_PERSON = re.compile(r"(每人|人均|一个人)\s*(\d+(?:\.\d+)?)\s*(?:元|块|万)?")
_BUDGET_AMOUNT_ONLY = re.compile(r"^(\d+(?:\.\d+)?)\s*(?:元|块|万)?$")
_DAYS_RANGE = re.compile(r"(\d+)\s*[-~到至]\s*(\d+)\s*天")
_DAYS_LOOSE = re.compile(r"(\d+)\s*来?\s*天")


def expand_colloquial_phrases(text: str) -> str:
    """将口语短语扩展为规范表达（不改变未匹配部分）。"""
    result = text
    for pattern, replacement in _COMPILED_PHRASE_MAP:
        result = pattern.sub(replacement, result)
    return result


def _parse_amount(raw: str) -> float:
    value = float(raw)
    return value


def _extract_transport_needs(text: str) -> str | None:
    for pattern, label in _TRANSPORT_PATTERNS:
        if pattern.search(text):
            return label
    return None


def _extract_budget_amounts(text: str) -> dict[str, Any]:
    """解析预算金额；区分每人 vs 总共。"""
    total_match = _BUDGET_TOTAL.search(text)
    if total_match:
        amount = _parse_amount(total_match.group(2))
        if "万" in total_match.group(0):
            amount *= 10000
        return {"budget_scope": "total", "budget_amount": amount}

    per_match = _BUDGET_PER_PERSON.search(text)
    if per_match:
        amount = _parse_amount(per_match.group(2))
        if "万" in per_match.group(0):
            amount *= 10000
        return {"budget_scope": "per_person", "budget_amount": amount}

    if _BUDGET_AMOUNT_ONLY.match(text.strip()):
        amount = _parse_amount(_BUDGET_AMOUNT_ONLY.match(text.strip()).group(1))  # type: ignore[union-attr]
        return {"budget_scope": "unknown", "budget_amount": amount}

    return {}


def _extract_travel_days(text: str) -> int | None:
    range_match = _DAYS_RANGE.search(text)
    if range_match:
        low, high = int(range_match.group(1)), int(range_match.group(2))
        return (low + high) // 2

    loose = _DAYS_LOOSE.search(text)
    if loose:
        return int(loose.group(1))
    return None


def extract_intent_slots(
    text: str,
    step: GuidanceStep,
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> dict[str, Any]:
    """从口语输入提取与当前步骤相关的槽位更新。"""
    if not text.strip():
        return {}

    expanded = expand_colloquial_phrases(text)
    updates: dict[str, Any] = {}

    whole_holiday_days = extract_whole_holiday_travel_days(
        text,
        fields,
        dialogue_text=dialogue_text,
    ) or extract_whole_holiday_travel_days(
        expanded,
        fields,
        dialogue_text=dialogue_text,
    )

    transport = _extract_transport_needs(expanded)
    if transport:
        existing = fields.get("special_needs") or ""
        if transport not in existing:
            updates["special_needs"] = f"{existing}；{transport}".strip("；")

    if step == "party" or step != "destination":
        party_fields = apply_party_from_dialogue({}, expanded)
        for key in ("adult_count", "children_count", "party_confirmed"):
            if party_fields.get(key) is not None:
                updates[key] = party_fields[key]

    if step == "budget":
        tier_fields = apply_budget_tier_to_fields({}, expanded)
        if tier_fields.get("budget_min") is not None:
            updates["budget_min"] = tier_fields["budget_min"]
            updates["budget_max"] = tier_fields["budget_max"]
            if tier_fields.get("budget_tier"):
                updates["budget_tier"] = tier_fields["budget_tier"]
        else:
            budget_raw = _extract_budget_amounts(expanded)
            if budget_raw:
                updates.update(budget_raw)

    if step == "travel_days" or "天" in expanded:
        days = _extract_travel_days(expanded)
        if days and not fields.get("travel_days"):
            updates["travel_days"] = days

    if step == "travel_days" or step != "destination":
        if whole_holiday_days and not fields.get("travel_days"):
            updates["travel_days"] = whole_holiday_days

    if step == "departure_date" or step != "destination":
        rel_date = parse_relative_date(expanded)
        if rel_date and not fields.get("departure_date"):
            updates["departure_date"] = rel_date

    return updates
