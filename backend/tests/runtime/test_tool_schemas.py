"""ToolContext schema contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.runtime.tools.schemas import ToolContext, ToolWarning, WeatherContext


def _weather_context_dict() -> dict:
    return {
        "status": "available",
        "destination": "成都",
        "date_range": "2026-07-01 ~ 2026-07-03",
        "summary": "未来三天以多云为主，偶有阵雨。",
        "risks": ["7月2日可能有阵雨，户外行程需备雨具"],
        "source": "qweather",
        "fetched_at": "2026-06-09T12:00:00+00:00",
    }


def test_weather_context_round_trip() -> None:
    weather = WeatherContext.from_runtime_dict(_weather_context_dict())
    restored = WeatherContext.from_runtime_dict(weather.to_runtime_dict())

    assert restored == weather
    assert restored.status == "available"
    assert restored.destination == "成都"


def test_weather_context_rejects_invalid_status() -> None:
    payload = _weather_context_dict()
    payload["status"] = "degraded"

    with pytest.raises(ValidationError):
        WeatherContext.from_runtime_dict(payload)


def test_tool_warning_round_trip() -> None:
    warning = ToolWarning(code="weather_unavailable", message="缺少目的地，跳过天气查询")
    restored = ToolWarning.from_runtime_dict(warning.to_runtime_dict())

    assert restored == warning


def test_tool_context_round_trip_with_weather_and_warnings() -> None:
    context = ToolContext(
        weather=WeatherContext.from_runtime_dict(_weather_context_dict()),
        tool_warnings=[
            ToolWarning(code="weather_skipped", message="测试警告"),
        ],
    )
    restored = ToolContext.from_runtime_dict(context.to_runtime_dict())

    assert restored.weather is not None
    assert restored.weather.summary.startswith("未来三天")
    assert restored.tool_warnings[0].code == "weather_skipped"


def test_tool_context_unavailable_weather_without_summary() -> None:
    context = ToolContext(
        weather=WeatherContext(
            status="unavailable",
            destination="成都",
            summary="",
            risks=[],
        ),
    )
    restored = ToolContext.from_runtime_dict(context.to_runtime_dict())

    assert restored.weather is not None
    assert restored.weather.status == "unavailable"
    assert restored.weather.summary == ""
