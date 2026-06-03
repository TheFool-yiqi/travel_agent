"""Holiday date resolution tests for all 2026 statutory holidays."""

from datetime import date

import pytest
from langchain_core.messages import HumanMessage

from app.graph.nodes.collect_requirements import (
    _heuristic_extract,
    _heuristic_extract_from_messages,
    _merge_extractions,
)
from app.schemas.travel import RequirementExtraction
from app.tools.holiday_calendar import (
    CANONICAL_HOLIDAYS_2026,
    apply_holiday_date_to_fields,
    detect_holiday_departure_date,
    detect_holiday_label,
    validate_holiday_date_mismatch,
)


@pytest.mark.parametrize(
    ("text", "expected_start", "expected_label"),
    [
        ("元旦出行", "2026-01-01", "元旦"),
        ("过年回家", "2026-02-17", "春节"),
        ("清明节", "2026-04-04", "清明节"),
        ("五一小长假", "2026-05-01", "劳动节"),
        ("端午节", "2026-06-19", "端午节"),
        ("中秋假期", "2026-09-25", "中秋节"),
        ("十一黄金周", "2026-10-01", "国庆节"),
    ],
)
def test_all_holidays_detect_correct_2026_date(
    text: str,
    expected_start: str,
    expected_label: str,
) -> None:
    assert detect_holiday_departure_date(text) == expected_start
    assert detect_holiday_label(text) == expected_label


def test_canonical_holidays_cover_seven_entries() -> None:
    assert len(CANONICAL_HOLIDAYS_2026) == 7


def test_heuristic_extract_from_multi_turn_messages() -> None:
    messages = [
        HumanMessage(content="上海"),
        HumanMessage(content="劳动节"),
    ]
    extracted = _heuristic_extract_from_messages(messages)
    # 单字城市名由 semantic 层 step-aware 绑定，heuristic 仅保留节日/日期
    assert extracted.departure_city is None
    assert extracted.departure_date == "2026-05-01"


def test_merge_extractions_heuristic_overrides_wrong_labor_day() -> None:
    llm = RequirementExtraction(departure_date="2026-05-06", departure_city="上海")
    heuristic = RequirementExtraction(departure_date="2026-05-01")
    merged = _merge_extractions(llm, heuristic)
    assert merged.departure_date == "2026-05-01"


def test_apply_holiday_date_to_fields_overwrites_llm() -> None:
    fields = {"departure_date": "2026-10-08", "departure_city": "北京"}
    updated = apply_holiday_date_to_fields(fields, "用户: 国庆节")
    assert updated["departure_date"] == "2026-10-01"


def test_validate_holiday_mismatch_national_day() -> None:
    err = validate_holiday_date_mismatch("用户: 国庆", "2026-10-08")
    assert err is not None
    assert "2026-10-01" in err
    assert "国庆节" in err


def test_heuristic_extract_travel_days() -> None:
    assert _heuristic_extract("想玩3天").travel_days == 3


def test_nearest_upcoming_holidays_from_june() -> None:
    from app.tools.holiday_calendar import (
        format_holiday_date_range,
        nearest_holiday_examples_text,
        nearest_upcoming_holidays,
    )

    anchor = date(2026, 6, 1)
    holidays = nearest_upcoming_holidays(anchor, count=2)
    assert holidays[0].label == "端午节"
    assert "端午" in nearest_holiday_examples_text(anchor)
    assert "6月" in format_holiday_date_range(holidays[0])


@pytest.mark.parametrize(
    ("departure_date", "expected_days"),
    [
        ("2026-06-19", 3),
        ("2026-06-20", 3),
        ("2026-05-01", 5),
        ("2026-10-01", 7),
        ("2026-06-18", None),
    ],
)
def test_holiday_span_days_for_date(departure_date: str, expected_days: int | None) -> None:
    from app.tools.holiday_calendar import holiday_span_days_for_date

    assert holiday_span_days_for_date(departure_date) == expected_days


def test_extract_whole_holiday_travel_days() -> None:
    from app.tools.holiday_calendar import extract_whole_holiday_travel_days

    fields = {"departure_date": "2026-06-19"}
    assert extract_whole_holiday_travel_days("整个假期", fields) == 3
    assert extract_whole_holiday_travel_days("3天", fields) is None
    assert extract_whole_holiday_travel_days("整个假期", {}, dialogue_text="端午节") == 3


def test_suggest_holiday_travel_days() -> None:
    from app.tools.holiday_calendar import suggest_holiday_travel_days

    assert suggest_holiday_travel_days({"departure_date": "2026-06-19"}) == (3, "端午节")
    assert suggest_holiday_travel_days({}, dialogue_text="用户: 端午节") == (3, "端午节")
