"""需求摘要模板（关键事实从 state 渲染，减少 LLM 编造）"""

from __future__ import annotations

from typing import Any

from app.graph.templates.budget_tiers import format_budget_summary
from app.tools.holiday_calendar import detect_holiday_label, format_holiday_departure_hint


def format_requirements_summary(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> str:
    """从已合并字段生成固定格式摘要，供确认与回复前缀使用。"""
    lines: list[str] = []
    if fields.get("departure_city"):
        lines.append(f"出发城市：{fields['departure_city']}")
    if fields.get("departure_date"):
        date_line = f"出发日期：{fields['departure_date']}"
        hint = format_holiday_departure_hint(dialogue_text)
        label = detect_holiday_label(dialogue_text)
        if hint and label:
            date_line = f"出发日期：{fields['departure_date']}（{label}）"
        lines.append(date_line)
    if fields.get("travel_days"):
        lines.append(f"出行天数：{fields['travel_days']} 天")
    if fields.get("party_confirmed") or fields.get("adult_count") is not None:
        adults = fields.get("adult_count") or 1
        children = fields.get("children_count") or 0
        lines.append(f"人数：{adults} 成人 + {children} 儿童")
    budget_line = format_budget_summary(fields)
    if budget_line:
        lines.append(budget_line)
    elif fields.get("budget_min") is not None and fields.get("budget_max") is not None:
        lines.append(f"预算：每人 {fields['budget_min']}-{fields['budget_max']} 元")
    if fields.get("destination"):
        lines.append(f"目的地：{fields['destination']}")
    if fields.get("travel_styles"):
        styles = fields["travel_styles"]
        if isinstance(styles, list) and styles:
            lines.append(f"旅行风格：{', '.join(styles)}")
    if fields.get("special_needs"):
        lines.append(f"特殊需求：{fields['special_needs']}")
    return "\n".join(lines) if lines else "（暂无）"


def render_facts_prefix(fields: dict[str, Any], *, dialogue_text: str = "") -> str:
    """回复开头必须使用的已确认事实块。"""
    summary = format_requirements_summary(fields, dialogue_text=dialogue_text)
    return f"【当前已确认】\n{summary}"
