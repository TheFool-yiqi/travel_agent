"""和风天气 HTTP 实现（MCP provider 与 adapter 共用，避免重复）。"""

from __future__ import annotations

import httpx
from loguru import logger

from app.mcp.http_client import provider_sync_client
from app.settings import settings


def fetch_weather_markdown(destination: str) -> str:
    """
    查询目的地天气（实时 + 3 日预报），返回 Markdown 文本。

    需配置 QWEATHER_API_KEY 与 QWEATHER_API_HOST。
    """
    if not settings.qweather_api_key or not settings.qweather_base_url:
        logger.warning("和风天气未配置，返回占位信息")
        return (
            f"## {destination} 天气\n\n"
            "（未配置 QWEATHER_API_KEY / QWEATHER_API_HOST，请在 .env 中填写）"
        )

    headers = {"X-QW-Api-Key": settings.qweather_api_key}
    base = settings.qweather_base_url.rstrip("/")
    timeout = httpx.Timeout(15.0)

    try:
        with provider_sync_client(timeout=timeout) as client:
            geo_resp = client.get(
                f"{base}/geo/v2/city/lookup",
                params={"location": destination, "lang": settings.qweather_lang},
                headers=headers,
            )
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            locations = geo_data.get("location") or []
            if not locations:
                return f"## {destination} 天气\n\n未找到该城市的气象站点。"

            location_id = locations[0]["id"]
            city_name = locations[0].get("name", destination)

            now_resp = client.get(
                f"{base}/v7/weather/now",
                params={
                    "location": location_id,
                    "lang": settings.qweather_lang,
                    "unit": settings.qweather_unit,
                },
                headers=headers,
            )
            now_resp.raise_for_status()
            now = now_resp.json().get("now") or {}

            forecast_resp = client.get(
                f"{base}/v7/weather/3d",
                params={
                    "location": location_id,
                    "lang": settings.qweather_lang,
                    "unit": settings.qweather_unit,
                },
                headers=headers,
            )
            forecast_resp.raise_for_status()
            daily = forecast_resp.json().get("daily") or []

    except httpx.HTTPError as exc:
        logger.error("和风天气请求失败: {}", exc)
        return f"## {destination} 天气\n\n天气服务暂时不可用，请稍后重试。"

    lines = [f"## {city_name} 天气信息", ""]
    if now:
        lines.append(
            f"**当前**：{now.get('text', '—')}，"
            f"{now.get('temp', '—')}°C，"
            f"体感 {now.get('feelsLike', '—')}°C，"
            f"湿度 {now.get('humidity', '—')}%"
        )
        lines.append("")

    for day in daily[:3]:
        lines.append(
            f"- **{day.get('fxDate', '—')}**："
            f"{day.get('textDay', '—')} / {day.get('textNight', '—')}，"
            f"{day.get('tempMin', '—')}–{day.get('tempMax', '—')}°C"
        )

    return "\n".join(lines)
