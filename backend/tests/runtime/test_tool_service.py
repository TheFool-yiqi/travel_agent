"""ToolService and weather adapter tests."""

from __future__ import annotations

import pytest

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.tools.allowlist import assert_allowlisted, is_allowlisted, is_runtime_invocable
from app.runtime.tools.service import ToolService
from app.runtime.tools.weather_adapter import WeatherToolAdapter


def test_allowlist_includes_weather_and_helper_names() -> None:
    assert is_allowlisted("weather.get_forecast")
    assert is_allowlisted("date.resolve_relative_date")
    assert is_runtime_invocable("weather.get_forecast")
    assert not is_runtime_invocable("date.resolve_relative_date")


def test_assert_allowlisted_rejects_unknown_tool() -> None:
    with pytest.raises(ValueError, match="not allowlisted"):
        assert_allowlisted("search.web")


def test_weather_adapter_trims_markdown_into_summary_and_risks() -> None:
    raw = "\n".join(
        [
            "成都 实时天气",
            "今天多云 26°C",
            "明天有阵雨，出行请备雨具",
            "后天晴 28°C",
        ],
    )
    adapter = WeatherToolAdapter(fetch_forecast=lambda _city: raw)

    weather, warnings = adapter.fetch_forecast("成都", date_range="2026-07-01 ~ 3天")

    assert weather.status == "available"
    assert "成都" in weather.summary
    assert any("阵雨" in risk for risk in weather.risks)
    assert warnings == []
    assert weather.fetched_at


def test_weather_adapter_returns_unavailable_on_fetch_error() -> None:
    def _raise(_city: str) -> str:
        raise RuntimeError("network down")

    adapter = WeatherToolAdapter(fetch_forecast=_raise)

    weather, warnings = adapter.fetch_forecast("成都")

    assert weather.status == "unavailable"
    assert warnings[0].code == "weather_unavailable"


def test_weather_adapter_skips_empty_destination() -> None:
    adapter = WeatherToolAdapter(fetch_forecast=lambda _city: "unused")

    weather, warnings = adapter.fetch_forecast("  ")

    assert weather.status == "unavailable"
    assert warnings[0].code == "weather_skipped"


def _planning_need_dict() -> dict:
    return PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
            PlanningFact(
                field="departure_date",
                value="2026-07-01",
                fact_type="confirmed",
                source="user",
            ),
            PlanningFact(
                field="travel_days",
                value=3,
                fact_type="confirmed",
                source="user",
            ),
        ],
    ).to_runtime_dict()


def test_tool_service_enrich_writes_available_weather() -> None:
    service = ToolService(
        weather_adapter=WeatherToolAdapter(
            fetch_forecast=lambda _city: "成都 多云\n明天有阵雨",
        ),
    )

    tool_context = service.enrich(
        _planning_need_dict(),
        BaseContext(
            planning_need_summary={
                "destination": "成都",
                "departure_date": "2026-07-01",
                "travel_days": 3,
            },
        ).to_runtime_dict(),
    )

    assert tool_context.weather is not None
    assert tool_context.weather.status == "available"
    assert tool_context.weather.date_range == "2026-07-01 ~ 3天"
    assert tool_context.weather.summary


def test_tool_service_enrich_continues_when_weather_unavailable() -> None:
    service = ToolService(
        weather_adapter=WeatherToolAdapter(fetch_forecast=lambda _city: ""),
    )

    tool_context = service.enrich(_planning_need_dict(), None)

    assert tool_context.weather is not None
    assert tool_context.weather.status == "unavailable"
    assert tool_context.tool_warnings
