"""Weather tool runtime adapter."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from app.runtime.tools.allowlist import assert_allowlisted
from app.runtime.tools.schemas import ToolWarning, WeatherContext
from app.tools.weather import fetch_weather_info

_RISK_KEYWORDS = ("雨", "雪", "风", "高温", "低温", "雾", "霾", "警告", "警戒", "雷")
WEATHER_TOOL_NAME = "weather.get_forecast"


class WeatherToolAdapter:
    """Trim existing weather markdown into planner-safe WeatherContext."""

    def __init__(
        self,
        *,
        fetch_forecast: Callable[[str], str] | None = None,
    ) -> None:
        self._fetch_forecast = fetch_forecast or fetch_weather_info

    def fetch_forecast(
        self,
        destination: str,
        *,
        date_range: str | None = None,
    ) -> tuple[WeatherContext, list[ToolWarning]]:
        assert_allowlisted(WEATHER_TOOL_NAME)
        destination = destination.strip()
        if not destination:
            return (
                WeatherContext(
                    status="unavailable",
                    destination=None,
                    date_range=date_range,
                ),
                [
                    ToolWarning(
                        code="weather_skipped",
                        message="缺少目的地，跳过天气查询",
                    ),
                ],
            )

        try:
            raw = self._fetch_forecast(destination).strip()
        except Exception as exc:
            return (
                WeatherContext(
                    status="unavailable",
                    destination=destination,
                    date_range=date_range,
                ),
                [
                    ToolWarning(
                        code="weather_unavailable",
                        message=f"天气查询失败: {exc}",
                    ),
                ],
            )

        if not raw:
            return (
                WeatherContext(
                    status="unavailable",
                    destination=destination,
                    date_range=date_range,
                ),
                [
                    ToolWarning(
                        code="weather_unavailable",
                        message="天气查询返回空结果",
                    ),
                ],
            )

        summary, risks = _parse_weather_markdown(raw)
        return (
            WeatherContext(
                status="available",
                destination=destination,
                date_range=date_range,
                summary=summary,
                risks=risks,
                source="qweather",
                fetched_at=datetime.now(UTC).isoformat(),
            ),
            [],
        )


def _parse_weather_markdown(raw: str) -> tuple[str, list[str]]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        return "", []

    summary_lines = lines[:3]
    summary = " ".join(summary_lines)
    if len(summary) > 500:
        summary = summary[:497] + "..."

    risks: list[str] = []
    for line in lines:
        if any(keyword in line for keyword in _RISK_KEYWORDS):
            risks.append(line)
    return summary, list(dict.fromkeys(risks))
