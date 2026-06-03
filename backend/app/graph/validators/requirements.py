"""需求字段校验（防 LLM 幻觉写入 state）"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from app.tools.datetime_tools import today_beijing
from app.tools.holiday_calendar import validate_holiday_date_mismatch

_TRAVEL_STYLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("relaxation", re.compile(r"放松|躺平|休闲|度假|relaxation", re.I)),
    ("culture", re.compile(r"文化|人文|博物馆|历史|古迹|非遗|culture", re.I)),
    ("adventure", re.compile(r"户外|冒险|徒步|登山|探险|adventure", re.I)),
    ("food", re.compile(r"美食|吃喝|吃吃喝喝|吃货|food", re.I)),
)

_BUDGET_TIER_LABELS = re.compile(r"穷游党|一般党|富有党|学生党|随便玩玩")
_BUDGET_AMOUNT = re.compile(
    r"(总共|一共|合计|总计|每人|人均|一个人)\s*\d+(?:\.\d+)?\s*(?:元|块|万)?",
)
_BUDGET_AMOUNT_ONLY = re.compile(r"^\s*\d+(?:\.\d+)?\s*(?:元|块|万)?\s*$")
_BUDGET_KEYWORDS = re.compile(
    r"穷游|省钱|经济型|预算有限|便宜点|一般党|富有党|豪华|轻奢|高端|不差钱|品质优先|随便玩玩",
)

_REQUIRED_KEYS = ("departure_city", "departure_date", "travel_days", "budget_min", "budget_max")

_FIELD_LABELS: dict[str, str] = {
    "departure_city": "出发城市",
    "departure_date": "出发日期",
    "travel_days": "出行天数",
    "budget_min": "预算下限",
    "budget_max": "预算上限",
}


def validate_requirements(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> list[str]:
    """返回可读错误列表；空列表表示通过当前校验。"""
    errors: list[str] = []

    for key in _REQUIRED_KEYS:
        value = fields.get(key)
        if value is None or value == "":
            errors.append(f"缺少{_FIELD_LABELS[key]}")

    departure_date = fields.get("departure_date")
    if departure_date:
        try:
            parsed = datetime.strptime(str(departure_date), "%Y-%m-%d").date()
            if parsed < today_beijing():
                errors.append(f"出发日期 {departure_date} 早于今天，请确认")
        except ValueError:
            errors.append(f"出发日期格式无效：{departure_date}")

    travel_days = fields.get("travel_days")
    if travel_days is not None:
        try:
            days = int(travel_days)
            if days < 1:
                errors.append("出行天数至少为 1 天")
            elif days > 60:
                errors.append("出行天数过长，请确认是否在 60 天以内")
        except (TypeError, ValueError):
            errors.append(f"出行天数无效：{travel_days}")

    budget_min = fields.get("budget_min")
    budget_max = fields.get("budget_max")
    if budget_min is not None and budget_max is not None:
        try:
            if float(budget_min) > float(budget_max):
                errors.append("预算下限不能高于预算上限")
            if float(budget_min) < 0 or float(budget_max) < 0:
                errors.append("预算不能为负数")
        except (TypeError, ValueError):
            errors.append("预算范围格式无效")

    holiday_err = validate_holiday_date_mismatch(dialogue_text, str(departure_date) if departure_date else None)
    if holiday_err:
        errors.append(holiday_err)

    return errors


def _user_dialogue_text(dialogue_text: str) -> str:
    lines: list[str] = []
    for line in dialogue_text.splitlines():
        if line.startswith("用户:"):
            lines.append(line.removeprefix("用户:").strip())
    return "\n".join(lines)


def explicit_travel_styles_in_dialogue(dialogue_text: str) -> list[str]:
    """从用户发言中识别明确提到的旅行风格（不含 LLM 推断）。"""
    user_text = _user_dialogue_text(dialogue_text)
    if not user_text.strip():
        return []

    found: list[str] = []
    for style, pattern in _TRAVEL_STYLE_PATTERNS:
        if pattern.search(user_text):
            found.append(style)
    return found


def sanitize_travel_styles(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> dict[str, Any]:
    """移除未在用户对话中明确出现的 travel_styles。"""
    styles = fields.get("travel_styles") or []
    if not styles:
        return fields

    explicit = explicit_travel_styles_in_dialogue(dialogue_text)
    if not explicit:
        updated = dict(fields)
        updated.pop("travel_styles", None)
        return updated

    valid = [style for style in styles if style in explicit]
    updated = dict(fields)
    if valid:
        updated["travel_styles"] = valid
    else:
        updated.pop("travel_styles", None)
    return updated


def explicit_budget_in_dialogue(dialogue_text: str) -> bool:
    """用户发言中是否明确提到预算档位或金额（不含助手引导语）。"""
    user_text = _user_dialogue_text(dialogue_text)
    if not user_text.strip():
        return False

    for line in user_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if _BUDGET_TIER_LABELS.search(stripped):
            return True
        if _BUDGET_AMOUNT.search(stripped):
            return True
        if _BUDGET_KEYWORDS.search(stripped):
            return True
        if _BUDGET_AMOUNT_ONLY.match(stripped):
            return True
    return False


def sanitize_budget(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> dict[str, Any]:
    """移除未在用户对话中明确出现的 budget_min/max/tier（防 LLM 或规则误填）。"""
    if fields.get("budget_min") is None and fields.get("budget_max") is None:
        return fields

    if explicit_budget_in_dialogue(dialogue_text):
        return fields

    from app.graph.templates.collect_guidance import next_guidance_step

    if next_guidance_step(fields) == "done":
        return fields

    updated = dict(fields)
    for key in ("budget_min", "budget_max", "budget_tier"):
        updated.pop(key, None)
    return updated


def _last_user_utterance(dialogue_text: str) -> str:
    user_text = _user_dialogue_text(dialogue_text)
    lines = [line.strip() for line in user_text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def sanitize_destination(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
    pending_clarification: dict[str, Any] | None = None,
    guidance_step: str | None = None,
) -> dict[str, Any]:
    """移除与用户原话不一致、且未经确认的目的地（防 LLM / 模糊误绑）。

    仅在「destination」引导步执行；用户回答出发城市/日期等时不应误删已确认目的地。
    """
    dest = fields.get("destination")
    if not dest:
        return fields

    if guidance_step and guidance_step != "destination":
        return fields

    # 用户刚确认过的澄清候选
    if pending_clarification and pending_clarification.get("slot") == "destination":
        return fields

    last_user = _last_user_utterance(dialogue_text)
    if not last_user:
        return fields

    from app.graph.semantic.destination_resolver import resolve_destination_input

    if last_user == dest or dest in last_user:
        resolution = resolve_destination_input(last_user)
        if resolution.action == "accept":
            return fields
        updated = dict(fields)
        updated.pop("destination", None)
        return updated

    resolution = resolve_destination_input(last_user)
    if resolution.action == "accept" and resolution.city == dest:
        return fields

    # 用户说的是 A，state 里是 B（如 西藏 → 西安）
    if resolution.city and resolution.city != dest:
        updated = dict(fields)
        updated.pop("destination", None)
        return updated

    if resolution.action in ("clarify", "none") and str(dest) not in last_user:
        user_text = _user_dialogue_text(dialogue_text)
        if str(dest) not in user_text:
            updated = dict(fields)
            updated.pop("destination", None)
            return updated

    return fields
