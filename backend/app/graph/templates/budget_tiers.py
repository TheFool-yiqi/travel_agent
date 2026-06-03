"""预算档位（穷游/一般/富有）与人数确认文案"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.schemas.travel import infer_budget_level


@dataclass(frozen=True)
class BudgetTier:
    key: str
    label: str
    budget_min: float
    budget_max: float
    hint: str


BUDGET_TIERS: tuple[BudgetTier, ...] = (
    BudgetTier(
        key="economy",
        label="穷游党",
        budget_min=800,
        budget_max=2000,
        hint="青旅/经济型住宿、公共交通为主，性价比优先",
    ),
    BudgetTier(
        key="comfort",
        label="一般党",
        budget_min=2000,
        budget_max=5000,
        hint="舒适型酒店、精选体验，均衡省心",
    ),
    BudgetTier(
        key="luxury",
        label="富有党",
        budget_min=5000,
        budget_max=15000,
        hint="高端酒店、品质优先，体验拉满",
    ),
)

_TIER_BY_KEY = {tier.key: tier for tier in BUDGET_TIERS}
_TIER_BY_LABEL = {tier.label: tier for tier in BUDGET_TIERS}

_TIER_KEYWORDS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"穷游|省钱|经济型|预算有限|便宜点|学生党"), "economy"),
    (re.compile(r"一般党|随便玩玩"), "comfort"),
    (re.compile(r"富有党|富有|豪华|轻奢|高端|不差钱|品质优先"), "luxury"),
)

_SOLO_PARTY = re.compile(r"独自|一个人|就我|自己(去|玩|出行)?|单身")
_ADULT_CHILD = re.compile(r"(\d+)\s*大\s*(\d+)\s*小")
_ADULTS = re.compile(r"(\d+)\s*个?\s*(?:大人|成人|成年人|位)")
_CHILDREN = re.compile(r"(\d+)\s*个?\s*(?:小孩|儿童|娃|孩子)")


def format_budget_tier_lines() -> list[str]:
    return [
        f"{tier.label}：约 {int(tier.budget_min)}-{int(tier.budget_max)} 元/人（{tier.hint}）"
        for tier in BUDGET_TIERS
    ]


def render_party_question() -> str:
    return (
        "这次一行有几位呢？请告诉我成人和儿童人数，"
        "例如「2 成人 + 1 儿童（5 岁）」或「就我一个人」。"
    )


def render_budget_tier_question() -> str:
    tier_text = "；".join(format_budget_tier_lines())
    return (
        f"了解啦，咱们按每人预算（含交通、吃住、门票）来定个档位：{tier_text}。"
        "您更倾向哪一档？也可以直接回复「穷游党 / 一般党 / 富有党」。"
    )


def _user_dialogue_text(dialogue_text: str) -> str:
    lines: list[str] = []
    for line in dialogue_text.splitlines():
        if line.startswith("用户:"):
            lines.append(line.removeprefix("用户:").strip())
    return "\n".join(lines)


def detect_budget_tier_key(text: str) -> str | None:
    if not text:
        return None
    for label, tier in _TIER_BY_LABEL.items():
        if label in text:
            return tier.key
    for pattern, key in _TIER_KEYWORDS:
        if pattern.search(text):
            return key
    return None


def apply_budget_tier_to_fields(fields: dict[str, Any], text: str) -> dict[str, Any]:
    """用户选择档位时写入 budget_min/max（已有明确金额则不覆盖）。"""
    if fields.get("budget_min") is not None and fields.get("budget_max") is not None:
        return fields
    user_text = _user_dialogue_text(text) if "用户:" in text else text
    key = detect_budget_tier_key(user_text)
    if not key:
        return fields
    tier = _TIER_BY_KEY[key]
    updated = dict(fields)
    updated["budget_min"] = tier.budget_min
    updated["budget_max"] = tier.budget_max
    updated["budget_tier"] = tier.label
    return updated


def apply_party_from_dialogue(fields: dict[str, Any], text: str) -> dict[str, Any]:
    """从对话解析人数；解析成功则标记 party_confirmed。"""
    if not text:
        return fields
    updated = dict(fields)
    stripped = text.strip()

    if _SOLO_PARTY.search(stripped):
        updated["adult_count"] = 1
        updated["children_count"] = 0
        updated["party_confirmed"] = True
        return updated

    match = _ADULT_CHILD.search(stripped)
    if match:
        updated["adult_count"] = int(match.group(1))
        updated["children_count"] = int(match.group(2))
        updated["party_confirmed"] = True
        return updated

    adults_match = _ADULTS.search(stripped)
    children_match = _CHILDREN.search(stripped)
    if adults_match or children_match:
        if adults_match:
            updated["adult_count"] = int(adults_match.group(1))
        if children_match:
            updated["children_count"] = int(children_match.group(1))
        if updated.get("adult_count") is None:
            updated["adult_count"] = 1
        if updated.get("children_count") is None:
            updated["children_count"] = 0
        updated["party_confirmed"] = True
        return updated

    # 纯数字「2人」「3个人」
    people_match = re.search(r"(\d+)\s*个?\s*人", stripped)
    if people_match and len(stripped) <= 12:
        updated["adult_count"] = int(people_match.group(1))
        updated["children_count"] = 0
        updated["party_confirmed"] = True

    return updated


def is_party_confirmed(fields: dict[str, Any]) -> bool:
    return bool(fields.get("party_confirmed"))


def format_budget_summary(fields: dict[str, Any]) -> str:
    budget_min = fields.get("budget_min")
    budget_max = fields.get("budget_max")
    if budget_min is None or budget_max is None:
        return ""
    tier_label = fields.get("budget_tier")
    if not tier_label:
        level = infer_budget_level(float(budget_min), float(budget_max))
        tier_label = next((t.label for t in BUDGET_TIERS if t.key == level), "")
    range_text = f"每人 {int(float(budget_min))}-{int(float(budget_max))} 元"
    if tier_label:
        return f"预算：{tier_label}（{range_text}）"
    return f"预算：{range_text}"
