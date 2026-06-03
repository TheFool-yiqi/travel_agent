"""需求收集回复校验与清洗（防止 LLM 对话乱码/逻辑矛盾）"""

from __future__ import annotations

import re
from datetime import date, timedelta

from app.tools.datetime_tools import today_beijing

_ANNUAL_LEAVE = re.compile(r"年假")
_SHORT_TRIP_ABSURD_NIGHTS = re.compile(r"短途\s*(\d{2,})\s*晚")
_LONG_NIGHTS = re.compile(r"(\d{2,})\s*晚")
_DAYS_NIGHTS_PAIR = re.compile(r"(\d+)\s*天\s*(\d+)\s*晚")
_ANNUAL_LEAVE_CLAUSE = re.compile(
    r"[，,]?\s*(?:还是)?想休个?年假(?:来个)?[^。！？?]*",
    re.IGNORECASE,
)
_MARKDOWN_BOLD_PAIR = re.compile(r"\*\*([^*]+)\*\*")


def strip_markdown_bold_artifacts(text: str) -> str:
    """去掉未闭合或多余的 Markdown 加粗符，避免界面出现突兀的 **。"""
    cleaned = _MARKDOWN_BOLD_PAIR.sub(r"\1", text)
    return cleaned.replace("**", "")


def _fix_garbled_budget_ranges(text: str) -> str:
    """修正 LLM 乱写的预算区间（如 2000-30）。"""

    def _replace(match: re.Match[str]) -> str:
        low, high = int(match.group(1)), int(match.group(2))
        if high < 100 and low >= 500:
            return f"{low}-{low + 2000}"
        if high < low:
            return f"{low}-{low + 2000}"
        return match.group(0)

    return re.sub(r"(\d{3,5})\s*[-–—]\s*(\d+)", _replace, text)


def _reply_mentions_upcoming_holiday(reply: str, anchor: date | None = None) -> bool:
    from app.tools.holiday_calendar import nearest_upcoming_holidays

    anchor = anchor or today_beijing()
    for entry in nearest_upcoming_holidays(anchor, count=2):
        terms = (entry.label, *entry.aliases)
        if any(term in reply for term in terms):
            return True
    return False


def should_mention_annual_leave(dialogue_text: str, anchor: date | None = None) -> bool:
    """仅当用户提到或临近春节规划窗口时才适合提年假。"""
    anchor = anchor or today_beijing()
    if "年假" in dialogue_text or "带薪假" in dialogue_text or "调休" in dialogue_text:
        return True
    # 12 月–2 月常见春节/寒假规划，可顺带提及长假
    return anchor.month in (12, 1, 2)


def sanitize_collect_reply(reply: str, *, dialogue_text: str = "") -> str:
    """修正常见乱码与不合逻辑表述。"""
    text = reply.strip()
    if not text:
        return text

    text = strip_markdown_bold_artifacts(text)
    text = _fix_garbled_budget_ranges(text)
    text = _SHORT_TRIP_ABSURD_NIGHTS.sub("短途2-3天（1-2晚）", text)

    def _fix_long_nights(match: re.Match[str]) -> str:
        nights = int(match.group(1))
        if nights > 10:
            return "2-3天（1-2晚）"
        return match.group(0)

    text = _LONG_NIGHTS.sub(_fix_long_nights, text)

    for day_match, night_match in _DAYS_NIGHTS_PAIR.findall(text):
        days, nights = int(day_match), int(night_match)
        if nights >= days + 2 or (days <= 4 and nights >= 7):
            text = _DAYS_NIGHTS_PAIR.sub("2-3天（1-2晚）", text, count=1)
            break

    if not should_mention_annual_leave(dialogue_text):
        text = _ANNUAL_LEAVE_CLAUSE.sub("", text)
        text = text.replace("年假", "小长假")

    text = re.sub(r"玩几天呢(?=[^\s，。！？?])", "玩几天呢？", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_collect_reply(
    reply: str,
    *,
    dialogue_text: str = "",
    missing_departure_date: bool = False,
) -> list[str]:
    """返回可读问题；非空表示应改用模板回复。"""
    errors: list[str] = []
    if not reply.strip():
        errors.append("回复为空")
        return errors

    if "**" in reply:
        errors.append("含未渲染的 Markdown 加粗符")

    if missing_departure_date and not _reply_mentions_upcoming_holiday(reply):
        errors.append("询问出发时间时未举例最近节假日")

    if _SHORT_TRIP_ABSURD_NIGHTS.search(reply):
        errors.append("短途出行天数/晚数矛盾")

    for day_str, night_str in _DAYS_NIGHTS_PAIR.findall(reply):
        days, nights = int(day_str), int(night_str)
        if nights > days + 1 or (days <= 5 and nights >= 10):
            errors.append("天数与晚数不匹配")
            break

    if _ANNUAL_LEAVE.search(reply) and not should_mention_annual_leave(dialogue_text):
        errors.append("非春节规划窗口不宜主动提年假")

    if re.search(r"短途\s*\d{2,}", reply):
        errors.append("短途天数异常")

    if _has_garbled_budget_range(reply):
        errors.append("预算金额区间异常")

    return errors


def _has_garbled_budget_range(text: str) -> bool:
    for low_str, high_str in re.findall(r"(\d{3,5})\s*[-–—]\s*(\d+)", text):
        low, high = int(low_str), int(high_str)
        if high < 100 and low >= 500:
            return True
        if low > 0 and high < low:
            return True
    return False
