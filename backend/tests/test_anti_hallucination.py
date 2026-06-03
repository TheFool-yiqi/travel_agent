"""Anti-hallucination validator tests."""

from datetime import date, timedelta

from app.graph.validators.requirements import validate_requirements
from app.tools.datetime_tools import parse_relative_date, relative_date_reference_text


def test_parse_relative_date_tomorrow() -> None:
    anchor = date(2026, 6, 1)
    assert parse_relative_date("明天出发", anchor=anchor) == "2026-06-02"


def test_parse_relative_date_next_weekday() -> None:
    anchor = date(2026, 6, 1)  # Monday
    assert parse_relative_date("下周五", anchor=anchor) == "2026-06-12"


def test_relative_date_reference_text() -> None:
    text = relative_date_reference_text(date(2026, 6, 1))
    assert "2026-06-01" in text
    assert "2026-06-02" in text


def test_validate_requirements_holiday_mismatch() -> None:
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-06",
        "travel_days": 3,
        "budget_min": 1000,
        "budget_max": 3000,
    }
    errors = validate_requirements(fields, dialogue_text="用户: 端午节")
    assert any("2026-06-19" in e for e in errors)


def test_validate_requirements_labor_day_mismatch() -> None:
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-05-06",
        "travel_days": 3,
        "budget_min": 1000,
        "budget_max": 3000,
    }
    errors = validate_requirements(fields, dialogue_text="用户: 五一")
    assert any("2026-05-01" in e for e in errors)


def test_validate_requirements_budget_range() -> None:
    fields = {
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "budget_min": 5000,
        "budget_max": 2000,
    }
    errors = validate_requirements(fields)
    assert any("预算下限" in e for e in errors)
