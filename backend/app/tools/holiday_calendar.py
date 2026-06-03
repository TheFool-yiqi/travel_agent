"""2026 年中国法定节假日（统一查表，防 LLM 编造节日日期）"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class HolidayEntry:
    """单个法定节日的 canonical 名称、别名与 2026 假期区间。"""

    key: str
    label: str
    start: str
    end: str
    aliases: tuple[str, ...]


# 2026 年国务院安排（出发日默认取假期首日）
CANONICAL_HOLIDAYS_2026: tuple[HolidayEntry, ...] = (
    HolidayEntry("new_year", "元旦", "2026-01-01", "2026-01-01", ("元旦", "新年")),
    HolidayEntry(
        "spring_festival",
        "春节",
        "2026-02-17",
        "2026-02-23",
        ("春节", "过年", "大年", "除夕"),
    ),
    HolidayEntry(
        "qingming",
        "清明节",
        "2026-04-04",
        "2026-04-06",
        ("清明节", "清明", "清明假期"),
    ),
    HolidayEntry(
        "labor_day",
        "劳动节",
        "2026-05-01",
        "2026-05-05",
        ("劳动节", "五一", "五一小长假", "五一假期", "五一劳动节"),
    ),
    HolidayEntry(
        "dragon_boat",
        "端午节",
        "2026-06-19",
        "2026-06-21",
        ("端午节", "端午", "端午假期", "端午小长假"),
    ),
    HolidayEntry(
        "mid_autumn",
        "中秋节",
        "2026-09-25",
        "2026-09-27",
        ("中秋节", "中秋", "中秋假期"),
    ),
    HolidayEntry(
        "national_day",
        "国庆节",
        "2026-10-01",
        "2026-10-07",
        ("国庆节", "国庆", "十一", "十一假期", "黄金周", "国庆黄金周"),
    ),
)

# 兼容旧引用
HOLIDAY_START_DATES_2026: dict[str, str] = {
    alias: entry.start
    for entry in CANONICAL_HOLIDAYS_2026
    for alias in (entry.label, *entry.aliases)
}

HOLIDAY_RANGES_2026: dict[str, tuple[str, str]] = {
    alias: (entry.start, entry.end)
    for entry in CANONICAL_HOLIDAYS_2026
    for alias in (entry.label, *entry.aliases)
}


def _match_entries_in_text(text: str) -> list[HolidayEntry]:
    if not text:
        return []
    matched: list[HolidayEntry] = []
    for entry in CANONICAL_HOLIDAYS_2026:
        terms = sorted((entry.label, *entry.aliases), key=len, reverse=True)
        if any(term in text for term in terms):
            matched.append(entry)
    return matched


def detect_holiday_departure_date(text: str) -> str | None:
    """从文本识别节日，返回 2026 年假期首日（多节日时取在文本中最先出现的）。"""
    if not text:
        return None
    best: tuple[int, HolidayEntry] | None = None
    for entry in CANONICAL_HOLIDAYS_2026:
        terms = sorted((entry.label, *entry.aliases), key=len, reverse=True)
        for term in terms:
            index = text.find(term)
            if index >= 0 and (best is None or index < best[0]):
                best = (index, entry)
                break
    return best[1].start if best else None


def detect_holiday_label(text: str) -> str | None:
    """返回识别到的节日中文名（如 劳动节）。"""
    if not text:
        return None
    best: tuple[int, HolidayEntry] | None = None
    for entry in CANONICAL_HOLIDAYS_2026:
        terms = sorted((entry.label, *entry.aliases), key=len, reverse=True)
        for term in terms:
            index = text.find(term)
            if index >= 0 and (best is None or index < best[0]):
                best = (index, entry)
                break
    return best[1].label if best else None


def format_holiday_date_range(entry: HolidayEntry) -> str:
    """口语化日期区间，如「端午节（6月19-21日）」。"""
    start = date.fromisoformat(entry.start)
    end = date.fromisoformat(entry.end)
    if start == end:
        return f"{entry.label}（{start.month}月{start.day}日）"
    if start.month == end.month:
        return f"{entry.label}（{start.month}月{start.day}-{end.day}日）"
    return f"{entry.label}（{start.month}月{start.day}日-{end.month}月{end.day}日）"


def nearest_upcoming_holidays(
    anchor: date | None = None,
    *,
    count: int = 2,
    include_ongoing: bool = True,
) -> list[HolidayEntry]:
    """返回距 anchor 最近（未结束）的法定节假日，按开始日升序。"""
    from app.tools.datetime_tools import today_beijing

    anchor = anchor or today_beijing()
    candidates: list[tuple[date, HolidayEntry]] = []
    for entry in CANONICAL_HOLIDAYS_2026:
        start = date.fromisoformat(entry.start)
        end = date.fromisoformat(entry.end)
        if include_ongoing and start <= anchor <= end:
            candidates.append((start, entry))
        elif start >= anchor:
            candidates.append((start, entry))
    candidates.sort(key=lambda item: item[0])
    return [entry for _, entry in candidates[:count]]


def nearest_holiday_examples_text(
    anchor: date | None = None,
    *,
    count: int = 2,
) -> str:
    """供问候/追问使用的最近节日举例。"""
    holidays = nearest_upcoming_holidays(anchor, count=count)
    if not holidays:
        return ""
    return "、".join(format_holiday_date_range(entry) for entry in holidays)


def holiday_reference_lines() -> list[str]:
    lines: list[str] = []
    for entry in CANONICAL_HOLIDAYS_2026:
        if entry.start == entry.end:
            lines.append(f"- {entry.label}：{entry.start}")
        else:
            lines.append(
                f"- {entry.label}：{entry.start} 至 {entry.end}（出发日可取 {entry.start}）",
            )
    return lines


def holiday_reference_text() -> str:
    return "2026年法定节假日参考：\n" + "\n".join(holiday_reference_lines())


def format_holiday_departure_hint(text: str) -> str | None:
    """用于回复模板：劳动节（2026-05-01）。"""
    label = detect_holiday_label(text)
    start = detect_holiday_departure_date(text)
    if label and start:
        return f"{label}（{start}）"
    return None


def apply_holiday_date_to_fields(fields: dict, dialogue_text: str) -> dict:
    """对话提到节日时，强制写入查表出发日期（覆盖 LLM 幻觉日期）。"""
    expected = detect_holiday_departure_date(dialogue_text)
    if not expected:
        return fields
    updated = dict(fields)
    updated["departure_date"] = expected
    return updated


def validate_holiday_date_mismatch(dialogue_text: str, departure_date: str | None) -> str | None:
    """若对话提到节日但 departure_date 与查表不一致，返回错误说明。"""
    if not departure_date or not dialogue_text:
        return None
    label = detect_holiday_label(dialogue_text)
    expected = detect_holiday_departure_date(dialogue_text)
    if label and expected and departure_date != expected:
        return f"出发日期 {departure_date} 与对话中的{label}不符（{label} 2026 年出发日应为 {expected}）"
    return None


_WHOLE_HOLIDAY_DURATION = re.compile(
    r"整个(?:小)?(?:长)?假(?:期)?"
    r"|(?:小)?(?:长)?假(?:期)?(?:全|都)(?:部)?(?:玩|去|过)?"
    r"|假期(?:全|都)(?:部)?玩"
    r"|放几天玩几天"
    r"|假(?:期)?玩(?:满|完)"
    r"|(?:把)?(?:这个)?(?:小)?(?:长)?假(?:期)?(?:都|全)(?:部)?(?:玩|去|过)?"
)


def is_whole_holiday_duration_phrase(text: str) -> bool:
    """口语「整个假期 / 小长假玩满」等是否表示按法定假期长度出行。"""
    if not text:
        return False
    return bool(_WHOLE_HOLIDAY_DURATION.search(text))


def holiday_entry_for_date(departure_date: str) -> HolidayEntry | None:
    """返回 departure_date 落在其区间内的法定节日。"""
    if not departure_date:
        return None
    try:
        anchor = date.fromisoformat(departure_date)
    except ValueError:
        return None
    for entry in CANONICAL_HOLIDAYS_2026:
        start = date.fromisoformat(entry.start)
        end = date.fromisoformat(entry.end)
        if start <= anchor <= end:
            return entry
    return None


def holiday_entry_for_label(label: str) -> HolidayEntry | None:
    if not label:
        return None
    for entry in CANONICAL_HOLIDAYS_2026:
        if entry.label == label:
            return entry
    return None


def holiday_span_days(entry: HolidayEntry) -> int:
    """法定假期天数（含首尾）。"""
    start = date.fromisoformat(entry.start)
    end = date.fromisoformat(entry.end)
    return (end - start).days + 1


def holiday_span_days_for_date(departure_date: str) -> int | None:
    entry = holiday_entry_for_date(departure_date)
    return holiday_span_days(entry) if entry else None


def extract_whole_holiday_travel_days(
    text: str,
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> int | None:
    """从「整个假期」类口语 + 已知出发日/节日上下文推断出行天数。"""
    if not is_whole_holiday_duration_phrase(text):
        return None

    departure_date = fields.get("departure_date")
    if departure_date:
        span = holiday_span_days_for_date(str(departure_date))
        if span:
            return span

    label = detect_holiday_label(text) or detect_holiday_label(dialogue_text)
    entry = holiday_entry_for_label(label) if label else None
    if entry:
        return holiday_span_days(entry)
    return None


def suggest_holiday_travel_days(
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> tuple[int, str] | None:
    """根据出发日或对话中的节日，给出建议天数与节日名。"""
    departure_date = fields.get("departure_date")
    if departure_date:
        entry = holiday_entry_for_date(str(departure_date))
        if entry:
            return holiday_span_days(entry), entry.label

    label = detect_holiday_label(dialogue_text)
    entry = holiday_entry_for_label(label) if label else None
    if entry:
        return holiday_span_days(entry), entry.label
    return None
