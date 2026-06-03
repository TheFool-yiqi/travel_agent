"""本地日期工具测试。"""

from __future__ import annotations

from app.tools.datetime_tools import (
    date_context_for_prompt,
    get_current_date,
    parse_relative_date,
    today_beijing_iso,
)


def test_get_current_date_includes_holiday_and_relative() -> None:
    value = get_current_date.invoke({})
    assert today_beijing_iso() in value or "今天" in value
    assert "端午节" in value
    assert "2026-06-19" in value


def test_date_context_for_prompt() -> None:
    text = date_context_for_prompt()
    assert "相对日期参考" in text
    assert "法定节假日" in text


def test_parse_relative_date_today_keyword() -> None:
    anchor = __import__("datetime").date(2026, 6, 1)
    assert parse_relative_date("今天走", anchor=anchor) == "2026-06-01"
