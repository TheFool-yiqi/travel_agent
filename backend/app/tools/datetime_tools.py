"""日期/时间工具（本地，不走 MCP）。"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

DEFAULT_TZ = ZoneInfo("Asia/Shanghai")

_WEEKDAY_MAP = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}


def today_beijing() -> date:
    return datetime.now(DEFAULT_TZ).date()


def today_beijing_iso() -> str:
    """今天日期 YYYY-MM-DD（北京时间）。"""
    return today_beijing().isoformat()


def parse_relative_date(text: str, anchor: date | None = None) -> str | None:
    """解析相对日期口语（今天/明天/后天/下周X），返回 YYYY-MM-DD。"""
    if not text:
        return None
    anchor = anchor or today_beijing()
    stripped = text.strip()

    simple_offsets = {
        "今天": 0,
        "今日": 0,
        "明天": 1,
        "明日": 1,
        "后天": 2,
        "大后天": 3,
    }
    for word, offset in simple_offsets.items():
        if word in stripped:
            return (anchor + timedelta(days=offset)).isoformat()

    if "这周末" in stripped or "本周末" in stripped:
        days_until_sat = (5 - anchor.weekday()) % 7
        if anchor.weekday() == 6:
            days_until_sat = 0
        return (anchor + timedelta(days=days_until_sat)).isoformat()

    if "下周末" in stripped:
        days_until_sat = (5 - anchor.weekday()) % 7
        if anchor.weekday() == 6:
            days_until_sat = 7
        else:
            days_until_sat += 7
        return (anchor + timedelta(days=days_until_sat)).isoformat()

    match = re.search(r"下(?:周|礼拜)([一二三四五六日天])", stripped)
    if match:
        target_weekday = _WEEKDAY_MAP[match.group(1)]
        days_ahead = (7 - anchor.weekday()) + target_weekday
        if days_ahead <= 0:
            days_ahead += 7
        return (anchor + timedelta(days=days_ahead)).isoformat()

    match = re.search(r"(?:周|礼拜)([一二三四五六日天])", stripped)
    if match and "下" not in stripped[: match.start() + 1]:
        target_weekday = _WEEKDAY_MAP[match.group(1)]
        days_ahead = (target_weekday - anchor.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (anchor + timedelta(days=days_ahead)).isoformat()

    iso_match = re.search(r"(20\d{2})-(\d{2})-(\d{2})", stripped)
    if iso_match:
        try:
            return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))).isoformat()
        except ValueError:
            return None

    cn_match = re.search(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日", stripped)
    if cn_match:
        month, day = int(cn_match.group(1)), int(cn_match.group(2))
        year = anchor.year
        try:
            candidate = date(year, month, day)
            if candidate < anchor:
                candidate = date(year + 1, month, day)
            return candidate.isoformat()
        except ValueError:
            return None

    return None


def relative_date_reference_text(anchor: date | None = None) -> str:
    """供 prompt / 工具注入的相对日期锚点。"""
    anchor = anchor or today_beijing()
    offsets = [
        ("今天", 0),
        ("明天", 1),
        ("后天", 2),
        ("大后天", 3),
    ]
    lines = [f"- {label}：{(anchor + timedelta(days=offset)).isoformat()}" for label, offset in offsets]
    return "相对日期参考（北京时间）：\n" + "\n".join(lines)


def date_context_for_prompt() -> str:
    from app.tools.holiday_calendar import holiday_reference_text

    return f"{relative_date_reference_text()}\n\n{holiday_reference_text()}"


@tool("get-current-date")
def get_current_date() -> str:
    """
    返回今天日期（YYYY-MM-DD，北京时间）。

    用户说「今天/明天/后天/下周」时，协调器或 Subagent 应先调用此工具再查票/路线。
    """
    return date_context_for_prompt()
