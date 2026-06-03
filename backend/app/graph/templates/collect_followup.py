"""需求收集中间轮次的模板化追问（一次只引导一项）"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from app.graph.templates.budget_tiers import render_budget_tier_question, render_party_question
from app.graph.templates.collect_guidance import next_guidance_step
from app.graph.templates.requirements_summary import render_facts_prefix
from app.tools.datetime_tools import today_beijing
from app.tools.holiday_calendar import nearest_holiday_examples_text, suggest_holiday_travel_days


def _this_weekend(anchor: date) -> tuple[date, date]:
    days_until_sat = (5 - anchor.weekday()) % 7
    saturday = anchor + timedelta(days=days_until_sat)
    if anchor.weekday() == 6:
        saturday = anchor - timedelta(days=1)
    return saturday, saturday + timedelta(days=1)


def _format_md_range(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.month}月{start.day}-{end.day}日"
    return f"{start.month}月{start.day}日-{end.month}月{end.day}日"


def _ack_line(fields: dict[str, Any], step: str) -> str:
    """简短承接，不重复追问已确认项。"""
    destination = fields.get("destination")
    city = fields.get("departure_city")
    if step == "departure_city" and destination:
        return f"{destination}是个不错的选择！"
    if step == "departure_date" and city:
        return f"从{city}出发，交通安排会方便很多。"
    return ""


def _question_for_step(step: str, *, anchor: date) -> str:
    sat, sun = _this_weekend(anchor)
    weekend_label = _format_md_range(sat, sun)

    if step == "destination":
        return "你想去哪里玩？（例如：成都、杭州、三亚）"
    if step == "departure_city":
        return "您从哪个城市出发？（例如：北京、上海、成都）"
    if step == "departure_date":
        holiday_hint = nearest_holiday_examples_text(anchor, count=2)
        examples = [f"本周末（{weekend_label}）"]
        if holiday_hint:
            examples.append(holiday_hint)
        example_text = "、".join(examples)
        return f"您大概想什么时候出发？例如{example_text}？"
    if step == "travel_days":
        return "您计划玩几天？短途常见是 2-3 天（1-2 晚），如果想多逛几个地方可以选 4-5 天。"
    if step == "party":
        return render_party_question()
    if step == "budget":
        return render_budget_tier_question()
    return "我这边信息差不多齐了，您看看有没有要补充或修改的？"


def render_collect_followup(fields: dict[str, Any], *, dialogue_text: str = "") -> str:
    """按引导顺序每次只追问一项；节假日举例仅在问时间时出现。"""
    anchor = today_beijing()
    step = next_guidance_step(fields)

    if step == "done":
        summary_prefix = render_facts_prefix(fields, dialogue_text=dialogue_text)
        return f"{summary_prefix}\n\n{_question_for_step('done', anchor=anchor)}"

    ack = _ack_line(fields, step)
    question = _question_for_step(step, anchor=anchor)
    body = f"{ack} {question}".strip() if ack else question

    prefix = render_facts_prefix(fields, dialogue_text=dialogue_text)
    if fields.get("destination") or fields.get("departure_city") or fields.get("departure_date"):
        return f"{prefix}\n\n{body}"
    return body


def render_destination_clarification(city: str, original: str) -> str:
    """同音/近音错字：请用户确认候选城市。"""
    if original and original != city:
        return f"你是说「{city}」吗？确认的话我就按{city}来规划～"
    return f"你是说「{city}」吗？确认的话我就按{city}来规划～"


def render_destination_ambiguity(original: str, candidates: tuple[str, ...]) -> str:
    """多个接近候选：列出备选项，避免静默选错。"""
    if not candidates:
        return render_destination_unrecognized(original)
    options = "、".join(f"「{c}」" for c in candidates[:3])
    if original:
        return f"没太确定「{original}」指哪里，您是指 {options} 中的哪一个？直接回复地名或「对」确认即可～"
    return f"您是指 {options} 中的哪一个？直接回复地名即可～"


def render_destination_unrecognized(original: str) -> str:
    """无法识别短输入时，避免原样重复追问。"""
    hint = f"「{original}」" if original else "这个"
    return (
        f"没太确定{hint}是哪个目的地，方便再说一下城市名吗？"
        "比如成都、杭州、三亚～"
    )


def render_travel_days_clarification(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
    force_generic: bool = False,
) -> dict[str, Any]:
    """天数槽位未填时的澄清追问（含节日建议，避免重复同一模板句）。"""
    if not force_generic:
        suggestion = suggest_holiday_travel_days(fields, dialogue_text=dialogue_text)
        if suggestion:
            days, label = suggestion
            return {
                "reply": (
                    f"理解您想充分利用假期～{label}假期一般是{days}天，"
                    f"您是指{days}天吗？确认回复「对」即可，或直接告诉我具体天数～"
                ),
                "pending": {
                    "slot": "travel_days",
                    "kind": "travel_days",
                    "candidate": days,
                },
            }
    return {
        "reply": "没太确定您计划玩几天，方便说个大概吗？例如 2-3 天，或「整个小长假」也可以～",
        "pending": None,
    }
